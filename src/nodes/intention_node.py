from src.state.state import IntentOutput, InteractionState
from dotenv import load_dotenv
from langchain_groq import ChatGroq
load_dotenv()

def intent_node(state: InteractionState, config):
    """
    Determines user intent from input text: 'log' for new data, 'edit_interaction' for updates, 'query' for searches.
    Uses structured LLM output and updates conversation history.
    """
    print(state)
    llm = config["configurable"]["llm"]
    
    #Converts LLM into structured mode
    structured_llm = llm.with_structured_output(IntentOutput)
    

    """
    This prompt will classify the user input into one of 4 categories:[log, edit_interaction, query, delete]
    """
    prompt = f"""
    Classify user intent into one of:
    - log # only in case of total new data
    - edit_interaction # incase to update any field of last saved data
    - query # for querying existing data
    - delete # for deleting existing data
    
    Input: {state["input"]}
    """
    
    result = structured_llm.invoke(prompt)
    
    # FIX: Add user message to conversation history
    user_message = {"role": "user", "text": state["input"]}
    current_messages = state.get("messages", [])
    
    return {
        "intent": result.intent,
        "messages": current_messages + [user_message]
    }