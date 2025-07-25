from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import uuid
import json
import datetime
import asyncio
from urllib.parse import unquote

from sgptAgent.agent import ResearchAgent
from sgptAgent.config import cfg
from sgptAgent.research_automation import (
    ResearchAutomation, execute_research_command_with_approval,
    get_safe_research_suggestions
)
from sgptAgent.llm_functions.common.research_data_analysis import Function as DataAnalysisFunction
from sgptAgent.llm_functions.common.research_data_visualization import Function as DataVisualizationFunction
from sgptAgent.llm_functions.common.research_workflow_automation import Function as WorkflowAutomationFunction

app = FastAPI()

# Mount static files (HTML, CSS, JS)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=STATIC_DIR)

# Directory for storing research reports and project data
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

# In-memory storage for research tasks and their progress
# In a real-world app, this would be a database (Redis, PostgreSQL, etc.)
research_tasks = {}

# Automation system storage
automation_tasks = {}
automation_system = None

@app.on_event("startup")
async def startup_event():
    global automation_system
    # Ensure the documents directory exists
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize automation system
    try:
        automation_system = ResearchAutomation(
            research_dir=str(DOCUMENTS_DIR),
            approval_callback=None  # Web interface will handle approval differently
        )
        print("✅ Research automation system initialized for web interface")
    except Exception as e:
        print(f"⚠️ Failed to initialize automation system: {e}")
        automation_system = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    relative_docs_dir = os.path.relpath(DOCUMENTS_DIR, Path(__file__).resolve().parent.parent)
    return templates.TemplateResponse("index.html", {"request": request, "documents_dir": str(relative_docs_dir)})

@app.get("/api/models")
@app.get("/v1/models")
async def get_models():
    """
    Retrieves the list of available models from the Ollama service.
    """
    try:
        from sgptAgent.llm_functions.ollama import OllamaClient
        from sgptAgent.config import cfg
        
        ollama_client = OllamaClient()
        # The list_models() function returns a list of model name strings.
        model_names = await asyncio.to_thread(ollama_client.list_models)
        
        # Ensure default and embedding models are in the list, as a fallback
        default_model = cfg.get("DEFAULT_MODEL")
        embedding_model = cfg.get("EMBEDDING_MODEL")
        
        if default_model not in model_names:
            model_names.append(default_model)
        if embedding_model not in model_names:
            model_names.append(embedding_model)
            
        # Return a unique, sorted list of model names
        return {"models": sorted(list(set(model_names)))}
        
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        # Fallback to default models if Ollama is not reachable
        from sgptAgent.config import cfg
        return {"models": [cfg.get("DEFAULT_MODEL"), cfg.get("EMBEDDING_MODEL")]}

@app.get("/api/projects")
async def get_projects():
    projects = [d.name for d in DOCUMENTS_DIR.iterdir() if d.is_dir()]
    return {"projects": sorted(projects)}

@app.post("/api/research")
async def start_research(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    
    query = data.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Research query is required.")

    task_id = str(uuid.uuid4())
    
    research_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "log": [],
        "result": None,
        "report_path": None,
        "error": None,
        "start_time": datetime.datetime.now().isoformat()
    }

    background_tasks.add_task(run_research_task, task_id, data)
    
    return {"task_id": task_id, "status": "research_started"}

@app.get("/api/research/status/{task_id}")
async def get_research_status(task_id: str):
    task = research_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Research task not found.")
    return task

