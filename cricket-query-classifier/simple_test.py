#!/usr/bin/env python3
"""
Simple test to show classification output
"""
import asyncio
from query_classifier import CricketQueryClassifier

async def test_classification():
    """Test the classification for your wagon wheel query"""
    
    classifier = CricketQueryClassifier()
    
    # Your specific query
    test_query = "A wagon wheel for rohit from year 2023 to 2025"
    
    print(f"🏏 Testing Query: {test_query}")
    print("=" * 60)
    
    try:
        # Get the classification result
        result = await classifier.classify_and_route(test_query)
        
        if result.get("classification_success", False):
            print("✅ Classification successful!")
            print(f"Tools needed: {result['tools_needed']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"Query type: {result.get('query_type', 'unknown')}")
            print(f"Confidence: {result.get('confidence', 'unknown')}")
            
            print("\n📋 Tool Instructions:")
            for tool, instructions in result.get('tool_instructions', {}).items():
                print(f"\n{tool.upper()}:")
                for key, value in instructions.items():
                    print(f"  {key}: {value}")
                    
            print(f"\n🔧 LLM Usage: {result.get('llm_usage', {})}")
            
        else:
            print("❌ Classification failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if 'raw_content' in result:
                print(f"Raw response: {result['raw_content'][:200]}...")
        
    except Exception as e:
        print(f"💥 Exception: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_classification())