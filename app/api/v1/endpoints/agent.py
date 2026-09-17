from fastapi import APIRouter, HTTPException, status
from app.services.agent_service import agent_service
from app.schemas.agent import AgentRequest, AgentResponse, ToolExecution

router = APIRouter(prefix="/agent", tags=["Agent"])


@router.post(
    "/run",
    response_model=AgentResponse,
    summary="Run tool-augmented agent",
    description="Executes multi-step reasoning by retrieving knowledge base context and performing analytical tools.",
)
def run_agent(request: AgentRequest):
    try:
        result = agent_service.run(prompt=request.prompt, session_id=request.session_id)
        tools_executed = [
            ToolExecution(
                tool_name=t["tool_name"],
                tool_input=t.get("tool_input", {}),
                tool_output=t.get("tool_output"),
            )
            for t in result.get("tools_used", [])
        ]
        return AgentResponse(
            answer=result["answer"],
            session_id=result["session_id"],
            tools_used=tools_executed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {str(e)}",
        )
