from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ToolExecution(BaseModel):
    tool_name: str = Field(..., description="Name of executed tool")
    tool_input: Dict[str, Any] = Field(default_factory=dict, description="Input parameters passed to tool")
    tool_output: Any = Field(..., description="Result returned from the tool")


class AgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000, description="Task or multi-step question for the agent")
    session_id: str = Field(default="agent-default", description="Session identifier for the agent")


class AgentResponse(BaseModel):
    answer: str = Field(..., description="Final reasoning response from the agent")
    session_id: str
    tools_used: List[ToolExecution] = Field(default_factory=list, description="Audit trail of tools executed")
