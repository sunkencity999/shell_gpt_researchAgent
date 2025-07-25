"""
Research Data Analysis Function
Safe system integration for data analysis during research tasks.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional

from ...research_automation import create_research_automation, SecurityLevel


class Function(OpenAISchema):
    """
    Analyze data files or directories for research purposes using safe system commands.
    This function can count files, analyze text patterns, check file sizes, and more.
    """

    analysis_type: str = Field(
        ...,
        example="file_count",
        description="Type of analysis: 'file_count', 'text_patterns', 'file_sizes', 'content_summary', 'keyword_search'",
    )
    
    target_path: str = Field(
        default="documents",
        example="documents/research_topic",
        description="Path to analyze (relative to research directory, defaults to 'documents')",
    )
    
    search_term: Optional[str] = Field(
        default=None,
        example="climate change",
        description="Search term for keyword_search analysis type",
    )
    
    file_pattern: Optional[str] = Field(
        default="*",
        example="*.txt",
        description="File pattern to match (e.g., '*.txt', '*.pdf', '*.md')",
    )

    class Config:
        title = "analyze_research_data"

    @classmethod
    def execute(cls, analysis_type: str, target_path: str = "documents", 
                search_term: Optional[str] = None, file_pattern: str = "*") -> str:
        """Execute research data analysis using safe system commands."""
        
        try:
            # Create research automation instance
            automation = create_research_automation()
            
            results = []
            
            if analysis_type == "file_count":
                # Count files in the target directory
                cmd = f"find {target_path} -name '{file_pattern}' -type f | wc -l"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    count = result.output.strip()
                    results.append(f"Found {count} files matching pattern '{file_pattern}' in {target_path}")
                else:
                    results.append(f"Error counting files: {result.error}")
            
            elif analysis_type == "file_sizes":
                # Analyze file sizes
                cmd = f"find {target_path} -name '{file_pattern}' -type f -exec du -h {{}} \\; | sort -hr | head -20"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"Largest files in {target_path}:")
                    results.append(result.output)
                else:
                    results.append(f"Error analyzing file sizes: {result.error}")
            
            elif analysis_type == "text_patterns":
                # Analyze common text patterns
                cmd = f"find {target_path} -name '*.txt' -o -name '*.md' | head -10 | xargs grep -h -o -E '[A-Z][a-z]+( [A-Z][a-z]+)*' | sort | uniq -c | sort -nr | head -20"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"Most common capitalized phrases in {target_path}:")
                    results.append(result.output)
                else:
                    results.append(f"Error analyzing text patterns: {result.error}")
            
            elif analysis_type == "keyword_search":
                if not search_term:
                    return "Error: search_term is required for keyword_search analysis"
                
                # Search for keywords in files
                cmd = f"find {target_path} -name '*.txt' -o -name '*.md' | xargs grep -l -i '{search_term}' | head -20"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    if result.output.strip():
                        results.append(f"Files containing '{search_term}' in {target_path}:")
                        results.append(result.output)
                        
                        # Also count occurrences
                        count_cmd = f"find {target_path} -name '*.txt' -o -name '*.md' | xargs grep -c -i '{search_term}' | grep -v ':0$' | head -10"
                        count_result = automation.execute_safe_command(count_cmd)
                        if count_result.success and count_result.output.strip():
                            results.append(f"\nOccurrence counts:")
                            results.append(count_result.output)
                    else:
                        results.append(f"No files found containing '{search_term}' in {target_path}")
                else:
                    results.append(f"Error searching for keyword: {result.error}")
            
            elif analysis_type == "content_summary":
                # Provide a summary of content types and structure
                cmds = [
                    (f"find {target_path} -type f | wc -l", "Total files"),
                    (f"find {target_path} -type d | wc -l", "Total directories"),
                    (f"find {target_path} -name '*.txt' | wc -l", "Text files"),
                    (f"find {target_path} -name '*.md' | wc -l", "Markdown files"),
                    (f"find {target_path} -name '*.pdf' | wc -l", "PDF files"),
                    (f"du -sh {target_path}", "Total size")
                ]
                
                results.append(f"Content summary for {target_path}:")
                for cmd, description in cmds:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"{description}: {result.output.strip()}")
                    else:
                        results.append(f"{description}: Error - {result.error}")
            
            else:
                return f"Unknown analysis type: {analysis_type}"
            
            # Add session info
            session = automation.get_session_summary()
            results.append(f"\nAnalysis completed. Commands executed: {session['total_commands']}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"Research data analysis failed: {str(e)}"
