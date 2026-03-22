from src.state.state import EditExtraction, InteractionState
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.save_to_db import Interaction
from datetime import datetime, timedelta

load_dotenv()

engine = create_engine("mysql+pymysql://root:toor@localhost/aivoa")
SessionLocal = sessionmaker(bind=engine)

def edit_interaction(state: InteractionState, config):
    """
    Updates an existing interaction record based on user input.
    
    Steps:
    1. Extracts LLM and cache from config.
    2. Retrieves last_id from interaction_data; if missing, returns error message.
    3. Creates structured LLM output for EditExtraction schema.
    4. Invokes LLM with prompt to identify field_need_change and new_data from user input.
    5. Extracts field and value from LLM result; if invalid, returns error message.
    6. Prepares updated_fields dictionary with the change.
    7. Handles special cases: converts materials to JSON list, formats time to HH:MM.
    8. Updates the Interaction record in database with updated_fields.
    9. Commits database changes and closes session.
    10. Merges updated fields into interaction_data.
    11. Updates cache with new interaction data.
    12. If hcp_name changed, updates followUps by replacing old name with new name.
    13. Returns updated interaction_data, followUps, and success message.
    """
    
    print("inside edit_interaction")

    llm = config["configurable"]["llm"]
    cache = config["configurable"]["cache"]
    
    # safe access
    last_id = state["interaction_data"]["last_id"]
    print(last_id)
    if not last_id:
        return {
            "messages": state.get("messages", []) + [
                {"role": "ai", "text": "No interaction found to update."}
            ]
        }
    
    structured_llm = llm.with_structured_output(EditExtraction)

    prompt = f"""
    You are given an existing interaction record.

    Fields*:
    hcp_name, date, time, topics, materials, sentiment, interaction_type

    Your task:
    - Identify which fields user wants to update Choose from Fields* only
    - Identify what new value he/she want to put for any of hcp_name, date, time, topics, materials, sentiment, interaction_type
    - Extract ONLY those fields
    - DO NOT include unchanged fields
    - DO NOT guess missing values

    User input:
    {state["input"]}
    """
    
    result = structured_llm.invoke(prompt)
    print(result)

    data = result.model_dump(exclude_none=True)

    field = data.get("field_need_change")
    value = data.get("new_data")

    if not field or not value:
       return {
            "messages": state.get("messages", []) + [
                {"role": "ai", "text": "No valid changes detected."}
            ]
        }

    updated_fields = {field: value}
    
    # handle materials separately
    if field == "materials":
        import json
        updated_fields[field] = json.dumps([value])

    if field == "time":
        dt = datetime.strptime(updated_fields[field], "%H:%M")
        updated_fields["time"] = dt.strftime("%H:%M")

    db = SessionLocal()

    rows = db.query(Interaction).filter(
        Interaction.id == last_id
    ).update(updated_fields)

    db.commit()
    db.close()

    print("Rows updated:", rows)

    updated_data = {
        **state.get("interaction_data", {}),
        **updated_fields
    }

    # Update cache with the new data
    cache.put(last_id, updated_data)

    # If the field changed is hcp_name, update followUps to reflect the change
    updated_followUps = state.get("followUps", [])
    if field == "hcp_name":
        old_name = state["interaction_data"].get("hcp_name", "")
        new_name = value
        updated_followUps = [item.replace(old_name, new_name) for item in updated_followUps]

    return {
        "interaction_data": updated_data,
        "followUps": updated_followUps,
        "messages": state.get("messages", []) + [
            {"role": "ai", "text": "Interaction updated successfully"}
        ]
    }