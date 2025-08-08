#!/usr/bin/env python3
"""
Test script to verify API separation
"""

import asyncio
from services.llm_service import LLMService
from query_classifier import CricketQueryClassifier

async def test_llm_service():
    """Test LLM service directly"""
    print("🔧 Testing LLM Service...")
    
    llm_service = LLMService()
    
    # Test model info (no API call)
    model_info = llm_service.get_model_info()
    print(f"Provider Info: {model_info}")
    
    # Test connection first
    print("Testing connection...")
    connection_test = await llm_service.test_connection()
    
    if connection_test["success"]:
        print("✅ LLM Connection working!")
        print(f"Provider: {connection_test['provider']}")
        
        # Test classification prompt
        simple_prompt = """
        Analyze this cricket query: "Who has more runs?"
        
        Return JSON: {"tools_needed": ["database_facts"], "reasoning": "This is a factual query"}
        """
        result = await llm_service.classify_query(simple_prompt)
        
        if result["success"]:
            print("✅ LLM Classification working!")
            print(f"Usage: {result.get('usage', {})}")
            return True
        else:
            print(f"❌ LLM Classification failed: {result['error']}")
            return False
    else:
        print(f"❌ LLM Connection failed: {connection_test['error']}")
        return False

async def test_classifier():
    """Test classifier (uses LLM service internally)"""
    print("\n🎯 Testing Query Classifier...")
    
    classifier = CricketQueryClassifier()
    
    test_query = "Who has more runs Kohli or Rohit?"
    result = await classifier.classify_and_route(test_query)
    
    if "error" not in result or not result.get("error"):
        print("✅ Classifier working!")
        print(f"Tools needed: {result['tools_needed']}")
        print(f"LLM Usage: {result.get('llm_usage', {})}")
        return True
    else:
        print(f"❌ Classifier failed: {result.get('error', 'Unknown error')}")
        return False

async def main():
    """Main test function"""
    print("🏏 Testing API Separation Architecture\n")
    
    # Test 1: LLM Service
    llm_success = await test_llm_service()
    
    # Test 2: Classifier
    classifier_success = await test_classifier()
    
    print(f"\n📊 Results:")
    print(f"LLM Service: {'✅ Pass' if llm_success else '❌ Fail'}")
    print(f"Classifier: {'✅ Pass' if classifier_success else '❌ Fail'}")
    
    if llm_success and classifier_success:
        print("\n🎉 All tests passed! API separation working correctly.")
        print("\n📋 Architecture:")
        print("  main.py → query_classifier.py → services/llm_service.py → OpenAI API")
        print("  ✅ Clean separation achieved!")
    else:
        print("\n⚠️  Some tests failed. Check your API key and model access.")

if __name__ == "__main__":
    asyncio.run(main())