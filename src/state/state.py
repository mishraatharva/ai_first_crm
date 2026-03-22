from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel, Field


class InteractionData(BaseModel):
    hcp_name: Optional[str]
    date: Optional[str]
    time: Optional[str]
    topics: Optional[str]
    materials: Optional[List[str]] = Field(
        default=None,
        description="List of materials (ALWAYS return as list, even if single item)"
    )
    sentiment: Optional[str]
    interaction_type : Optional[str] = Field(description="How user meet with hcp(example: on call, facetoface(face-to-face), online meeting etc)")


class IntentOutput(BaseModel):
    intent: str


class InteractionState(TypedDict):
    input: str
    intent: Optional[str]
    interaction_data: Dict[str, Any]
    messages: List[Dict[str, str]]  # FIX: Changed from List[str] to List[Dict[str, str]] for {role, text} format
    status: Optional[str]
    missing_data_question: Optional[str]
    followUps: Optional[List[str]]  # FIX: Changed from followups to followUps
    last_id: Optional[int]


class InteractionExtraction(BaseModel):
    hcp_name: Optional[str]
    date: Optional[str]
    time: Optional[str]
    attendees: Optional[str]
    topics: Optional[str]
    materials: Optional[List[str]] = Field(
        default=None,
        description="List of materials (ALWAYS return as list, even if single item)"
    )
    sentiment: Optional[str]
    outcomes: Optional[str]
    follow_up: Optional[str]



class EditExtraction(BaseModel):
    field_need_change: Optional[str]
    new_data : Optional[str]


from typing import Optional, List
from pydantic import BaseModel

class QueryExtraction(BaseModel):
    hcp_name: Optional[str]
    date: Optional[str]
    sentiment: Optional[str]
    interaction_type: Optional[str]
    materials: Optional[str]