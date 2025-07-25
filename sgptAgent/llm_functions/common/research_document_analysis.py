"""
Research Document Analysis Function
Advanced document processing and content analysis for research tasks.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional, List

from ...research_automation import create_research_automation


class Function(OpenAISchema):
    """
    Perform advanced document analysis including content extraction, 
    statistical analysis, similarity detection, and structured data extraction.
    """

    analysis_mode: str = Field(
        ...,
        example="content_extract",
        description="Analysis mode: 'content_extract', 'word_frequency', 'similarity_check', 'structure_analysis', 'metadata_extract'",
    )
    
    target_files: str = Field(
        default="documents/*.txt",
        example="documents/research/*.md",
        description="File pattern or specific files to analyze",
    )
    
    comparison_target: Optional[str] = Field(
        default=None,
        example="documents/reference.txt",
        description="Optional file for similarity comparison",
    )
    
    output_format: str = Field(
        default="summary",
        example="detailed",
        description="Output format: 'summary', 'detailed', 'csv', 'json'",
    )

    class Config:
        title = "analyze_research_documents"

    @classmethod
    def execute(cls, analysis_mode: str, target_files: str = "documents/*.txt", 
                comparison_target: Optional[str] = None, output_format: str = "summary") -> str:
        """Execute advanced document analysis using safe system commands."""
        
        try:
            automation = create_research_automation()
            results = []
            
            if analysis_mode == "content_extract":
                # Extract and summarize content from documents
                results.append("=== CONTENT EXTRACTION ANALYSIS ===")
                
                # Count total files
                count_cmd = f"find {target_files.split('*')[0] if '*' in target_files else target_files} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | wc -l"
                count_result = automation.execute_safe_command(count_cmd)
                if count_result.success:
                    results.append(f"Total files found: {count_result.output.strip()}")
                
                # Extract first few lines from each file
                preview_cmd = f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | head -10 | xargs -I {{}} sh -c 'echo \"=== {{}} ===\"; head -5 \"{{}}\"; echo'"
                preview_result = automation.execute_safe_command(preview_cmd)
                if preview_result.success:
                    results.append("Content previews:")
                    results.append(preview_result.output)
                else:
                    results.append(f"Error extracting content: {preview_result.error}")
            
            elif analysis_mode == "word_frequency":
                # Analyze word frequency in documents
                results.append("=== WORD FREQUENCY ANALYSIS ===")
                
                # Most common words (excluding common stopwords)
                freq_cmd = f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs cat | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' '\\n' | grep -E '^[a-z]{{3,}}$' | sort | uniq -c | sort -nr | head -20"
                freq_result = automation.execute_safe_command(freq_cmd)
                if freq_result.success:
                    results.append("Top 20 words by frequency:")
                    results.append(freq_result.output)
                else:
                    results.append(f"Error analyzing word frequency: {freq_result.error}")
                
                # Total word count
                total_cmd = f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs wc -w | tail -1"
                total_result = automation.execute_safe_command(total_cmd)
                if total_result.success:
                    results.append(f"\\nTotal word count: {total_result.output.strip()}")
            
            elif analysis_mode == "similarity_check":
                if not comparison_target:
                    return "Error: comparison_target is required for similarity_check mode"
                
                results.append("=== DOCUMENT SIMILARITY ANALYSIS ===")
                
                # Compare documents using word overlap
                similarity_cmd = f"comm -12 <(cat {comparison_target} | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' '\\n' | sort -u) <(find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs cat | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' '\\n' | sort -u) | wc -l"
                similarity_result = automation.execute_safe_command(f"bash -c \"{similarity_cmd}\"")
                if similarity_result.success:
                    results.append(f"Common unique words with {comparison_target}: {similarity_result.output.strip()}")
                else:
                    results.append(f"Error checking similarity: {similarity_result.error}")
            
            elif analysis_mode == "structure_analysis":
                # Analyze document structure (lines, paragraphs, sections)
                results.append("=== DOCUMENT STRUCTURE ANALYSIS ===")
                
                structure_cmds = [
                    (f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs wc -l | tail -1", "Total lines"),
                    (f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs grep -c '^$' | awk -F: '{{sum+=$2}} END {{print sum}}'", "Empty lines (paragraph breaks)"),
                    (f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs grep -c '^#' | awk -F: '{{sum+=$2}} END {{print sum}}'", "Markdown headers"),
                ]
                
                for cmd, description in structure_cmds:
                    struct_result = automation.execute_safe_command(f"bash -c \"{cmd}\"")
                    if struct_result.success:
                        results.append(f"{description}: {struct_result.output.strip()}")
                    else:
                        results.append(f"{description}: Error - {struct_result.error}")
            
            elif analysis_mode == "metadata_extract":
                # Extract metadata from files
                results.append("=== DOCUMENT METADATA ANALYSIS ===")
                
                # File sizes and modification dates
                meta_cmd = f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f -exec ls -lh {{}} \\; | awk '{{print $5, $6, $7, $8, $9}}'"
                meta_result = automation.execute_safe_command(meta_cmd)
                if meta_result.success:
                    results.append("File metadata (size, date, name):")
                    results.append(meta_result.output)
                else:
                    results.append(f"Error extracting metadata: {meta_result.error}")
                
                # File type analysis
                type_cmd = f"find {target_files.split('*')[0] if '*' in target_files else '.'} -name '{target_files.split('/')[-1] if '/' in target_files else target_files}' -type f | xargs file | cut -d: -f2 | sort | uniq -c"
                type_result = automation.execute_safe_command(type_cmd)
                if type_result.success:
                    results.append("\\nFile type distribution:")
                    results.append(type_result.output)
            
            else:
                return f"Unknown analysis mode: {analysis_mode}"
            
            # Add session summary
            session = automation.get_session_summary()
            results.append(f"\\n=== ANALYSIS COMPLETE ===")
            results.append(f"Commands executed: {session['total_commands']}")
            results.append(f"Session ID: {session['session_id']}")
            
            return "\\n".join(results)
            
        except Exception as e:
            return f"Document analysis failed: {str(e)}"
