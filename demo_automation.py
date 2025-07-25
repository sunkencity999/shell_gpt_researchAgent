#!/usr/bin/env python3
"""
Standalone Research Automation Demo
Tests the automation system without full ResearchAgent dependencies.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_command_validation():
    """Demonstrate command validation without imports"""
    print("🛡️  COMMAND VALIDATION DEMO")
    print("=" * 50)
    
    # Import here to avoid dependency issues
    from sgptAgent.research_automation import SafeCommandValidator, SecurityLevel
    
    validator = SafeCommandValidator()
    
    test_commands = [
        # Safe commands
        "ls -la documents/",
        "find documents -name '*.txt' | head -10", 
        "grep -c 'research' documents/*.txt",
        "curl -I https://example.com",
        "whois google.com",
        "date",
        "uname -a",
        
        # Moderate commands
        "mkdir documents/new_research",
        "cp document.txt documents/backup.txt",
        
        # Dangerous commands (should be blocked)
        "rm -rf /",
        "sudo apt install something", 
        "chmod 777 /etc/passwd",
        "systemctl stop nginx"
    ]
    
    for cmd in test_commands:
        level, approved, reason = validator.validate_command(cmd)
        status = "✅ APPROVED" if approved else "❌ BLOCKED"
        security_color = {"safe": "🟢", "moderate": "🟡", "advanced": "🔴"}
        print(f"{status} {security_color.get(level.value, '⚪')} [{level.value.upper()}] {cmd}")
        print(f"   → {reason}")
        print()

def demo_safe_execution():
    """Demonstrate safe command execution"""
    print("⚡ SAFE EXECUTION DEMO")
    print("=" * 50)
    
    from sgptAgent.research_automation import ResearchAutomation
    
    automation = ResearchAutomation("documents")
    
    # Test safe commands that should work on any system
    safe_commands = [
        "echo 'Hello from ResearchAgent automation!'",
        "date", 
        "pwd",
        "whoami",
        "uname -s"
    ]
    
    print("Executing safe commands:")
    for cmd in safe_commands:
        print(f"\n🔧 Executing: {cmd}")
        result = automation.execute_safe_command(cmd)
        
        if result.success:
            print(f"✅ Success (exit code {result.exit_code})")
            print(f"Output: {result.output}")
        else:
            print(f"❌ Failed (exit code {result.exit_code})")
            print(f"Error: {result.error}")
        
        print(f"Security Level: {result.security_level.value}")
    
    # Show session summary
    print("\n📊 SESSION SUMMARY")
    print("-" * 30)
    summary = automation.get_session_summary()
    for key, value in summary.items():
        if value is not None:
            print(f"{key}: {value}")

def demo_research_suggestions():
    """Demonstrate intelligent research suggestions"""
    print("💡 RESEARCH SUGGESTIONS DEMO")
    print("=" * 50)
    
    from sgptAgent.research_automation import ResearchAutomation
    
    automation = ResearchAutomation()
    
    research_goals = [
        "analyze data files in my research directory",
        "research website information for competitor analysis", 
        "check system performance for my analysis",
        "find documents about climate change"
    ]
    
    for goal in research_goals:
        print(f"Research Goal: '{goal}'")
        suggestions = automation.get_command_suggestions(goal)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. [{suggestion['category']}] {suggestion['command']}")
            print(f"     → {suggestion['description']}")
        print()

def demo_script_creation():
    """Demonstrate research script creation"""
    print("📜 SCRIPT CREATION DEMO")
    print("=" * 50)
    
    from sgptAgent.research_automation import ResearchAutomation
    
    automation = ResearchAutomation("documents")
    
    # Example research commands
    research_commands = [
        "echo 'Starting research automation...'",
        "date",
        "ls -la",
        "find . -name '*.txt' | wc -l",
        "echo 'Research automation completed!'",
        "rm -rf /"  # This dangerous command should be filtered out
    ]
    
    print("Creating research automation script...")
    script_path = automation.create_research_script(research_commands, "demo_research.sh")
    
    print(f"✅ Script created: {script_path}")
    
    # Show script content
    print("\n📄 Script content:")
    print("-" * 30)
    try:
        with open(script_path, 'r') as f:
            content = f.read()
        print(content)
    except Exception as e:
        print(f"Error reading script: {e}")

def main():
    """Run all demonstrations"""
    print("🚀 RESEARCHAGENT AUTOMATION SYSTEM DEMO")
    print("=" * 60)
    print("Testing safe, research-focused system integration")
    print("=" * 60)
    print()
    
    demos = [
        ("Command Validation", demo_command_validation),
        ("Safe Execution", demo_safe_execution), 
        ("Research Suggestions", demo_research_suggestions),
        ("Script Creation", demo_script_creation)
    ]
    
    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            print(f"\n{'='*15} DEMO {i}/{len(demos)}: {name} {'='*15}")
            demo_func()
            print(f"{'='*60}")
        except Exception as e:
            print(f"❌ Demo {i} ({name}) failed: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}")
        
        if i < len(demos):
            print("\nPress Enter to continue to next demo...")
            input()
    
    print("\n🎉 AUTOMATION DEMO COMPLETED!")
    print("\n✨ ResearchAgent now has safe, powerful system integration:")
    print("   🛡️  Multi-tier security validation")
    print("   📚 Research-focused command library") 
    print("   📝 Comprehensive audit logging")
    print("   💡 Intelligent automation suggestions")
    print("   🔧 Integration with existing shell-gpt functions")
    print("   📜 Automated script generation")

if __name__ == "__main__":
    main()