async def run_research_task(task_id: str, data: dict):
    task = research_tasks[task_id]
    task["status"] = "running"
    
    try:
        agent = ResearchAgent(
            model=data.get("model"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            system_prompt=data.get("system_prompt"),
            ctx_window=data.get("ctx_window")
        )

        def progress_callback(desc, bar, substep=None, percent=None, log=None):
            task["log"].append({"timestamp": datetime.datetime.now().isoformat(), "desc": desc, "bar": bar, "substep": substep, "percent": percent, "log": log})
            if percent is not None:
                task["progress"] = int(percent)
            elif isinstance(bar, str) and bar.endswith('%'):
                try:
                    task["progress"] = int(bar.replace('%', ''))
                except ValueError:
                    pass
            
            # Updates to task dictionary are immediately visible to polling endpoint

        report_path, total_results_found, successful_queries, total_queries = await agent.run(
            goal=data.get("query"),
            audience=data.get("audience"),
            tone=data.get("tone"),
            improvement=data.get("improvement"),
            structured_data_prompt=data.get("structured_data_prompt"),
            project_name=data.get("project_name"),
            num_results=data.get("num_results"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            system_prompt=data.get("system_prompt"),
            ctx_window=data.get("ctx_window"),
            citation_style=data.get("citation_style"),
            filename=data.get("filename"),
            documents_base_dir=str(DOCUMENTS_DIR), # Pass the base documents directory
            local_docs_path=data.get("local_docs_path"),
            domain=data.get("domain"),
            research_depth=data.get("research_depth", "balanced"),
            progress_callback=progress_callback
        )
        
        task["report_path"] = report_path
        task["total_results_found"] = total_results_found
        task["successful_queries"] = successful_queries
        task["total_queries"] = total_queries
        if report_path and os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                task["result"] = f.read()
        else:
            task["result"] = "Research completed, but report file not found."
        
        task["status"] = "completed"
        task["progress"] = 100

    except Exception as e:
        import traceback
        task["status"] = "failed"
        task["error"] = str(e)
        task["log"].append({"timestamp": datetime.datetime.now().isoformat(), "log": f"Error: {str(e)}"})
        task["log"].append({"timestamp": datetime.datetime.now().isoformat(), "log": traceback.format_exc()})

@app.post("/api/research/cancel/{task_id}")
async def cancel_research(task_id: str):
    """Cancel a running research task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    if task["status"] in ["completed", "failed", "cancelled"]:
        return {"message": "Task already finished", "status": task["status"]}
    
    # Mark task as cancelled
    task["status"] = "cancelled"
    task["progress"] = 0
    task["log"].append({
        "timestamp": datetime.datetime.now().isoformat(), 
        "desc": "🛑 Research cancelled",
        "substep": "Research was cancelled by the user.",
        "log": "Research cancelled by user request"
    })
    
    return {"message": "Research cancelled successfully", "status": "cancelled"}

@app.get("/api/reports")
async def get_reports(path: str = '.'):
    # Prevent directory traversal attacks
    safe_base_path = DOCUMENTS_DIR.resolve()
    requested_path = (DOCUMENTS_DIR / path).resolve()
    if not requested_path.is_dir() or safe_base_path not in requested_path.parents and requested_path != safe_base_path:
        raise HTTPException(status_code=400, detail="Invalid path specified.")

    items = []
    for item in sorted(requested_path.iterdir()):
        if item.name.startswith('.'):
            continue # Skip hidden files/folders
        relative_path = item.relative_to(DOCUMENTS_DIR)
        item_type = 'folder' if item.is_dir() else 'file'
        items.append({"name": item.name, "path": str(relative_path), "type": item_type})
    
    return {"reports": items}


@app.get("/api/reports/{report_path:path}", response_class=HTMLResponse)
async def get_report_content(report_path: str):
    # Decode the URL-encoded path
    decoded_path = unquote(report_path)
    # Securely join the path and check it's within the documents dir
    full_path = (DOCUMENTS_DIR / decoded_path).resolve()
    if not full_path.is_file() or not full_path.is_relative_to(DOCUMENTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Report not found or access denied.")

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Basic markdown to HTML conversion for display
    import markdown2
    html_content = markdown2.markdown(content, extras=["fenced-code-blocks", "tables"])

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{decoded_path}</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 20px auto; padding: 0 20px; }}
            pre {{ background-color: #eee; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            code {{ font-family: monospace; }}
            h1, h2, h3, h4, h5, h6 {{ color: #333; }}
            a {{ color: #007bff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <a href="/">Back to Research Agent</a>
        <hr>
        {html_content}
    </body>
    </html>
    """


@app.get("/api/download/{file_path:path}")
async def download_file(file_path: str):
    decoded_path = unquote(file_path)
    full_path = (DOCUMENTS_DIR / decoded_path).resolve()
    if not full_path.is_file() or not full_path.is_relative_to(DOCUMENTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="File not found or access denied.")
    return FileResponse(full_path, media_type='application/octet-stream', filename=full_path.name)


@app.delete("/api/delete/{file_path:path}")
async def delete_file(file_path: str):
    """Delete a file from the documents directory."""
    try:
        decoded_path = unquote(file_path)
        full_path = (DOCUMENTS_DIR / decoded_path).resolve()
        
        # Security check: ensure the file is within the documents directory
        if not full_path.is_relative_to(DOCUMENTS_DIR.resolve()):
            raise HTTPException(status_code=403, detail="Access denied.")
        
        # Check if file exists
        if not full_path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {full_path}")
        
        # Delete the file
        full_path.unlink()
        
        return {"message": f"File '{full_path.name}' deleted successfully."}
        
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied. Cannot delete file.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


# ==================== AUTOMATION API ENDPOINTS ====================

@app.get("/api/automation/suggestions")
async def get_automation_suggestions(research_goal: str = "analyze document content and extract key insights"):
    """Get automation suggestions based on research goal"""
    try:
        if not automation_system:
            raise HTTPException(status_code=503, detail="Automation system not available")
        
        suggestions = get_safe_research_suggestions(research_goal)
        
        # Format suggestions for web interface
        formatted_suggestions = []
        for suggestion in suggestions[:12]:  # Limit to 12 suggestions
            formatted_suggestions.append({
                "command": suggestion.get('command', ''),
                "description": suggestion.get('description', ''),
                "category": suggestion.get('category', 'General')
            })
        
        return {
            "status": "success",
            "research_goal": research_goal,
            "suggestions": formatted_suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@app.post("/api/automation/execute")
async def execute_automation(request: Request, background_tasks: BackgroundTasks):
    """Execute automation command with approval workflow"""
    try:
        if not automation_system:
            raise HTTPException(status_code=503, detail="Automation system not available")
        
        data = await request.json()
        command = data.get('command', '').strip()
        mode = data.get('mode', 'custom')  # custom, data_analysis, visualization, workflow, suggestions
        auto_approve = data.get('auto_approve', False)
        
        if not command and mode == 'custom':
            raise HTTPException(status_code=400, detail="Command is required for custom mode")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        automation_tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "progress": 0,
            "message": "Starting automation...",
            "result": None,
            "error": None,
            "start_time": datetime.datetime.now().isoformat(),
            "command": command,
            "mode": mode
        }
        
        # Run automation in background
        background_tasks.add_task(run_automation_task, task_id, command, mode, auto_approve)
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting automation: {str(e)}")

@app.get("/api/automation/status/{task_id}")
async def get_automation_status(task_id: str):
    """Get automation task status"""
    if task_id not in automation_tasks:
        raise HTTPException(status_code=404, detail="Automation task not found")
    
    return automation_tasks[task_id]

async def run_automation_task(task_id: str, command: str, mode: str, auto_approve: bool):
    """Background task to run automation"""
    try:
        # Update task status
        automation_tasks[task_id]["status"] = "running"
        automation_tasks[task_id]["progress"] = 10
        automation_tasks[task_id]["message"] = "Executing automation command..."
        
        if mode == 'custom' and command:
            # Execute custom command
            result = automation_system.execute_safe_command(
                command, 
                allow_moderate=True, 
                user_approved_advanced=auto_approve,
                auto_approve=False  # Web interface doesn't support interactive approval yet
            )
            
            automation_tasks[task_id]["progress"] = 90
            automation_tasks[task_id]["message"] = "Processing results..."
            
            if result.success:
                automation_tasks[task_id]["result"] = {
                    "output": result.output,
                    "command": result.command,
                    "security_level": result.security_level.value,
                    "timestamp": result.timestamp.isoformat()
                }
            else:
                automation_tasks[task_id]["error"] = result.error
        
        elif mode == 'data_analysis':
            # Run data analysis
            analysis_func = DataAnalysisFunction(
                analysis_type="file_count",
                target_path=str(DOCUMENTS_DIR)
            )
            result = analysis_func.run(automation=automation_system)
            automation_tasks[task_id]["result"] = {
                "output": result,
                "mode": "data_analysis",
                "target": str(DOCUMENTS_DIR)
            }
        
        elif mode == 'visualization':
            # Run data visualization
            viz_func = DataVisualizationFunction(
                visualization_type="data_summary",
                data_path=str(DOCUMENTS_DIR)
            )
            result = viz_func.run(automation=automation_system)
            automation_tasks[task_id]["result"] = {
                "output": result,
                "mode": "visualization",
                "target": str(DOCUMENTS_DIR)
            }
        
        elif mode == 'workflow':
            # Run workflow automation
            workflow_func = WorkflowAutomationFunction(
                workflow_type="system_health",
                target=str(DOCUMENTS_DIR)
            )
            result = workflow_func.run(automation=automation_system)
            automation_tasks[task_id]["result"] = {
                "output": result,
                "mode": "workflow",
                "workflow_type": "system_health"
            }
        
        else:
            automation_tasks[task_id]["error"] = "Invalid automation mode"
        
        # Mark as complete
        automation_tasks[task_id]["status"] = "completed" if not automation_tasks[task_id].get("error") else "failed"
        automation_tasks[task_id]["progress"] = 100
        automation_tasks[task_id]["message"] = "Automation completed" if not automation_tasks[task_id].get("error") else "Automation failed"
        automation_tasks[task_id]["end_time"] = datetime.datetime.now().isoformat()
        
    except Exception as e:
        automation_tasks[task_id]["status"] = "failed"
        automation_tasks[task_id]["error"] = str(e)
        automation_tasks[task_id]["progress"] = 100
        automation_tasks[task_id]["message"] = f"Automation failed: {str(e)}"
        automation_tasks[task_id]["end_time"] = datetime.datetime.now().isoformat()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
