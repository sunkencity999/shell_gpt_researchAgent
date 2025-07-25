"""
Research Workflow Automation Function
Orchestrate complex research workflows combining multiple automation tasks.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional, List

from ...research_automation import create_research_automation


class Function(OpenAISchema):
    """
    Execute complex research workflows that combine multiple automation tasks.
    Supports data collection, processing, analysis, and reporting in automated sequences.
    """

    workflow_type: str = Field(
        ...,
        example="data_pipeline",
        description="Workflow type: 'data_pipeline', 'research_report', 'competitive_analysis', 'content_audit', 'system_health'",
    )
    
    target_directory: str = Field(
        default="documents",
        example="documents/research_project",
        description="Target directory for the research workflow",
    )
    
    parameters: Optional[str] = Field(
        default=None,
        example="keyword=climate,format=markdown",
        description="Optional parameters as key=value pairs separated by commas",
    )

    class Config:
        title = "execute_research_workflow"

    @classmethod
    def execute(cls, workflow_type: str, target_directory: str = "documents", 
                parameters: Optional[str] = None) -> str:
        """Execute automated research workflows using safe system commands."""
        
        try:
            automation = create_research_automation(target_directory)
            results = []
            
            # Parse parameters
            params = {}
            if parameters:
                for param in parameters.split(','):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        params[key.strip()] = value.strip()
            
            if workflow_type == "data_pipeline":
                # Automated data processing pipeline
                results.append("🔄 EXECUTING DATA PIPELINE WORKFLOW")
                results.append("=" * 50)
                
                # Step 1: Data Discovery
                results.append("\\n📊 Step 1: Data Discovery")
                discovery_cmd = f"find {target_directory} -type f \\( -name '*.csv' -o -name '*.txt' -o -name '*.json' \\) | head -20"
                discovery_result = automation.execute_safe_command(discovery_cmd)
                if discovery_result.success:
                    data_files = discovery_result.output.strip().split('\\n') if discovery_result.output.strip() else []
                    results.append(f"Found {len(data_files)} data files:")
                    for i, file in enumerate(data_files[:10], 1):
                        results.append(f"  {i}. {file}")
                else:
                    results.append(f"Error in discovery: {discovery_result.error}")
                    data_files = []
                
                # Step 2: Data Validation
                results.append("\\n✅ Step 2: Data Validation")
                for file in data_files[:5]:  # Validate first 5 files
                    validation_cmd = f"file {file}"
                    validation_result = automation.execute_safe_command(validation_cmd)
                    if validation_result.success:
                        results.append(f"  {file}: {validation_result.output.strip()}")
                
                # Step 3: Data Summary
                results.append("\\n📈 Step 3: Data Summary")
                summary_cmd = f"find {target_directory} -name '*.csv' -exec wc -l {{}} \\; | awk '{{total+=$1}} END {{print \"Total CSV lines:\", total}}'"
                summary_result = automation.execute_safe_command(f"bash -c \"{summary_cmd}\"")
                if summary_result.success:
                    results.append(f"  {summary_result.output.strip()}")
            
            elif workflow_type == "research_report":
                # Automated research report generation
                results.append("📄 EXECUTING RESEARCH REPORT WORKFLOW")
                results.append("=" * 50)
                
                # Step 1: Content Inventory
                results.append("\\n📚 Step 1: Content Inventory")
                inventory_cmd = f"find {target_directory} \\( -name '*.md' -o -name '*.txt' \\) -exec wc -w {{}} \\; | awk '{{words+=$1; files++}} END {{print \"Files:\", files, \"| Total words:\", words}}'"
                inventory_result = automation.execute_safe_command(f"bash -c \"{inventory_cmd}\"")
                if inventory_result.success:
                    results.append(f"  {inventory_result.output.strip()}")
                
                # Step 2: Key Terms Extraction
                results.append("\\n🔍 Step 2: Key Terms Analysis")
                keyword = params.get('keyword', 'research')
                terms_cmd = f"find {target_directory} \\( -name '*.md' -o -name '*.txt' \\) -exec grep -ih '{keyword}' {{}} \\; | wc -l"
                terms_result = automation.execute_safe_command(terms_cmd)
                if terms_result.success:
                    results.append(f"  References to '{keyword}': {terms_result.output.strip()}")
                
                # Step 3: Document Structure Analysis
                results.append("\\n🏗️ Step 3: Document Structure")
                structure_cmd = f"find {target_directory} -name '*.md' -exec grep -c '^#' {{}} \\; | awk '{{headers+=$1}} END {{print \"Total headers:\", headers}}'"
                structure_result = automation.execute_safe_command(f"bash -c \"{structure_cmd}\"")
                if structure_result.success:
                    results.append(f"  {structure_result.output.strip()}")
            
            elif workflow_type == "competitive_analysis":
                # Competitive research analysis workflow
                results.append("🏆 EXECUTING COMPETITIVE ANALYSIS WORKFLOW")
                results.append("=" * 50)
                
                # Step 1: Data Collection Status
                results.append("\\n📥 Step 1: Data Collection Status")
                collection_cmd = f"ls -la {target_directory}/ | grep -E '\\.(txt|md|csv|json)$' | wc -l"
                collection_result = automation.execute_safe_command(collection_cmd)
                if collection_result.success:
                    results.append(f"  Research files available: {collection_result.output.strip()}")
                
                # Step 2: Competitor Mention Analysis
                results.append("\\n🔍 Step 2: Competitor Analysis")
                competitors = params.get('competitors', 'competitor').split('|')
                for competitor in competitors:
                    mention_cmd = f"find {target_directory} -type f \\( -name '*.txt' -o -name '*.md' \\) -exec grep -l -i '{competitor}' {{}} \\; | wc -l"
                    mention_result = automation.execute_safe_command(mention_cmd)
                    if mention_result.success:
                        results.append(f"  '{competitor}' mentioned in: {mention_result.output.strip()} files")
                
                # Step 3: Market Intelligence Summary
                results.append("\\n📊 Step 3: Intelligence Summary")
                intel_cmd = f"find {target_directory} -name '*.txt' -o -name '*.md' | xargs wc -w | tail -1 | awk '{{print \"Total intelligence words:\", $1}}'"
                intel_result = automation.execute_safe_command(f"bash -c \"{intel_cmd}\"")
                if intel_result.success:
                    results.append(f"  {intel_result.output.strip()}")
            
            elif workflow_type == "content_audit":
                # Content audit and quality assessment
                results.append("🔍 EXECUTING CONTENT AUDIT WORKFLOW")
                results.append("=" * 50)
                
                # Step 1: Content Inventory
                results.append("\\n📋 Step 1: Content Inventory")
                audit_cmds = [
                    (f"find {target_directory} -name '*.md' | wc -l", "Markdown files"),
                    (f"find {target_directory} -name '*.txt' | wc -l", "Text files"),
                    (f"find {target_directory} -name '*.pdf' | wc -l", "PDF files"),
                    (f"find {target_directory} -type f | xargs ls -la | awk '{{size+=$5}} END {{print \"Total size:\", size/1024/1024, \"MB\"}}'", "Total content size"),
                ]
                
                for cmd, description in audit_cmds:
                    audit_result = automation.execute_safe_command(f"bash -c \"{cmd}\"")
                    if audit_result.success:
                        results.append(f"  {description}: {audit_result.output.strip()}")
                
                # Step 2: Quality Metrics
                results.append("\\n📏 Step 2: Quality Metrics")
                quality_cmds = [
                    (f"find {target_directory} -name '*.md' -exec wc -w {{}} \\; | awk '{{if($1<100) short++; else if($1>1000) long++; else medium++}} END {{print \"Short(<100):\", short, \"Medium:\", medium, \"Long(>1000):\", long}}'", "Document length distribution"),
                    (f"find {target_directory} -name '*.md' -exec grep -c '^#' {{}} \\; | awk '{{if($1==0) no_headers++; else headers++}} END {{print \"With headers:\", headers, \"Without:\", no_headers}}'", "Header usage"),
                ]
                
                for cmd, description in quality_cmds:
                    quality_result = automation.execute_safe_command(f"bash -c \"{cmd}\"")
                    if quality_result.success:
                        results.append(f"  {description}: {quality_result.output.strip()}")
            
            elif workflow_type == "system_health":
                # System health check for research environment
                results.append("🏥 EXECUTING SYSTEM HEALTH WORKFLOW")
                results.append("=" * 50)
                
                # Step 1: Storage Health
                results.append("\\n💾 Step 1: Storage Health")
                storage_cmds = [
                    ("df -h | grep -v tmpfs", "Disk usage"),
                    (f"du -sh {target_directory}", "Research directory size"),
                    (f"find {target_directory} -type f | wc -l", "Total research files"),
                ]
                
                for cmd, description in storage_cmds:
                    storage_result = automation.execute_safe_command(cmd)
                    if storage_result.success:
                        results.append(f"  {description}:")
                        results.append(f"    {storage_result.output.strip()}")
                
                # Step 2: Performance Metrics
                results.append("\\n⚡ Step 2: Performance Metrics")
                perf_cmds = [
                    ("uptime", "System load"),
                    ("free -h", "Memory usage"),
                    ("ps aux --sort=-%cpu | head -5", "Top CPU processes"),
                ]
                
                for cmd, description in perf_cmds:
                    perf_result = automation.execute_safe_command(cmd)
                    if perf_result.success:
                        results.append(f"  {description}:")
                        results.append(f"    {perf_result.output.strip()}")
            
            else:
                return f"Unknown workflow type: {workflow_type}"
            
            # Workflow completion summary
            session = automation.get_session_summary()
            results.append(f"\\n🎉 WORKFLOW COMPLETE")
            results.append("=" * 30)
            results.append(f"Workflow: {workflow_type}")
            results.append(f"Target: {target_directory}")
            results.append(f"Commands executed: {session['total_commands']}")
            results.append(f"Successful: {session['successful_commands']}")
            results.append(f"Session ID: {session['session_id']}")
            
            return "\\n".join(results)
            
        except Exception as e:
            return f"Research workflow failed: {str(e)}"
