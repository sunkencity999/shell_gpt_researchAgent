"""
Research Data Visualization Function
Generate charts and visualizations from research data using command-line tools.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional

from ...research_automation import create_research_automation


class Function(OpenAISchema):
    """
    Create data visualizations and charts from research data using safe command-line tools.
    Supports histograms, bar charts, data distribution analysis, and ASCII charts.
    """

    chart_type: str = Field(
        ...,
        example="histogram",
        description="Chart type: 'histogram', 'bar_chart', 'distribution', 'ascii_chart', 'data_summary'",
    )
    
    data_source: str = Field(
        ...,
        example="documents/data.csv",
        description="Path to data file or command to generate data",
    )
    
    column_name: Optional[str] = Field(
        default=None,
        example="price",
        description="Column name for analysis (for CSV data)",
    )
    
    output_file: Optional[str] = Field(
        default=None,
        example="chart_output.txt",
        description="Optional output file for saving chart",
    )

    class Config:
        title = "create_data_visualization"

    @classmethod
    def execute(cls, chart_type: str, data_source: str, 
                column_name: Optional[str] = None, output_file: Optional[str] = None) -> str:
        """Create data visualizations using safe command-line tools."""
        
        try:
            automation = create_research_automation()
            results = []
            
            if chart_type == "histogram":
                # Create histogram from numeric data
                results.append("=== HISTOGRAM ANALYSIS ===")
                
                if column_name and data_source.endswith('.csv'):
                    # Extract column from CSV and create histogram
                    extract_cmd = f"cut -d',' -f1 {data_source} | tail -n +2 | sort -n"
                    extract_result = automation.execute_safe_command(extract_cmd)
                    if extract_result.success:
                        # Create simple ASCII histogram
                        hist_cmd = f"echo '{extract_result.output}' | awk '{{count[int($1/10)*10]++}} END {{for (i in count) print i, count[i]}}' | sort -n"
                        hist_result = automation.execute_safe_command(f"bash -c \"{hist_cmd}\"")
                        if hist_result.success:
                            results.append("Histogram distribution (value ranges and counts):")
                            results.append(hist_result.output)
                        else:
                            results.append(f"Error creating histogram: {hist_result.error}")
                    else:
                        results.append(f"Error extracting data: {extract_result.error}")
                else:
                    # Simple numeric data histogram
                    hist_cmd = f"cat {data_source} | sort -n | awk '{{count[int($1/10)*10]++}} END {{for (i in count) print i, count[i]}}' | sort -n"
                    hist_result = automation.execute_safe_command(f"bash -c \"{hist_cmd}\"")
                    if hist_result.success:
                        results.append("Histogram distribution:")
                        results.append(hist_result.output)
                    else:
                        results.append(f"Error creating histogram: {hist_result.error}")
            
            elif chart_type == "bar_chart":
                # Create bar chart from categorical data
                results.append("=== BAR CHART ANALYSIS ===")
                
                # Count occurrences and create ASCII bar chart
                bar_cmd = f"cat {data_source} | sort | uniq -c | sort -nr | head -20"
                bar_result = automation.execute_safe_command(bar_cmd)
                if bar_result.success:
                    results.append("Top 20 categories (count and value):")
                    results.append(bar_result.output)
                    
                    # Create ASCII visualization
                    ascii_cmd = f"cat {data_source} | sort | uniq -c | sort -nr | head -10 | awk '{{printf \"%-20s |%s\\n\", $2, substr(\"########################################\", 1, $1/10)}}'"
                    ascii_result = automation.execute_safe_command(f"bash -c \"{ascii_cmd}\"")
                    if ascii_result.success:
                        results.append("\\nASCII Bar Chart:")
                        results.append(ascii_result.output)
                else:
                    results.append(f"Error creating bar chart: {bar_result.error}")
            
            elif chart_type == "distribution":
                # Analyze data distribution statistics
                results.append("=== DISTRIBUTION ANALYSIS ===")
                
                # Basic statistics
                stats_cmds = [
                    (f"cat {data_source} | wc -l", "Total data points"),
                    (f"cat {data_source} | sort -n | head -1", "Minimum value"),
                    (f"cat {data_source} | sort -n | tail -1", "Maximum value"),
                    (f"cat {data_source} | awk '{{sum+=$1}} END {{print sum/NR}}'", "Mean (average)"),
                ]
                
                for cmd, description in stats_cmds:
                    stats_result = automation.execute_safe_command(f"bash -c \"{cmd}\"")
                    if stats_result.success:
                        results.append(f"{description}: {stats_result.output.strip()}")
                    else:
                        results.append(f"{description}: Error - {stats_result.error}")
                
                # Quartiles
                quartile_cmd = f"cat {data_source} | sort -n | awk '{{all[NR] = $0}} END{{print \"Q1:\", all[int(NR*0.25)]; print \"Median:\", all[int(NR*0.5)]; print \"Q3:\", all[int(NR*0.75)]}}'"
                quartile_result = automation.execute_safe_command(f"bash -c \"{quartile_cmd}\"")
                if quartile_result.success:
                    results.append("\\nQuartiles:")
                    results.append(quartile_result.output)
            
            elif chart_type == "ascii_chart":
                # Create simple ASCII line chart
                results.append("=== ASCII LINE CHART ===")
                
                # Create time series or sequential ASCII chart
                chart_cmd = f"cat {data_source} | awk '{{printf \"%3d |%s\\n\", NR, substr(\"********************************\", 1, $1/2)}}'"
                chart_result = automation.execute_safe_command(f"bash -c \"{chart_cmd}\"")
                if chart_result.success:
                    results.append("ASCII Line Chart (row | value visualization):")
                    results.append(chart_result.output)
                else:
                    results.append(f"Error creating ASCII chart: {chart_result.error}")
            
            elif chart_type == "data_summary":
                # Comprehensive data summary
                results.append("=== DATA SUMMARY REPORT ===")
                
                # File information
                file_info_cmd = f"ls -lh {data_source}"
                file_info_result = automation.execute_safe_command(file_info_cmd)
                if file_info_result.success:
                    results.append(f"File info: {file_info_result.output.strip()}")
                
                # Data preview
                preview_cmd = f"head -10 {data_source}"
                preview_result = automation.execute_safe_command(preview_cmd)
                if preview_result.success:
                    results.append("\\nData preview (first 10 lines):")
                    results.append(preview_result.output)
                
                # Data characteristics
                char_cmds = [
                    (f"cat {data_source} | wc -l", "Total lines"),
                    (f"grep -c '^[0-9]' {data_source}", "Numeric lines"),
                    (f"cat {data_source} | sort | uniq | wc -l", "Unique values"),
                    (f"grep -c '^$' {data_source}", "Empty lines"),
                ]
                
                results.append("\\nData characteristics:")
                for cmd, description in char_cmds:
                    char_result = automation.execute_safe_command(f"bash -c \"{cmd}\"")
                    if char_result.success:
                        results.append(f"  {description}: {char_result.output.strip()}")
            
            else:
                return f"Unknown chart type: {chart_type}"
            
            # Save output if requested
            if output_file:
                save_cmd = f"echo '{chr(10).join(results)}' > {output_file}"
                save_result = automation.execute_safe_command(f"bash -c \"{save_cmd}\"", allow_moderate=True)
                if save_result.success:
                    results.append(f"\\n✅ Chart saved to: {output_file}")
                else:
                    results.append(f"\\n❌ Error saving chart: {save_result.error}")
            
            # Add session summary
            session = automation.get_session_summary()
            results.append(f"\\n=== VISUALIZATION COMPLETE ===")
            results.append(f"Commands executed: {session['total_commands']}")
            
            return "\\n".join(results)
            
        except Exception as e:
            return f"Data visualization failed: {str(e)}"
