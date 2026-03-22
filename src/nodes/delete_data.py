from src.state.state import InteractionState, QueryExtraction
from src.utils.save_to_db import delete_by_filters
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

def delete_data_node(state: InteractionState, config):
    """
    Processes user input to extract filters and delete matching data from the database.
    
    Steps:
    1. Extracts LLM from config.
    2. Creates structured LLM output for QueryExtraction schema.
    3. Invokes LLM to extract filters from user input.
    4. If filters are found, attempts to delete matching interactions.
    5. Returns success or failure message.
    """
    
    llm = config["configurable"]["llm"]

    structured_llm = llm.with_structured_output(QueryExtraction)

    prompt = f"""
    Extract query filters from user input for deletion.

    Available fields: hcp_name, date, sentiment, interaction_type, materials

    Rules:
    - Only set fields that are explicitly mentioned
    - Set other fields to null
    - Do NOT guess
    - Convert natural language:
        "today" → actual date
        "yesterday" → actual date
    - Return JSON with all fields, null for unspecified

    Examples:
    Input: delete all negative sentiment doctors
    Output: {{"hcp_name": null, "date": null, "sentiment": "negative", "interaction_type": null, "materials": null}}

    Input: delete meetings with Dr Sharma
    Output: {{"hcp_name": "Dr Sharma", "date": null, "sentiment": null, "interaction_type": "Meeting", "materials": null}}

    User input:
    {state["input"]}
    """
    
    result = structured_llm.invoke(prompt)
    
    filters = result.model_dump(exclude_none=True)
    
    print("Delete Filters:", filters)
    
    if not filters:
        return {
            "messages": state.get("messages", []) + [{"role": "ai", "text": "Please specify what data you want to delete (e.g., by sentiment, name, date, etc.)."}],
            "status": "failed"
        }
    
    # normalize date
    if "date" in filters:
        if filters["date"].lower() == "today":
            filters["date"] = datetime.today().strftime("%Y-%m-%d")
        elif filters["date"].lower() == "yesterday":
            filters["date"] = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    count = delete_by_filters(filters)

    if count > 0:
        message = f"Deleted {count} interaction(s) matching the criteria."
    else:
        message = "No data found matching the specified criteria."
    
    return {
        "messages": state.get("messages", []) + [{"role": "ai", "text": message}],
        "status": "complete"
    }