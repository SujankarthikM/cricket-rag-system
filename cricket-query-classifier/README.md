# 🏏 Cricket Query Classifier

A smart query classification system that analyzes cricket queries and determines which tools should handle them, along with specific instructions for each tool.

## 🎯 What This Does

For any cricket query, this system:
1. **Classifies** the type of query (factual, opinion, live, historical, visual)
2. **Selects** appropriate tools to handle it
3. **Generates** specific instructions for each tool

## 🛠️ Available Tools

- **Opinion RAG Tool**: For subjective analysis, comparisons, "why" questions
- **Database Facts Tool**: For direct factual data like runs, averages, records
- **Live Data Tool**: For current/ongoing matches, live scores
- **Historical Match Tool**: For specific past matches, tournaments
- **Visualization Tool**: For charts, graphs, trends

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Environment
```bash
cp .env.example .env
# Add your OpenAI API key to .env
```

### 3. Run the API
```bash
python main.py
```

### 4. Try the Demo
Visit: http://localhost:8000/demo

## 📖 API Endpoints

### Single Query Classification
```bash
curl -X POST "http://localhost:8000/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "Who has more runs Kohli or Rohit?"}'
```

### Batch Classification
```bash
curl -X POST "http://localhost:8000/classify-batch" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["Who is better Kohli or Rohit?", "What is the current score?"]}'
```

### Demo All Examples
```bash
curl "http://localhost:8000/demo"
```

## 📊 Example Classifications

### Factual Query
**Input**: "Who has more runs Kohli or Rohit?"
**Output**:
```json
{
  "tools_needed": ["database_facts"],
  "tool_instructions": {
    "database_facts": {
      "sql_requirement": "Compare total runs between Kohli and Rohit",
      "specific_fields": ["player_name", "total_runs", "matches", "average"],
      "filters": "active players, all formats"
    }
  }
}
```

### Opinion Query  
**Input**: "Why is Kohli better than Rohit?"
**Output**:
```json
{
  "tools_needed": ["opinion_rag"],
  "tool_instructions": {
    "opinion_rag": {
      "rag_queries": [
        "Kohli batting technique analysis",
        "Kohli vs Rohit performance comparison",
        "Kohli consistency in pressure situations",
        "Kohli career achievements",
        "Kohli adaptability across formats"
      ]
    }
  }
}
```

### Visualization Query
**Input**: "Show me Kohli's run trend over years"
**Output**:
```json
{
  "tools_needed": ["database_facts", "visualization"],
  "tool_instructions": {
    "database_facts": {
      "sql_requirement": "Get Kohli's yearly run totals",
      "specific_fields": ["year", "runs", "matches", "average"]
    },
    "visualization": {
      "chart_type": "line",
      "x_axis": "year", 
      "y_axis": "runs",
      "comparison_type": "performance over time"
    }
  }
}
```

## 🔧 Features

- **Smart Classification**: Uses LLM to understand query intent
- **Specific Instructions**: Generates detailed instructions for each tool
- **Multiple Tools**: Can select multiple tools for complex queries
- **Batch Processing**: Handle multiple queries simultaneously
- **Interactive Docs**: Swagger UI at `/docs`
- **Demo Mode**: Test with example queries

## 📈 Use Cases

This classifier helps determine:
- **When to use RAG** (opinion/analysis questions)
- **When to query database** (factual data)
- **When to fetch live data** (current matches)
- **When to create visualizations** (trend analysis)
- **How to combine tools** (complex queries)

Perfect foundation for building an intelligent cricket chatbot! 🎯