from src.state.state import InteractionState
from langgraph.graph import StateGraph, END
from src.nodes.edit_node import edit_interaction
from src.nodes.log_node import log_node
from src.nodes.query_sentiment_node import query_node
from src.nodes.followup_node import followup_node
from src.nodes.intention_node import intent_node
from src.nodes.delete_data import delete_data_node


def route(state: InteractionState):
    intent = state["intent"]
    
    if intent == "log":
        return "log"
    elif intent == "edit_interaction":
        return "edit_interaction"
    elif intent == "query":
        return "query"
    elif intent == "delete":
        return "delete"
    

from langgraph.graph import END


def route_after_log(state: InteractionState):
    if state.get("status") == "complete":
        return "followup"
    else:
        return "end"


def build_graph():
    builder = StateGraph(InteractionState)
    
    builder.add_node("intent", intent_node)
    builder.add_node("log", log_node)
    builder.add_node("edit_interaction", edit_interaction)
    builder.add_node("query", query_node)
    builder.add_node("followup", followup_node)
    builder.add_node("delete", delete_data_node)
    
    builder.set_entry_point("intent")
    
    builder.add_conditional_edges(
            "intent",
            route,
            {
                "log": "log",
                "edit_interaction": "edit_interaction",
                "query": "query",
                "delete": "delete",
            }
        )
    
    builder.add_conditional_edges(
        "log",
        route_after_log,
        {
            "followup": "followup",
            "end": END
        }
    )

    builder.add_edge("edit_interaction", END)
    builder.add_edge("query", END)
    builder.add_edge("followup", END)
    builder.add_edge("delete", END)
    
    return builder.compile()