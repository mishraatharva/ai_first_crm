from src.state.state import QueryExtraction, InteractionState
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.save_to_db import Interaction
load_dotenv()

engine = create_engine("mysql+pymysql://root:toor@localhost/aivoa")
SessionLocal = sessionmaker(bind=engine)

def query_node(state: InteractionState, config):

    llm = config["configurable"]["llm"]

    structured_llm = llm.with_structured_output(QueryExtraction)

    prompt = f"""
    Extract query filters from user input.

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
    Input: show all negative sentiment doctors
    Output: {{"hcp_name": null, "date": null, "sentiment": "negative", "interaction_type": null, "materials": null}}

    Input: show meetings with Dr Sharma
    Output: {{"hcp_name": "Dr Sharma", "date": null, "sentiment": null, "interaction_type": "Meeting", "materials": null}}

    User input:
    {state["input"]}
    """
    
    result = structured_llm.invoke(prompt)
    
    filters = result.model_dump(exclude_none=True)
    
    print("Filters:", filters)
    
    if not filters:
        return {
            "messages": state.get("messages", []) + [
                {"role": "ai", "text": "Please specify what you want to query."}
            ]
        }
    
    # normalize date
    from datetime import datetime, timedelta
    
    if "date" in filters:
        if filters["date"].lower() == "today":
            filters["date"] = datetime.today().strftime("%Y-%m-%d")
        elif filters["date"].lower() == "yesterday":
            filters["date"] = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    db = SessionLocal()
    query = db.query(Interaction)
    
    # APPLY FILTERS DYNAMICALLY
    for key, value in filters.items():
    
        if key == "hcp_name":
            query = query.filter(Interaction.hcp_name.ilike(f"%{value}%"))
        
        elif key == "materials":
            query = query.filter(Interaction.materials.ilike(f"%{value}%"))

        else:
            query = query.filter(getattr(Interaction, key) == value)
        
    results = query.all()
    db.close()
       
    if not results:
        return {
            "messages": state.get("messages", []) + [
                {"role": "ai", "text": "No matching records found."}
            ]
        }

    # FORMAT RESPONSE
    formatted = []

    for r in results:
        formatted.append(
            f"{r.hcp_name} | {r.date} | {r.time} | {r.sentiment} | {r.interaction_type}"
        )

    response_text = "\n".join(formatted)

    return {
        "messages": state.get("messages", []) + [
            {"role": "ai", "text": response_text}
        ]
    }