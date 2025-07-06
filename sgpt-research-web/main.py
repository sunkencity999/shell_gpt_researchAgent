from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import uuid
import json
import datetime
import asyncio
from urllib.parse import unquote

from sgptAgent.agent import ResearchAgent
from sgptAgent.config import cfg

app = FastAPI()

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="/home/administrator/shell_gpt_researchAgent/sgpt-research-web/static"), name="static")

# Directory for storing research reports and project data
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

# In-memory storage for research tasks and their progress
# In a real-world app, this would be a database (Redis, PostgreSQL, etc.)
research_tasks = {}

@app.on_event("startup")
async def startup_event():
    # Ensure the documents directory exists
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("/home/administrator/shell_gpt_researchAgent/sgpt-research-web/static/index.html")

@app.get("/api/models")
async def get_models():
    # This is a placeholder. In a real app, you'd query Ollama for available models.
    # For now, we'll return a hardcoded list or try to get from OllamaClient if it's easily accessible.
    try:
        from sgptAgent.llm_functions.ollama import OllamaClient
        ollama_client = OllamaClient()
        models = ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        print(f"Error fetching Ollama models: {e}")
        return {"models": [cfg.get("DEFAULT_MODEL")]}

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

        report_path, total_results_found, successful_queries, total_queries = agent.run(
            goal=data.get("query"),
            audience=data.get("audience"),
            tone=data.get("tone"),
            improvement=data.get("improvement"),
            project_name=data.get("project_name"),
            num_results=data.get("num_results"),
            temperature=data.get("temperature"),
            max_tokens=data.get("max_tokens"),
            system_prompt=data.get("system_prompt"),
            ctx_window=data.get("ctx_window"),
            citation_style=data.get("citation_style"),
            filename=data.get("filename"),
            documents_base_dir=str(DOCUMENTS_DIR), # Pass the base documents directory
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

@app.get("/api/reports")
async def get_reports():
    reports = []
    for root, _, files in os.walk(DOCUMENTS_DIR):
        for f in files:
            if f.endswith(('.md', '.txt')):
                full_path = Path(root) / f
                relative_path = full_path.relative_to(DOCUMENTS_DIR)
                reports.append({"name": str(relative_path), "path": str(relative_path)})
    return {"reports": sorted(reports, key=lambda x: x["name"], reverse=True)}


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


@app.get("/api/download/{report_path:path}")
async def download_report(report_path: str):
    decoded_path = unquote(report_path)
    full_path = (DOCUMENTS_DIR / decoded_path).resolve()
    if not full_path.is_file() or not full_path.is_relative_to(DOCUMENTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Report not found or access denied.")
    return FileResponse(full_path, media_type='application/octet-stream', filename=full_path.name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
