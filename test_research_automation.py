#!/usr/bin/env python3
"""
ResearchAgent System Integration Demo
Demonstrates safe, research-focused automation capabilities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sgptAgent.research_automation import (
    create_research_automation, 
    validate_research_command,
    get_safe_research_suggestions,
    SecurityLevel
)

def demo_command_validation():
    """Demonstrate command validation system"""
    print("🛡️  COMMAND VALIDATION DEMO")
    print("=" * 50)
    
    test_commands = [
        # Safe commands
        "ls -la documents/",
        "find documents -name '*.txt' | head -10",
        "grep -c 'research' documents/*.txt",
        "curl -I https://example.com",
        "whois google.com",
        
        # Moderate commands (require explicit approval)
        "mkdir documents/new_research",
        "cp document.txt documents/backup.txt",
        
        # Dangerous commands (should be blocked)
        "rm -rf /",
        "sudo apt install something",
        "chmod 777 /etc/passwd"
    ]
    
    for cmd in test_commands:
        level, approved, reason = validate_research_command(cmd)
        status = "✅ APPROVED" if approved else "❌ BLOCKED"
        print(f"{status} [{level.upper()}] {cmd}")
        print(f"   → {reason}")
        print()

def demo_research_suggestions():
    """Demonstrate intelligent research suggestions"""
    print("💡 RESEARCH SUGGESTIONS DEMO")
    print("=" * 50)
    
    research_goals = [
        "analyze data files in my research directory",
        "research website information for competitor analysis", 
        "check system performance for my analysis",
        "find documents about climate change"
    ]
    
    for goal in research_goals:
        print(f"Research Goal: '{goal}'")
        suggestions = get_safe_research_suggestions(goal)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. [{suggestion['category']}] {suggestion['command']}")
            print(f"     → {suggestion['description']}")
        print()

def demo_safe_execution():
    """Demonstrate safe command execution"""
    print("⚡ SAFE EXECUTION DEMO")
    print("=" * 50)
    
    automation = create_research_automation("documents")
    
    # Test safe commands
    safe_commands = [
        "echo 'Hello from ResearchAgent automation!'",
        "date",
        "pwd",
        "ls -la | head -5",
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

def demo_research_data_analysis():
    """Demonstrate research data analysis function"""
    print("📊 RESEARCH DATA ANALYSIS DEMO")
    print("=" * 50)
    
    # Import the function we created
    from sgptAgent.llm_functions.common.research_data_analysis import Function as DataAnalysis
    
    # Test different analysis types
    analyses = [
        ("content_summary", "documents", None, "*"),
        ("file_count", "documents", None, "*.txt"),
        ("file_count", "documents", None, "*.md"),
    ]
    
    for analysis_type, target_path, search_term, file_pattern in analyses:
        print(f"\n🔍 Analysis: {analysis_type} on {target_path}")
        print("-" * 40)
        
        try:
            result = DataAnalysis.execute(analysis_type, target_path, search_term, file_pattern)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

def demo_web_research_tools():
    """Demonstrate web research tools"""
    print("🌐 WEB RESEARCH TOOLS DEMO")
    print("=" * 50)
    
    from sgptAgent.llm_functions.common.research_web_tools import Function as WebTools
    
    # Test web research tools
    web_tests = [
        ("website_headers", "https://httpbin.org/headers"),
        ("dns_lookup", "google.com"),
        ("ping_test", "8.8.8.8"),
    ]
    
    for tool_type, target in web_tests:
        print(f"\n🔧 Web Tool: {tool_type} → {target}")
        print("-" * 40)
        
        try:
            result = WebTools.execute(tool_type, target)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

def demo_system_info():
    """Demonstrate system information gathering"""
    print("💻 SYSTEM INFO DEMO")
    print("=" * 50)
    
    from sgptAgent.llm_functions.common.research_system_info import Function as SystemInfo
    
    # Test system info gathering
    info_tests = [
        ("overview", False),
        ("environment", False),
    ]
    
    for info_type, detailed in info_tests:
        print(f"\n📋 System Info: {info_type} (detailed={detailed})")
        print("-" * 40)
        
        try:
            result = SystemInfo.execute(info_type, detailed)
            print(result)
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Run all demonstrations"""
    print("🚀 RESEARCHAGENT AUTOMATION SYSTEM DEMO")
    print("=" * 60)
    print("Testing safe, research-focused system integration")
    print("=" * 60)
    print()
    
    demos = [
        demo_command_validation,
        demo_research_suggestions,
        demo_safe_execution,
        demo_research_data_analysis,
        demo_web_research_tools,
        demo_system_info
    ]
    
    for i, demo in enumerate(demos, 1):
        try:
            print(f"\n{'='*20} DEMO {i}/{len(demos)} {'='*20}")
            demo()
            print(f"{'='*50}")
        except Exception as e:
            print(f"Demo {i} failed: {e}")
            print(f"{'='*50}")
        
        if i < len(demos):
            input("\nPress Enter to continue to next demo...")
    
    print("\n🎉 ALL DEMOS COMPLETED!")
    print("\nThe ResearchAgent now has safe, powerful system integration capabilities!")
    print("Key benefits:")
    print("✅ Multi-tier security validation")
    print("✅ Research-focused command library") 
    print("✅ Comprehensive audit logging")
    print("✅ Intelligent automation suggestions")
    print("✅ Integration with existing shell-gpt functions")

if __name__ == "__main__":
    main()
