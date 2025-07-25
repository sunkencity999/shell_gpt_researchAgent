#!/usr/bin/env python3
"""
Test the enhanced automation system with user approval workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sgptAgent'))

from research_automation import ResearchAutomation, execute_research_command_with_approval

def mock_approval_callback(command, security_level, reason):
    """Mock approval callback that simulates user approval"""
    print(f"\n🔒 APPROVAL REQUEST:")
    print(f"   Command: {command}")
    print(f"   Security Level: {security_level}")
    print(f"   Reason: {reason}")
    
    # For testing, approve bash and other advanced commands
    if 'bash' in command.lower() or security_level == 'advanced':
        print(f"   ✅ APPROVED (auto-approved for testing)")
        return True
    elif security_level == 'moderate':
        print(f"   ✅ APPROVED (moderate command approved)")
        return True
    else:
        print(f"   ❌ REJECTED")
        return False

def test_approval_workflow():
    """Test the approval workflow for restricted commands"""
    print("🧪 TESTING ENHANCED AUTOMATION WITH APPROVAL WORKFLOW")
    print("=" * 60)
    
    # Create automation instance with approval callback
    automation = ResearchAutomation("documents", approval_callback=mock_approval_callback)
    
    print("\n📋 Test 1: Safe command (should work without approval)")
    result = automation.execute_safe_command("ls documents/", auto_approve=True)
    print(f"   Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"   Output: {result.output[:100]}..." if result.output else f"   Error: {result.error}")
    
    print("\n📋 Test 2: Bash command (should request approval)")
    bash_command = 'bash -c "echo \'Testing bash approval\'"'
    result = automation.execute_safe_command(bash_command, auto_approve=True)
    print(f"   Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"   Output: {result.output}" if result.output else f"   Error: {result.error}")
    
    print("\n📋 Test 3: Complex bash analysis (should request approval)")
    complex_bash = 'bash -c "find documents -name \\\"*.txt\\\" | head -5 | xargs wc -l"'
    result = automation.execute_safe_command(complex_bash, auto_approve=True)
    print(f"   Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"   Output: {result.output}" if result.output else f"   Error: {result.error}")
    
    print("\n📋 Test 4: Using convenience function")
    result = execute_research_command_with_approval(
        command="echo 'Testing convenience function'",
        research_dir="documents",
        approval_callback=mock_approval_callback,
        auto_approve=True
    )
    print(f"   Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"   Output: {result.output}" if result.output else f"   Error: {result.error}")
    
    print("\n📊 Session Summary:")
    summary = automation.get_session_summary()
    print(f"   Commands executed: {summary['total_commands']}")
    print(f"   Successful: {summary['successful_commands']}")
    print(f"   Session ID: {summary['session_id']}")
    
    print("\n🎉 APPROVAL WORKFLOW TEST COMPLETE!")

if __name__ == "__main__":
    test_approval_workflow()
