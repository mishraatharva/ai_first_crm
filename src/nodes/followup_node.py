from src.state.state import  InteractionState
from dotenv import load_dotenv
load_dotenv()


from langchain_groq import ChatGroq
llm = ChatGroq(model="llama-3.3-70b-versatile")


def followup_node(state: InteractionState, config):
    """
    Generates personalized follow-up suggestions based on recent interactions.
    
    What it does: This function looks at recent cached interactions and uses AI to suggest follow-up actions.
    
    Steps explained simply:
    1. Gets the cache (memory storage) from config - this holds recent positive/neutral interactions.
    2. Gets the language model (LLM) from config - this is the AI that will generate suggestions.
    3. Retrieves all recent interactions from cache - gets the stored data about past meetings/calls.
    4. If no recent interactions exist, returns a default message saying no data available.
    5. Creates a text summary (context) by combining details from each recent interaction like HCP name, date, sentiment, etc.
    6. Builds a prompt for the AI asking it to generate 2-3 personalized follow-up suggestions based on the context.
    7. Tries to call the AI with the prompt and get a response.
    8. Takes the AI's response text and removes extra spaces.
    9. Parses the response into a list by splitting on newlines and cleaning up bullet points/numbers.
    10. If no suggestions were parsed, uses a default suggestion.
    11. Creates a formatted message for the chat (though not used in return).
    12. Returns the top 3 suggestions in a list for UI display.
    13. If any error occurs during AI call, prints the error and returns a default suggestion.
    """
    
    cache = config["configurable"]["cache"]
    llm = config["configurable"]["llm"]

    recent = cache.get_all()

    if not recent:
        return {
            "followUps": ["No recent interactions available for follow-up suggestions."]
        }

    # Prepare context from recent interactions
    context = "\n".join([
        f"HCP: {r['hcp_name']}, Date: {r['date']}, Sentiment: {r['sentiment']}, "
        f"Type: {r['interaction_type']}, Topics: {r.get('topics', 'N/A')}, "
        f"Materials: {r.get('materials', 'N/A')}"
        for r in recent
    ])

    prompt = f"""
    Based on these recent HCP interactions, generate 2-3 personalized follow-up action items.
    Focus on actionable suggestions that would strengthen the relationship or advance business goals.

    Recent Interactions:
    {context}

    Generate follow-up suggestions that are:
    - Specific and actionable
    - Personalized to the HCP and interaction details
    - Focused on relationship building and business advancement
    - Realistic and timely

    Return only the suggestions as a numbered list, no additional text.
    """

    try:
        response = llm.invoke(prompt)
        suggestions_text = response.content.strip()
        
        # Parse the suggestions into a list
        suggestions = [line.strip('-•123456789. ').strip() for line in suggestions_text.split('\n') if line.strip()]
        
        # Ensure we have at least some suggestions
        if not suggestions:
            suggestions = ["Schedule a follow-up meeting to discuss next steps"]
        
        return {
            "followUps": suggestions[:3]  # Only return for UI rendering, not add to chat messages
        }
        
    except Exception as e:
        print(f"Error generating followups: {e}")
        return {
            "followUps": ["Schedule a follow-up meeting to discuss next steps"]
        }




        # Create a message for the chat
        # followup_message = {
        #     "role": "ai", 
        #     "text": "Here are some AI-generated follow-up suggestions based on recent interactions:\n" + 
        #            "\n".join(f"• {suggestion}" for suggestion in suggestions[:3])
        # }