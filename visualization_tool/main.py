from fastapi import FastAPI, HTTPException, Response
import httpx
from pydantic import BaseModel, Field
import json
import os
import datetime
import logging
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Optional

from config import DATABASE_AGENT_URL
from services.llm_service import LLMService

# --- Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
llm_service = LLMService()

# --- Pydantic Models ---
class APIRequest(BaseModel):
    query: str

class VisualizationPlan(BaseModel):
    chart_type: str = Field(..., description="Type of chart, e.g., 'bar', 'line'.")
    x_axis: str = Field(..., description="The column for the x-axis.")
    y_axis: List[str] = Field(..., description="A list of one or more columns for the y-axis.")
    title: str = Field(..., description="A descriptive title for the chart.")
    legend_by: Optional[str] = Field(None, description="Column to use for differentiating series (e.g., 'player_name').")

# --- Core Logic Functions ---

async def add_quotes_to_player_names(query: str) -> str:
    """
    Uses an LLM to identify player names in a query and ensure they are enclosed in double quotes.
    """
    system_prompt = """
    You are a query refining assistant for a cricket database. Your task is to analyze a query and ensure that any identified cricket player names are enclosed in exactly one pair of double quotes.
    - If a player name is found and is not quoted, add double quotes around it (e.g., rohit sharma -> "Rohit Sharma").
    - If a player name is already correctly quoted, leave it as is. DO NOT add another pair of quotes.
    - Do not change any other part of the query.
    - Return ONLY the modified query string, without any additional text, explanations, or markdown.

    Example 1 (needs quoting):
    User Query: "compare virat kohli and rohit sharma's career stats in ipl"
    Your Output: "compare \"Virat Kohli\" and \"Rohit Sharma\"'s career stats in ipl"

    Example 2 (already quoted):
    User Query: "show stats for \"Virat Kohli\" in tests"
    Your Output: "show stats for \"Virat Kohli\" in tests"
    
    Example 3 (mixed):
    User Query: "compare \"Virat Kohli\" and rohit sharma"
    Your Output: "compare \"Virat Kohli\" and \"Rohit Sharma\""
    """
    classification_prompt = f"User Query: \"{query}\"\n\nYour Output:"
    
    response = await llm_service.classify_query(
        classification_prompt=classification_prompt,
        system_prompt=system_prompt
    )

    # If the call succeeds with JSON data (less likely for this prompt)
    if response.get("success") and isinstance(response.get("data"), str):
        return response["data"].strip().replace('`', '').strip('"')

    # If JSON parsing failed (likely), the raw string is in 'raw_content'
    if not response.get("success") and response.get("raw_content"):
        content = response["raw_content"]
        return content.strip().replace('`', '').strip('"')

    # Fallback to original query if LLM fails unexpectedly
    logger.warning("LLM call to add quotes failed to produce usable content. Falling back to the original query.")
    return query


async def get_visualization_plan(query: str, data_sample: List[Dict[str, Any]]) -> VisualizationPlan:
    """
    Uses an LLM to create a visualization plan based on the user query and the retrieved data.
    """
    if not data_sample:
        raise ValueError("Cannot generate visualization plan from empty data.")

    columns = list(data_sample[0].keys())
    
    system_prompt = """
    You are a data visualization expert. Based on a user's query and a sample of the data, create a JSON plan to visualize that data.
    - For trends over time ("yearly", "season-wise"), use a 'line' chart.
    - For comparing entities (players, teams), a 'bar' chart is best.
    - The y_axis must be a list of numeric columns.
    - If multiple entities are tracked in a line chart (e.g., two players' runs over years), specify `legend_by`, which is usually 'player_name'.

    Respond ONLY with a valid JSON object matching the schema:
    {"chart_type": "bar|line", "x_axis": "<col>", "y_axis": ["<col>"], "title": "<title>", "legend_by": "<col_or_null>"}
    """
    classification_prompt = f"""
    User's query: "{query}"
    Data columns: {columns}
    Data sample: {json.dumps(data_sample[:3])}

    Generate the JSON visualization plan.
    """
    
    response = await llm_service.classify_query(
        classification_prompt=classification_prompt, system_prompt=system_prompt
    )

    if response.get("success"):
        try:
            plan_data = response.get("data", {})
            if isinstance(plan_data, str): plan_data = json.loads(plan_data)
            return VisualizationPlan(**plan_data)
        except Exception as e:
            raise ValueError(f"Could not create a valid visualization plan from LLM response: {e}")
    else:
        raise Exception("LLM service failed to generate a visualization plan.")


