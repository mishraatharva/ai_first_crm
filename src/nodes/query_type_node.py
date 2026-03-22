from src.state.state import QueryExtraction, InteractionState
from dotenv import load_dotenv
load_dotenv()


from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.3-70b-versatile")


def query_type_node(state: InteractionState):
    structured_llm = llm.with_structured_output(QueryExtraction)

    prompt = f"""
    Extract query filter from:
    {state["input"]}

    Example:
    field = interaction_type
    value = meeting
    """

    result = structured_llm.invoke(prompt)

    # simulate DB
    fake_db = [
        {"hcp_name": "Dr. Smith", "interaction_type": "meeting"},
        {"hcp_name": "Dr. John", "interaction_type": "call"},
    ]

    filtered = [
        x for x in fake_db if x.get(result.field) == result.value
    ]

    return {"result": filtered}