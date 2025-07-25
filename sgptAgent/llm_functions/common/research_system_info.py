"""
Research System Information Function
Safe system information gathering for research context and technical analysis.
"""

import json
from instructor import OpenAISchema
from pydantic import Field
from typing import Optional

from ...research_automation import create_research_automation


class Function(OpenAISchema):
    """
    Gather system information for research context. Useful for technical research,
    performance analysis, or understanding the research environment.
    """

    info_type: str = Field(
        ...,
        example="overview",
        description="Info type: 'overview', 'performance', 'network', 'storage', 'processes', 'environment'",
    )
    
    detailed: bool = Field(
        default=False,
        description="Whether to provide detailed information (may take longer)",
    )

    class Config:
        title = "gather_system_info"

    @classmethod
    def execute(cls, info_type: str, detailed: bool = False) -> str:
        """Gather system information using safe commands."""
        
        try:
            automation = create_research_automation()
            results = []
            
            if info_type == "overview":
                # Basic system overview
                commands = [
                    ("uname -a", "System information"),
                    ("whoami", "Current user"),
                    ("date", "Current date/time"),
                    ("uptime", "System uptime"),
                ]
                
                if detailed:
                    commands.extend([
                        ("lscpu | head -20", "CPU information"),
                        ("free -h", "Memory usage"),
                        ("df -h", "Disk usage"),
                    ])
                
                results.append("=== SYSTEM OVERVIEW ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"{desc}: {result.output.strip()}")
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            elif info_type == "performance":
                # System performance metrics
                commands = [
                    ("free -h", "Memory usage"),
                    ("df -h", "Disk usage"),
                    ("top -bn1 | head -20", "Process overview"),
                ]
                
                if detailed:
                    commands.extend([
                        ("ps aux --sort=-%cpu | head -15", "Top CPU processes"),
                        ("ps aux --sort=-%mem | head -15", "Top memory processes"),
                        ("iostat", "I/O statistics") if automation.execute_safe_command("which iostat").success else None,
                    ])
                    commands = [cmd for cmd in commands if cmd is not None]
                
                results.append("=== SYSTEM PERFORMANCE ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"\n{desc}:")
                        results.append(result.output.strip())
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            elif info_type == "network":
                # Network information
                commands = [
                    ("hostname", "Hostname"),
                    ("hostname -I", "IP addresses"),
                ]
                
                if detailed:
                    commands.extend([
                        ("netstat -i", "Network interfaces"),
                        ("ss -tuln | head -20", "Listening ports"),
                    ])
                
                results.append("=== NETWORK INFORMATION ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"{desc}: {result.output.strip()}")
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            elif info_type == "storage":
                # Storage and filesystem information
                commands = [
                    ("df -h", "Disk usage by filesystem"),
                    ("du -sh documents/", "Research directory size"),
                ]
                
                if detailed:
                    commands.extend([
                        ("lsblk", "Block devices"),
                        ("find documents/ -type f | wc -l", "Total files in research dir"),
                        ("find documents/ -name '*.txt' | wc -l", "Text files in research dir"),
                        ("find documents/ -name '*.pdf' | wc -l", "PDF files in research dir"),
                    ])
                
                results.append("=== STORAGE INFORMATION ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"{desc}:")
                        results.append(result.output.strip())
                        results.append("")
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            elif info_type == "processes":
                # Process information
                commands = [
                    ("ps aux --sort=-%cpu | head -15", "Top CPU processes"),
                    ("ps aux --sort=-%mem | head -15", "Top memory processes"),
                ]
                
                if detailed:
                    commands.extend([
                        ("pgrep -l python", "Python processes"),
                        ("pgrep -l ollama", "Ollama processes"),
                        ("ps aux | grep -E '(firefox|chrome|browser)' | grep -v grep", "Browser processes"),
                    ])
                
                results.append("=== PROCESS INFORMATION ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        output = result.output.strip()
                        if output:
                            results.append(f"\n{desc}:")
                            results.append(output)
                        else:
                            results.append(f"{desc}: No matching processes found")
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            elif info_type == "environment":
                # Environment and research setup information
                commands = [
                    ("pwd", "Current directory"),
                    ("echo $HOME", "Home directory"),
                    ("echo $PATH | tr ':' '\\n' | head -10", "PATH (first 10 entries)"),
                ]
                
                if detailed:
                    commands.extend([
                        ("python3 --version", "Python version"),
                        ("which python3", "Python location"),
                        ("pip3 list | grep -E '(torch|tensorflow|scipy|numpy|pandas)' | head -10", "AI/ML packages"),
                        ("ls -la ~/.local/bin/ | head -10", "User binaries"),
                    ])
                
                results.append("=== ENVIRONMENT INFORMATION ===")
                for cmd, desc in commands:
                    result = automation.execute_safe_command(cmd)
                    if result.success:
                        results.append(f"{desc}: {result.output.strip()}")
                    else:
                        results.append(f"{desc}: Error - {result.error}")
            
            else:
                return f"Unknown info type: {info_type}"
            
            # Add session summary
            session = automation.get_session_summary()
            results.append(f"\n=== SESSION INFO ===")
            results.append(f"Commands executed: {session['total_commands']}")
            results.append(f"Session ID: {session['session_id']}")
            
            return "\n".join(results)
            
        except Exception as e:
            return f"System information gathering failed: {str(e)}"