def generate_and_save_plot(data: List[Dict[str, Any]], plan: VisualizationPlan, query: str) -> str:
    """
    Generates and saves a plot based on the data and visualization plan.
    """
    try:
        df = pd.DataFrame(data)
        fig, ax = plt.subplots(figsize=(12, 7))

        if plan.chart_type == 'bar':
            df.plot(kind='bar', x=plan.x_axis, y=plan.y_axis, ax=ax, width=0.8)
        elif plan.chart_type == 'line':
            if plan.legend_by and plan.legend_by in df.columns:
                for label, group_df in df.groupby(plan.legend_by):
                    group_df.plot(kind='line', x=plan.x_axis, y=plan.y_axis[0], ax=ax, label=label, marker='o')
                ax.legend(title=plan.legend_by.replace('_', ' ').title())
            else:
                df.plot(kind='line', x=plan.x_axis, y=plan.y_axis, ax=ax, marker='o')
        
        ax.set_title(plan.title, fontsize=16)
        ax.set_xlabel(plan.x_axis.replace('_', ' ').title(), fontsize=12)
        ax.set_ylabel(plan.y_axis[0].replace('_', ' ').title(), fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.6)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_dir = "generated_graphs"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
        filename = f"{safe_query}_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        plt.savefig(filepath)
        plt.close(fig)
        logger.info(f"Plot saved to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error generating plot: {e}", exc_info=True)
        return None


def transform_db_result(db_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transforms the database agent's result format (columns and rows) into a list of dictionaries.
    """
    if not db_result or "columns" not in db_result or "rows" not in db_result:
        return []
    
    columns = db_result["columns"]
    rows = db_result["rows"]
    
    # Coerce numeric types for plotting
    df = pd.DataFrame(rows, columns=columns)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')
        
    return df.to_dict('records')


# --- API Endpoint ---
@app.post("/visualize", response_class=Response)
async def visualize(request: APIRequest):
    """
    Orchestrates the visualization process.
    """
    logger.info(f"Received query: '{request.query}'")
    try:
        # 1. Prepare query for DB agent (add quotes to names)
        prepared_query = await add_quotes_to_player_names(request.query)
        logger.info(f"Prepared query for DB agent: '{prepared_query}'")

        # 2. Get data from the database agent
        async with httpx.AsyncClient() as client:
            response = await client.post(DATABASE_AGENT_URL, json={"query": prepared_query}, timeout=60.0)
            response.raise_for_status()
            db_response = response.json()
        
        if isinstance(db_response, str): db_response = json.loads(db_response)
        
        db_result = db_response.get("result")
        if not db_result:
            error_detail = f"Database agent returned no 'result' block. Full response: {json.dumps(db_response)}"
            raise HTTPException(status_code=422, detail=error_detail)

        # 3. Transform the data into a list of dictionaries
        data_to_plot = transform_db_result(db_result)
        if not data_to_plot:
            raise HTTPException(status_code=404, detail="Data from database agent was empty or in an invalid format.")
        
        logger.info(f"Received and transformed {len(data_to_plot)} records from DB agent.")

        # 4. Get a visualization plan
        plan = await get_visualization_plan(request.query, data_to_plot)
        logger.info(f"Generated visualization plan: {plan.dict()}")

        # 5. Generate and save the plot
        plot_path = generate_and_save_plot(data_to_plot, plan, request.query)
        if not plot_path:
            raise HTTPException(status_code=500, detail="Failed to generate plot image.")

        # 6. Return the image
        with open(plot_path, "rb") as f:
            return Response(content=f.read(), media_type="image/png")

    except httpx.HTTPStatusError as e:
        logger.error(f"Error from database agent: {e.response.text}", exc_info=True)
        raise HTTPException(status_code=e.response.status_code, detail=f"Error from DB agent: {e.response.text}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Visualization Agent is running."}