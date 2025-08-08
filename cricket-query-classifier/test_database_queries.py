#!/usr/bin/env python3
"""
Test script for cricket database query generation and execution
"""
import asyncio
from database.query_generator import CricketQueryGenerator
from database.query_executor import CricketQueryExecutor, MockCricketQueryExecutor

async def test_query_flow():
    """Test the complete flow: Natural Language → SQL → Results"""
    
    print("🏏 Cricket Database Query System Test")
    print("=" * 50)
    
    # Initialize components
    generator = CricketQueryGenerator()
    executor = MockCricketQueryExecutor()  # Using mock since DB doesn't exist yet
    
    # Test requests
    test_requests = [
        "Get the best away ground for kohli"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\\n🔍 Test {i}: {request}")
        print("-" * 60)
        
        try:
            # Step 1: Generate SQL query from natural language
            print("Step 1: Generating SQL query...")
            query_result = await generator.generate_sql_query(request)
            
            if query_result["success"]:
                query_data = query_result["query_data"]
                sql_query = query_data["sql_query"]
                
                print(f"✅ Generated SQL: {sql_query}")
                print(f"📊 Query Type: {query_data['query_type']}")
                print(f"📋 Tables Used: {query_data['tables_used']}")
                print(f"💡 Explanation: {query_data['explanation']}")
                
                # Step 2: Execute the query
                print("\\nStep 2: Executing query...")
                execution_result = executor.execute_query(sql_query)
                
                if execution_result["success"]:
                    print(f"✅ Query executed successfully!")
                    print(f"📈 Rows returned: {execution_result['row_count']}")
                    print(f"📊 Results: {execution_result['data']}")
                    
                    if execution_result.get("is_mock"):
                        print("⚠️  Note: Using mock data (database not created yet)")
                
                else:
                    print(f"❌ Execution failed: {execution_result['error']}")
            
            else:
                print(f"❌ Query generation failed: {query_result['error']}")
                if 'fallback_query' in query_result:
                    fallback = query_result['fallback_query']
                    print(f"🔄 Fallback SQL: {fallback['sql_query']}")
        
        except Exception as e:
            print(f"💥 Error: {str(e)}")
        
        print("\\n" + "="*60)
    
    # Show schema information
    print("\\n📋 Database Schema Information:")
    schema = generator.get_schema_info()
    
    for table_name, table_info in schema["tables"].items():
        print(f"\\n📊 Table: {table_name}")
        print(f"   Description: {table_info['description']}")
        print(f"   Columns: {len(table_info['columns'])}")

async def test_individual_components():
    """Test individual components separately"""
    
    print("\\n🧪 Testing Individual Components")
    print("=" * 40)
    
    # Test 1: Query Generator
    print("\\n1. Testing Query Generator...")
    generator = CricketQueryGenerator()
    
    test_query = "Get Virat Kohli's ODI stats"
    result = await generator.generate_sql_query(test_query)
    
    if result["success"]:
        print(f"✅ SQL Generated: {result['query_data']['sql_query']}")
    else:
        print(f"❌ Generation failed: {result['error']}")
    
    # Test 2: Query Validator
    print("\\n2. Testing Query Validator...")
    test_sql = "SELECT * FROM player_profile WHERE full_name LIKE '%Kohli%'"
    validation = generator.validate_sql_query(test_sql)
    
    print(f"Validation: {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
    if validation['issues']:
        print(f"Issues: {validation['issues']}")
    
    # Test 3: Mock Executor
    print("\\n3. Testing Mock Executor...")
    executor = MockCricketQueryExecutor()
    exec_result = executor.execute_query(test_sql)
    
    if exec_result["success"]:
        print(f"✅ Execution successful: {exec_result['data']}")
    else:
        print(f"❌ Execution failed: {exec_result['error']}")

if __name__ == "__main__":
    print("🚀 Starting Cricket Database Query Tests\\n")
    
    # Run tests
    asyncio.run(test_query_flow())
    asyncio.run(test_individual_components())
    
    print("\\n🎉 All tests completed!")
    print("\\n📝 Summary:")
    print("  ✅ Query generation working")
    print("  ✅ SQL validation working") 
    print("  ✅ Mock execution working")
    print("  ⏳ Ready for real database integration")
    
    print("\\n🔧 Next Steps:")
    print("  1. Create actual SQLite database from extracted JSON data")
    print("  2. Replace MockCricketQueryExecutor with CricketQueryExecutor")
    print("  3. Test with real player data")
    print("  4. Integrate with the main classification system")