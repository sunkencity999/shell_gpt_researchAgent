#!/usr/bin/env python3
"""
Advanced Research Automation Functions Test
Test the new document analysis, data visualization, and workflow automation capabilities.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_test_data():
    """Create sample test data for demonstrations"""
    print("📁 Setting up test data...")
    
    from sgptAgent.research_automation import create_research_automation
    automation = create_research_automation("documents")
    
    # Create test documents
    test_files = {
        "documents/sample_research.txt": """Climate Change Research Report
        
This document examines the impact of climate change on global ecosystems.
Key findings include temperature increases, sea level rise, and biodiversity loss.
The research covers data from 2020 to 2024 across multiple regions.

Temperature data shows consistent warming trends.
Ocean levels have risen by 3.2mm annually.
Species migration patterns have shifted significantly.
""",
        "documents/data_sample.csv": """year,temperature,rainfall
2020,15.2,850
2021,15.8,820
2022,16.1,780
2023,16.5,760
2024,16.9,740""",
        "documents/competitor_analysis.md": """# Competitor Analysis Report

## Company A
- Strong market presence
- Advanced technology stack
- High customer satisfaction

## Company B  
- Emerging player
- Innovative features
- Growing user base

## Market Trends
- Increasing demand for sustainability
- Technology adoption accelerating
- Customer expectations rising
""",
        "documents/numeric_data.txt": """12
25
33
41
28
19
37
42
31
26
18
35
29
44
22
"""
    }
    
    # Create test files
    created_files = []
    for file_path, content in test_files.items():
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            with open(file_path, 'w') as f:
                f.write(content)
            created_files.append(file_path)
            print(f"✅ Created: {file_path}")
        except Exception as e:
            print(f"❌ Error creating {file_path}: {e}")
    
    return created_files

def test_fixed_automation():
    """Test the fixed basic automation system"""
    print("\n🔧 TESTING FIXED AUTOMATION SYSTEM")
    print("=" * 50)
    
    from sgptAgent.research_automation import create_research_automation
    automation = create_research_automation("documents")
    
    # Test commands that should now work
    test_commands = [
        "echo 'Hello from fixed automation!'",
        "pwd",
        "date", 
        "whoami",
        "ls -la | head -3"
    ]
    
    for cmd in test_commands:
        print(f"\n🔧 Testing: {cmd}")
        result = automation.execute_safe_command(cmd)
        
        if result.success:
            print(f"✅ Success: {result.output.strip()}")
        else:
            print(f"❌ Failed: {result.error}")
        print(f"Security Level: {result.security_level.value}")

def test_document_analysis():
    """Test the document analysis function"""
    print("\n📊 TESTING DOCUMENT ANALYSIS")
    print("=" * 50)
    
    try:
        from sgptAgent.llm_functions.common.research_document_analysis import Function as DocAnalysis
        
        # Test different analysis modes
        analyses = [
            ("content_extract", "documents/*.txt", None, "summary"),
            ("word_frequency", "documents/*.txt", None, "summary"),
            ("structure_analysis", "documents/*.md", None, "summary"),
            ("metadata_extract", "documents/*", None, "summary"),
        ]
        
        for analysis_type, target_files, comparison_target, output_format in analyses:
            print(f"\n📋 Testing: {analysis_type}")
            print("-" * 30)
            
            try:
                result = DocAnalysis.execute(analysis_type, target_files, comparison_target, output_format)
                print(result[:500] + "..." if len(result) > 500 else result)
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")

def test_data_visualization():
    """Test the data visualization function"""
    print("\n📈 TESTING DATA VISUALIZATION")
    print("=" * 50)
    
    try:
        from sgptAgent.llm_functions.common.research_data_visualization import Function as DataViz
        
        # Test different chart types
        charts = [
            ("data_summary", "documents/numeric_data.txt", None, None),
            ("distribution", "documents/numeric_data.txt", None, None),
            ("histogram", "documents/numeric_data.txt", None, None),
            ("bar_chart", "documents/sample_research.txt", None, None),
        ]
        
        for chart_type, data_source, column_name, output_file in charts:
            print(f"\n📊 Testing: {chart_type}")
            print("-" * 30)
            
            try:
                result = DataViz.execute(chart_type, data_source, column_name, output_file)
                print(result[:500] + "..." if len(result) > 500 else result)
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")

def test_workflow_automation():
    """Test the workflow automation function"""
    print("\n🔄 TESTING WORKFLOW AUTOMATION")
    print("=" * 50)
    
    try:
        from sgptAgent.llm_functions.common.research_workflow_automation import Function as WorkflowAuto
        
        # Test different workflow types
        workflows = [
            ("data_pipeline", "documents", None),
            ("research_report", "documents", "keyword=climate"),
            ("content_audit", "documents", None),
            ("system_health", "documents", None),
        ]
        
        for workflow_type, target_directory, parameters in workflows:
            print(f"\n⚙️ Testing: {workflow_type}")
            print("-" * 30)
            
            try:
                result = WorkflowAuto.execute(workflow_type, target_directory, parameters)
                print(result[:600] + "..." if len(result) > 600 else result)
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")

def test_research_suggestions():
    """Test enhanced research suggestions with new functions"""
    print("\n💡 TESTING ENHANCED RESEARCH SUGGESTIONS")
    print("=" * 50)
    
    from sgptAgent.research_automation import create_research_automation
    automation = create_research_automation()
    
    enhanced_goals = [
        "analyze document content and extract key insights",
        "create visualizations from my research data",
        "run automated workflow for competitive analysis",
        "perform comprehensive content audit of my files"
    ]
    
    for goal in enhanced_goals:
        print(f"\nResearch Goal: '{goal}'")
        suggestions = automation.get_command_suggestions(goal)
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. [{suggestion['category']}] {suggestion['command']}")
            print(f"     → {suggestion['description']}")
        print()

def main():
    """Run comprehensive test of all advanced research automation features"""
    print("🚀 ADVANCED RESEARCH AUTOMATION TEST SUITE")
    print("=" * 60)
    print("Testing enhanced capabilities with fixes and new functions")
    print("=" * 60)
    
    try:
        # Setup test data
        test_files = setup_test_data()
        print(f"✅ Test data setup complete ({len(test_files)} files created)")
        
        # Run all tests
        tests = [
            ("Fixed Basic Automation", test_fixed_automation),
            ("Document Analysis", test_document_analysis),
            ("Data Visualization", test_data_visualization), 
            ("Workflow Automation", test_workflow_automation),
            ("Enhanced Suggestions", test_research_suggestions),
        ]
        
        for i, (name, test_func) in enumerate(tests, 1):
            try:
                print(f"\n{'='*15} TEST {i}/{len(tests)}: {name} {'='*15}")
                test_func()
                print(f"✅ {name} test completed")
            except Exception as e:
                print(f"❌ {name} test failed: {e}")
                import traceback
                traceback.print_exc()
            
            if i < len(tests):
                print("\nPress Enter to continue to next test...")
                input()
        
        print("\n🎉 COMPREHENSIVE TESTING COMPLETED!")
        print("\n✨ Advanced Research Automation System Status:")
        print("   🔧 Basic fixes: Command classification, subprocess compatibility")
        print("   📊 Document Analysis: Content extraction, word frequency, structure analysis")
        print("   📈 Data Visualization: Histograms, bar charts, distribution analysis")
        print("   🔄 Workflow Automation: Data pipelines, research reports, content audits")
        print("   💡 Enhanced Suggestions: Context-aware automation recommendations")
        print("   🛡️ Security: Multi-tier validation with comprehensive audit logging")
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
