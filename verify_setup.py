#!/usr/bin/env python3
"""
Setup Verification Script for Shell GPT Research Agent
Tests all enhanced features and dependencies to ensure smooth operation.
"""

import sys
import os
import traceback
from typing import Dict, List, Tuple

def test_basic_imports() -> Tuple[bool, str]:
    """Test basic Python imports."""
    try:
        import requests
        import dotenv
        import typer
        import bs4  # beautifulsoup4 imports as bs4
        import newspaper
        import playwright
        import PyQt5
        return True, "✅ Basic imports successful"
    except ImportError as e:
        return False, f"❌ Basic import failed: {e}"

def test_nlp_dependencies() -> Tuple[bool, str]:
    """Test NLP dependencies and models."""
    results = []
    
    # Test spaCy
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            doc = nlp("Apple Inc. is a technology company founded in 1976.")
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            if entities:
                results.append("✅ spaCy with en_core_web_sm model working")
            else:
                results.append("⚠️ spaCy model loaded but no entities detected")
        except OSError:
            results.append("❌ spaCy en_core_web_sm model not found")
    except ImportError:
        results.append("❌ spaCy not installed")
    
    # Test NLTK
    try:
        import nltk
        from nltk.corpus import wordnet
        try:
            # Test wordnet access
            synsets = wordnet.synsets('good')
            if synsets:
                results.append("✅ NLTK WordNet data available")
            else:
                results.append("⚠️ NLTK WordNet data not accessible")
        except Exception:
            results.append("❌ NLTK WordNet data not downloaded")
    except ImportError:
        results.append("❌ NLTK not installed")
    
    # Test scikit-learn
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        results.append("✅ scikit-learn available")
    except ImportError:
        results.append("❌ scikit-learn not installed")
    
    # Test fuzzywuzzy
    try:
        from fuzzywuzzy import fuzz
        score = fuzz.ratio("test", "test")
        results.append("✅ fuzzywuzzy available")
    except ImportError:
        results.append("❌ fuzzywuzzy not installed")
    
    success = all("✅" in result for result in results)
    return success, "\n".join(results)

def test_query_enhancement() -> Tuple[bool, str]:
    """Test the enhanced query construction system."""
    try:
        sys.path.append(os.path.dirname(__file__))
        from sgptAgent.query_enhancement import enhance_search_query
        
        # Test query enhancement
        result = enhance_search_query(
            "iPhone vs Android performance", 
            research_goal="which smartphone is better",
            context_steps=["battery life", "camera quality", "price comparison"]
        )
        
        checks = []
        
        # Check return structure
        required_keys = ['original_query', 'enhanced_queries', 'entities', 'domain', 'fallback_queries']
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            checks.append(f"❌ Missing keys: {missing_keys}")
        else:
            checks.append("✅ Query enhancement returns correct structure")
        
        # Check domain detection
        detected_domain = result.get('domain', 'unknown')
        if detected_domain in ['technology', 'sports', 'business', 'science', 'health', 'politics', 'finance', 'education', 'general']:
            checks.append(f"✅ Domain detection working (detected: {detected_domain})")
        else:
            checks.append(f"⚠️ Domain detection: {detected_domain}")
        
        # Check enhanced queries
        enhanced_queries = result.get('enhanced_queries', [])
        if len(enhanced_queries) >= 3:
            checks.append(f"✅ Generated {len(enhanced_queries)} enhanced queries")
        else:
            checks.append(f"⚠️ Only {len(enhanced_queries)} enhanced queries generated")
        
        # Check fallback queries
        fallback_queries = result.get('fallback_queries', [])
        if len(fallback_queries) >= 2:
            checks.append(f"✅ Generated {len(fallback_queries)} fallback queries")
        else:
            checks.append(f"⚠️ Only {len(fallback_queries)} fallback queries generated")
        
        # Check entity extraction
        entities = result.get('entities', {})
        if entities and any(entities.values()):
            checks.append("✅ Entity extraction working")
        else:
            checks.append("⚠️ No entities extracted")
        
        success = all("✅" in check for check in checks)
        return success, "\n".join(checks)
        
    except Exception as e:
        return False, f"❌ Query enhancement test failed: {e}\n{traceback.format_exc()}"

def test_research_agent() -> Tuple[bool, str]:
    """Test ResearchAgent initialization."""
    try:
        sys.path.append(os.path.dirname(__file__))
        from sgptAgent.agent import ResearchAgent
        
        # Set dummy API key for testing
        os.environ['OPENAI_API_KEY'] = 'test-key'
        
        # Test agent initialization
        agent = ResearchAgent()
        
        return True, "✅ ResearchAgent initializes successfully"
        
    except Exception as e:
        return False, f"❌ ResearchAgent initialization failed: {e}\n{traceback.format_exc()}"

def main():
    """Run all verification tests."""
    print("🔍 Shell GPT Research Agent - Setup Verification")
    print("=" * 60)
    
    tests = [
        ("Basic Dependencies", test_basic_imports),
        ("NLP Dependencies", test_nlp_dependencies),
        ("Query Enhancement", test_query_enhancement),
        ("ResearchAgent", test_research_agent),
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        print("-" * 40)
        
        try:
            success, message = test_func()
            print(message)
            
            if not success:
                all_passed = False
                
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Your ResearchAgent is ready to use.")
        print("\nEnhanced features available:")
        print("  • Advanced entity recognition with spaCy")
        print("  • Query expansion with NLTK WordNet")
        print("  • Relevance scoring with TF-IDF")
        print("  • Domain-specific query enhancement")
        print("  • Progressive fallback strategies")
        print("  • Fuzzy text matching")
    else:
        print("⚠️  SOME TESTS FAILED. Check the output above for details.")
        print("The application may still work with reduced capabilities.")
    
    print("\nTo run the ResearchAgent:")
    print("  python sgptAgent/gui_app.py")

if __name__ == "__main__":
    main()
