"""
Safe Research-Focused System Integration and Automation

This module provides secure, research-focused system integration capabilities
while maintaining strict security controls and command validation.
"""

import os
import subprocess
import shlex
import tempfile
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import re
from dataclasses import dataclass
from enum import Enum

class SecurityLevel(Enum):
    """Security levels for command execution"""
    SAFE = "safe"           # Read-only, no system modification
    MODERATE = "moderate"   # Limited file operations in research directory
    ADVANCED = "advanced"   # Broader system access (requires explicit user consent)

@dataclass
class CommandResult:
    """Result of a system command execution"""
    success: bool
    output: str
    error: str
    exit_code: int
    security_level: SecurityLevel
    command: str
    timestamp: datetime

class SafeCommandValidator:
    """Validates and categorizes commands for safe research automation"""
    
    def __init__(self):
        # Define safe research-focused commands by category
        self.safe_commands = {
            # File system operations (read-only)
            'filesystem_read': {
                'commands': ['ls', 'find', 'grep', 'cat', 'head', 'tail', 'wc', 'file', 'stat', 'du', 'df'],
                'description': 'Read-only file system operations'
            },
            # Text processing and analysis
            'text_processing': {
                'commands': ['sort', 'uniq', 'cut', 'awk', 'sed', 'tr', 'fold', 'expand', 'unexpand'],
                'description': 'Text processing and analysis tools'
            },
            # Data analysis and conversion
            'data_analysis': {
                'commands': ['jq', 'csvkit', 'python3', 'node', 'sqlite3'],
                'description': 'Data analysis and conversion tools',
                'restrictions': {'python3': ['-c', 'script.py'], 'node': ['-e', 'script.js']}
            },
            # Network information (safe)
            'network_info': {
                'commands': ['ping', 'nslookup', 'dig', 'whois', 'curl', 'wget'],
                'description': 'Network information gathering',
                'restrictions': {
                    'curl': ['--max-time'],  # More flexible - just require timeout
                    'wget': ['--timeout', '--tries']
                }
            },
            # System information (read-only)
            'system_info': {
                'commands': ['uname', 'whoami', 'id', 'date', 'uptime', 'ps', 'top', 'free', 'lscpu'],
                'description': 'System information gathering'
            },
            # Basic shell utilities
            'shell_utilities': {
                'commands': ['echo', 'pwd', 'which', 'type', 'basename', 'dirname', 'env', 'printenv'],
                'description': 'Basic shell utility commands'
            }
        }
        
        # Commands that require moderate security (file creation in research dir)
        self.moderate_commands = {
            'research_files': {
                'commands': ['mkdir', 'touch', 'cp', 'mv', 'ln'],
                'description': 'File operations within research directory',
                'path_restrictions': ['documents/', 'research/', '/tmp/research_']
            },
            'data_export': {
                'commands': ['tee', 'dd'],
                'description': 'Data export and backup within research scope'
            }
        }
        
        # Dangerous commands that are never allowed
        self.forbidden_commands = {
            'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs',
            'sudo', 'su', 'passwd', 'chown', 'chmod', 'chroot',
            'systemctl', 'service', 'mount', 'umount',
            'iptables', 'ufw', 'firewall-cmd',
            'crontab', 'at', 'batch',
            'reboot', 'shutdown', 'halt', 'poweroff'
        }
    
    def validate_command(self, command_str: str) -> Tuple[SecurityLevel, bool, str]:
        """
        Validate a command and return security level, approval status, and reason.
        
        Returns:
            (SecurityLevel, is_approved, reason)
        """
        try:
            # Parse command safely
            parts = shlex.split(command_str.strip())
            if not parts:
                return SecurityLevel.SAFE, False, "Empty command"
            
            base_command = parts[0]
            
            # Check forbidden commands
            if base_command in self.forbidden_commands:
                return SecurityLevel.ADVANCED, False, f"Command '{base_command}' is forbidden for security"
            
            # Check safe commands
            for category, info in self.safe_commands.items():
                if base_command in info['commands']:
                    # Check for restrictions
                    if 'restrictions' in info and base_command in info['restrictions']:
                        required_args = info['restrictions'][base_command]
                        if not self._check_required_args(parts[1:], required_args):
                            return SecurityLevel.MODERATE, False, f"Command '{base_command}' missing required safety arguments"
                    return SecurityLevel.SAFE, True, f"Safe {category} command"
            
            # Check moderate commands
            for category, info in self.moderate_commands.items():
                if base_command in info['commands']:
                    if 'path_restrictions' in info:
                        if not self._check_path_restrictions(parts[1:], info['path_restrictions']):
                            return SecurityLevel.ADVANCED, False, f"Command '{base_command}' targets unsafe path"
                    return SecurityLevel.MODERATE, True, f"Moderate {category} command"
            
            # Unknown command - requires advanced security
            return SecurityLevel.ADVANCED, False, f"Unknown command '{base_command}' requires explicit approval"
        
        except Exception as e:
            return SecurityLevel.ADVANCED, False, f"Command parsing error: {str(e)}"
    
    def _check_required_args(self, args: List[str], required: List[str]) -> bool:
        """Check if required arguments are present"""
        for req in required:
            if req not in args:
                return False
        return True
    
    def _check_path_restrictions(self, args: List[str], allowed_paths: List[str]) -> bool:
        """Check if file paths are within allowed directories"""
        for arg in args:
            if os.path.sep in arg or arg.startswith('/'):  # Looks like a path
                if not any(arg.startswith(allowed) for allowed in allowed_paths):
                    return False
        return True

