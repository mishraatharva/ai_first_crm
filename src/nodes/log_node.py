from src.state.state import InteractionData, InteractionState
from src.utils.save_to_db import save_to_db
from dotenv import load_dotenv
from datetime import datetime, timedelta
load_dotenv()

def log_node(state: InteractionState, config):
    """
    Processes user input to extract and validate interaction data for CRM logging.
    
    Steps:
    1. Extracts LLM and cache from config.
    2. Creates structured LLM output for InteractionData schema.
    3. Invokes LLM with strict extraction prompt to get: hcp_name, date, time, topics, materials, sentiment, interaction_type.
    4. Retrieves extracted data as dictionary.
    5. Merges new data with existing interaction_data, preserving previous values and updating only non-null fields.
    6. Validates completeness by checking required fields; if any missing, returns incomplete status with question for missing data.
    7. Normalizes date values ('today'/'yesterday' to actual dates) and time to HH:MM format.
    8. Saves complete data to database and retrieves last_id.
    9. Caches interaction if sentiment is positive or neutral.
    10. Returns complete status with updated data, last_id, and success message.
    """
    
    llm = config["configurable"]["llm"]
    cache = config["configurable"]["cache"]

    structured_llm = llm.with_structured_output(InteractionData)

    # extraction = structured_llm.invoke(state["input"])
    extraction = structured_llm.invoke(f"""
      You are an information extraction system.

      STRICT RULES (must follow):
      - Extract ONLY explicitly mentioned values from the text
      - If a field is not present → return null
      - NEVER infer date or time
      - NEVER assume missing fields
      - NEVER generate defaults
      - If field is missing or null generate question to ask to user
     If date is not explicitly written → date = null  
     If time is not explicitly written → time = null  

     Fields:
     hcp_name, date, time, topics, materials, sentiment, interaction_type

     Allowed interaction_type:
     - on call
     - meeting
     - on mail

    Text:
    {state["input"]}
    """)

    # new_data = extraction.dict(exclude_none=True)
    new_data = extraction.dict()

    # get existing data safely
    current_data = state.get("interaction_data", {})
    
    # merge - FIX: Preserve existing data, only update non-null values
    updated = current_data.copy()
    for key, value in new_data.items():
        if value is not None:
            updated[key] = value
    
    required = ["hcp_name", "date", "time", "topics", "sentiment", "materials", "interaction_type"]
    missing = [f for f in required if not updated.get(f)]
    
    if missing:
        question = f"Please provide: {', '.join(missing)}"
        return {
            "interaction_data": updated,
            "status": "incomplete",
            "missing_data_question": question,
            "messages": state.get("messages", []) + [{"role": "ai", "text": question}]
        }
    
    # Handle date/time normalization
    if updated.get("date") == "today": 
        updated["date"] = datetime.today().strftime("%Y-%m-%d")
    elif updated.get("date") == "yesterday":
        updated["date"] = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if updated.get("time"):
        try:
            dt = datetime.strptime(new_data["time"], "%H:%M")
            updated["time"] = dt.strftime("%H:%M")
        except ValueError:
            updated["time"] = None
    
    # Complete → save (FIX: Don't overwrite with new_data again)
    last_id = save_to_db(updated)
    updated["last_id"] = last_id  # Just add last_id, don't re-merge
    
    if updated.get("sentiment") in ["positive", "neutral"]:
        cache.put(last_id, updated)
    
    return {
        "interaction_data": updated,
        "status": "complete",
        "messages": state.get("messages", []) + [{"role": "ai", "text": "Interaction saved successfully"}]
    }