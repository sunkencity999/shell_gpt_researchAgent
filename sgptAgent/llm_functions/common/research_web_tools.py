"""
Research Web Tools Function
Safe web research automation using system tools.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional

from ...research_automation import create_research_automation


class Function(OpenAISchema):
    """
    Perform web research tasks using safe system tools like curl, wget, whois, and dig.
    Useful for gathering website information, checking domains, and downloading research materials.
    """

    tool_type: str = Field(
        ...,
        example="domain_info",
        description="Tool type: 'domain_info', 'website_headers', 'download_content', 'dns_lookup', 'ping_test'",
    )
    
    target: str = Field(
        ...,
        example="example.com",
        description="Target URL, domain, or IP address for the research tool",
    )
    
    output_file: Optional[str] = Field(
        default=None,
        example="research_data.html",
        description="Optional filename to save output (for download_content)",
    )

    class Config:
        title = "research_web_tools"

    @classmethod
    def execute(cls, tool_type: str, target: str, output_file: Optional[str] = None) -> str:
        """Execute web research tools using safe system commands."""
        
        try:
            automation = create_research_automation()
            results = []
            
            if tool_type == "domain_info":
                # Get comprehensive domain information
                cmd = f"whois {target}"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"Domain information for {target}:")
                    # Truncate long whois output for readability
                    output_lines = result.output.split('\n')[:50]
                    results.append('\n'.join(output_lines))
                    if len(result.output.split('\n')) > 50:
                        results.append("... (output truncated)")
                else:
                    results.append(f"Error getting domain info: {result.error}")
            
            elif tool_type == "website_headers":
                # Get HTTP headers from website
                cmd = f"curl -I --max-time 30 '{target}'"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"HTTP headers for {target}:")
                    results.append(result.output)
                else:
                    results.append(f"Error getting headers: {result.error}")
            
            elif tool_type == "download_content":
                # Download web content for research
                if not output_file:
                    output_file = f"downloaded_content_{hash(target) % 10000}.html"
                
                cmd = f"curl --max-time 60 --user-agent 'ResearchAgent/1.0' -o '{output_file}' '{target}'"
                result = automation.execute_safe_command(cmd, allow_moderate=True)
                if result.success:
                    # Check if file was created and get size
                    size_cmd = f"ls -lh '{output_file}'"
                    size_result = automation.execute_safe_command(size_cmd)
                    if size_result.success:
                        results.append(f"Downloaded content from {target} to {output_file}")
                        results.append(f"File details: {size_result.output}")
                    else:
                        results.append(f"Downloaded content from {target} to {output_file}")
                else:
                    results.append(f"Error downloading content: {result.error}")
            
            elif tool_type == "dns_lookup":
                # Perform DNS lookup
                cmd = f"dig +short {target}"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"DNS lookup for {target}:")
                    if result.output.strip():
                        results.append(result.output)
                    else:
                        results.append("No DNS records found")
                        
                    # Also try A and MX records
                    for record_type in ['A', 'MX', 'NS']:
                        cmd = f"dig +short {target} {record_type}"
                        result = automation.execute_safe_command(cmd)
                        if result.success and result.output.strip():
                            results.append(f"{record_type} records: {result.output.strip()}")
                else:
                    results.append(f"Error performing DNS lookup: {result.error}")
            
            elif tool_type == "ping_test":
                # Test connectivity to target
                cmd = f"ping -c 4 {target}"
                result = automation.execute_safe_command(cmd)
                if result.success:
                    results.append(f"Ping test for {target}:")
                    # Extract key statistics
                    lines = result.output.split('\n')
                    stats_lines = [line for line in lines if 'packet loss' in line or 'round-trip' in line]
                    if stats_lines:
                        results.extend(stats_lines)
                    else:
                        results.append(result.output)
                else:
                    results.append(f"Error pinging target: {result.error}")
            
            else:
                return f"Unknown tool type: {tool_type}"
            
            # Add session summary
            session = automation.get_session_summary()
            results.append(f"\nWeb research completed. Session: {session['session_id']}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"Web research tools failed: {str(e)}"