class ResearchAutomation:
    """Main class for safe research automation and system integration"""
    
    def __init__(self, research_dir: Optional[str] = None, approval_callback=None):
        self.validator = SafeCommandValidator()
        self.research_dir = Path(research_dir) if research_dir else Path("documents")
        self.command_history: List[CommandResult] = []
        self.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        
        # Callback function for requesting user approval
        self.approval_callback = approval_callback
        
        # Create research directory if it doesn't exist
        self.research_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session log
        self.log_file = self.research_dir / f"automation_log_{self.session_id}.json"
    
    def execute_safe_command(self, command: str, allow_moderate: bool = True, 
                           user_approved_advanced: bool = False, auto_approve: bool = False) -> CommandResult:
        """
        Execute a command with safety validation and logging.
        
        Args:
            command: The command to execute
            allow_moderate: Whether to allow moderate security level commands
            user_approved_advanced: Whether user has explicitly approved advanced commands
            auto_approve: Whether to automatically request approval for restricted commands
        
        Returns:
            CommandResult with execution details
        """
        timestamp = datetime.now()
        
        try:
            # Validate command
            security_level, is_approved, reason = self.validator.validate_command(command)
            
            # Handle bash commands and other advanced operations that need approval
            if not is_approved and 'bash' in command.lower():
                # Special handling for bash commands - they can be useful for research
                security_level = SecurityLevel.ADVANCED
                is_approved = False  # Will be handled below
                reason = "Bash commands require user approval for security"
            
            # Check approval based on security level
            if not is_approved:
                # Check if we should request user approval
                if (security_level in [SecurityLevel.MODERATE, SecurityLevel.ADVANCED] and 
                    self.approval_callback and auto_approve):
                    
                    # Request user approval through callback
                    approval_granted = self.approval_callback(
                        command=command,
                        security_level=security_level.value,
                        reason=reason
                    )
                    
                    if approval_granted:
                        if security_level == SecurityLevel.MODERATE:
                            allow_moderate = True
                        elif security_level == SecurityLevel.ADVANCED:
                            user_approved_advanced = True
                    else:
                        result = CommandResult(
                            success=False,
                            output="",
                            error=f"Command rejected by user: {reason}",
                            exit_code=-1,
                            security_level=security_level,
                            command=command,
                            timestamp=timestamp
                        )
                        self._log_command(result)
                        return result
                else:
                    result = CommandResult(
                        success=False,
                        output="",
                        error=f"Command rejected: {reason}",
                        exit_code=-1,
                        security_level=security_level,
                        command=command,
                        timestamp=timestamp
                    )
                    self._log_command(result)
                    return result
            
            # Check user permissions
            if security_level == SecurityLevel.MODERATE and not allow_moderate:
                # Try to get approval if callback available
                if self.approval_callback and auto_approve:
                    approval_granted = self.approval_callback(
                        command=command,
                        security_level=security_level.value,
                        reason="Moderate security command requires approval"
                    )
                    if not approval_granted:
                        result = CommandResult(
                            success=False,
                            output="",
                            error="Moderate security command rejected by user",
                            exit_code=-1,
                            security_level=security_level,
                            command=command,
                            timestamp=timestamp
                        )
                        self._log_command(result)
                        return result
                else:
                    result = CommandResult(
                        success=False,
                        output="",
                        error="Moderate security commands not allowed in current context",
                        exit_code=-1,
                        security_level=security_level,
                        command=command,
                        timestamp=timestamp
                    )
                    self._log_command(result)
                    return result
            
            if security_level == SecurityLevel.ADVANCED and not user_approved_advanced:
                # Try to get approval if callback available
                if self.approval_callback and auto_approve:
                    approval_granted = self.approval_callback(
                        command=command,
                        security_level=security_level.value,
                        reason="Advanced security command requires approval"
                    )
                    if not approval_granted:
                        result = CommandResult(
                            success=False,
                            output="",
                            error="Advanced security command rejected by user",
                            exit_code=-1,
                            security_level=security_level,
                            command=command,
                            timestamp=timestamp
                        )
                        self._log_command(result)
                        return result
                else:
                    result = CommandResult(
                        success=False,
                        output="",
                        error="Advanced security commands require explicit user approval",
                        exit_code=-1,
                        security_level=security_level,
                        command=command,
                        timestamp=timestamp
                    )
                    self._log_command(result)
                    return result
            
            # Execute command with timeout and working directory restrictions
            # Handle timeout parameter compatibility across Python versions
            popen_kwargs = {
                'shell': True,
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True,
                'cwd': str(self.research_dir) if security_level != SecurityLevel.SAFE else None
            }
            
            process = subprocess.Popen(command, **popen_kwargs)
            
            try:
                # Use communicate with timeout (Python 3.3+)
                stdout, stderr = process.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(command, 60)
            
            result = CommandResult(
                success=process.returncode == 0,
                output=stdout.strip() if stdout else "",
                error=stderr.strip() if stderr else "",
                exit_code=process.returncode,
                security_level=security_level,
                command=command,
                timestamp=timestamp
            )
            
        except subprocess.TimeoutExpired:
            result = CommandResult(
                success=False,
                output="",
                error="Command timed out after 60 seconds",
                exit_code=-2,
                security_level=security_level,
                command=command,
                timestamp=timestamp
            )
        except Exception as e:
            result = CommandResult(
                success=False,
                output="",
                error=f"Execution error: {str(e)}",
                exit_code=-3,
                security_level=security_level,
                command=command,
                timestamp=timestamp
            )
        
        # Log the result
        self._log_command(result)
        self.command_history.append(result)
        
        return result
    
    def _log_command(self, result: CommandResult):
        """Log command execution to session log file"""
        log_entry = {
            'timestamp': result.timestamp.isoformat(),
            'command': result.command,
            'success': result.success,
            'exit_code': result.exit_code,
            'security_level': result.security_level.value,
            'output_length': len(result.output),
            'error': result.error if result.error else None
        }
        
        try:
            # Append to log file
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def get_command_suggestions(self, research_goal: str) -> List[Dict[str, str]]:
        """
        Generate safe command suggestions based on research goal.
        
        Args:
            research_goal: The research objective
            
        Returns:
            List of suggested commands with descriptions
        """
        suggestions = []
        
        # Analyze research goal for keywords
        goal_lower = research_goal.lower()
        
        # File analysis suggestions
        if any(word in goal_lower for word in ['file', 'document', 'text', 'data']):
            suggestions.extend([
                {
                    'command': 'find documents -name "*.txt" -o -name "*.md" -o -name "*.pdf" | head -20',
                    'description': 'Find text documents in research directory',
                    'category': 'File Discovery'
                },
                {
                    'command': 'ls -la documents/',
                    'description': 'List all files in research directory with details',
                    'category': 'File Analysis'
                }
            ])
        
        # Network research suggestions
        if any(word in goal_lower for word in ['website', 'domain', 'url', 'online', 'web']):
            suggestions.extend([
                {
                    'command': 'whois example.com',
                    'description': 'Get domain information (replace example.com)',
                    'category': 'Network Research'
                },
                {
                    'command': 'curl -I https://example.com',
                    'description': 'Get website headers (replace URL)',
                    'category': 'Network Research'
                }
            ])
        
        # Data analysis suggestions
        if any(word in goal_lower for word in ['analyze', 'data', 'statistics', 'count', 'measure']):
            suggestions.extend([
                {
                    'command': 'wc -l documents/*.txt',
                    'description': 'Count lines in text files',
                    'category': 'Data Analysis'
                },
                {
                    'command': 'grep -c "keyword" documents/*.txt',
                    'description': 'Count occurrences of keyword in files',
                    'category': 'Data Analysis'
                }
            ])
        
        # System information suggestions
        if any(word in goal_lower for word in ['system', 'computer', 'hardware', 'performance']):
            suggestions.extend([
                {
                    'command': 'uname -a',
                    'description': 'Get system information',
                    'category': 'System Info'
                },
                {
                    'command': 'df -h',
                    'description': 'Check disk space usage',
                    'category': 'System Info'
                }
            ])
        
        return suggestions
    
    def create_research_script(self, commands: List[str], script_name: str = None) -> str:
        """
        Create a safe research automation script from validated commands.
        
        Args:
            commands: List of commands to include in script
            script_name: Optional name for the script file
            
        Returns:
            Path to the created script file
        """
        if not script_name:
            script_name = f"research_automation_{self.session_id}.sh"
        
        script_path = self.research_dir / script_name
        
        # Validate all commands first
        validated_commands = []
        for cmd in commands:
            level, approved, reason = self.validator.validate_command(cmd)
            if approved and level in [SecurityLevel.SAFE, SecurityLevel.MODERATE]:
                validated_commands.append(f"# {reason}\n{cmd}")
            else:
                validated_commands.append(f"# SKIPPED: {reason}\n# {cmd}")
        
        # Create script content
        script_content = f"""#!/bin/bash
# Research Automation Script
# Created: {datetime.now().isoformat()}
# Session: {self.session_id}

set -e  # Exit on error
set -u  # Exit on undefined variable

# Change to research directory
cd "{self.research_dir.absolute()}"

echo "Starting research automation..."
echo "Working directory: $(pwd)"
echo "Timestamp: $(date)"
echo "===================="

{chr(10).join(validated_commands)}

echo "===================="
echo "Research automation completed at $(date)"
"""
        
        # Write script file
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        return str(script_path)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current automation session"""
        successful_commands = sum(1 for cmd in self.command_history if cmd.success)
        failed_commands = len(self.command_history) - successful_commands
        
        security_breakdown = {}
        for level in SecurityLevel:
            security_breakdown[level.value] = sum(
                1 for cmd in self.command_history if cmd.security_level == level
            )
        
        return {
            'session_id': self.session_id,
            'research_directory': str(self.research_dir),
            'total_commands': len(self.command_history),
            'successful_commands': successful_commands,
            'failed_commands': failed_commands,
            'security_breakdown': security_breakdown,
            'log_file': str(self.log_file) if self.log_file.exists() else None,
            'start_time': self.command_history[0].timestamp.isoformat() if self.command_history else None,
            'last_command_time': self.command_history[-1].timestamp.isoformat() if self.command_history else None
        }


# Convenience functions for integration with ResearchAgent

def create_research_automation(research_dir: str = None, approval_callback=None) -> ResearchAutomation:
    """Create a new research automation instance with optional approval callback"""
    return ResearchAutomation(research_dir, approval_callback)

def validate_research_command(command: str) -> Tuple[str, bool, str]:
    """Validate a single research command"""
    validator = SafeCommandValidator()
    security_level, is_approved, reason = validator.validate_command(command)
    return security_level.value, is_approved, reason

def get_safe_research_suggestions(research_goal: str) -> List[dict]:
    """Get safe command suggestions for a research goal"""
    automation = ResearchAutomation()
    return automation.get_command_suggestions(research_goal)

def execute_research_command_with_approval(command: str, research_dir: str = None, 
                                          approval_callback=None, auto_approve: bool = True):
    """Execute a research command with automatic approval workflow"""
    automation = ResearchAutomation(research_dir, approval_callback)
    return automation.execute_safe_command(command, allow_moderate=True, 
                                         user_approved_advanced=False, 
                                         auto_approve=auto_approve)
