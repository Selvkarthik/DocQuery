import json
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.core.logging import logger
from app.services.retriever import retriever_service
from app.services.generator import generator_service


def tool_search_documents(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search company knowledge base for policy or factual information."""
    return retriever_service.retrieve(query=query, top_k=top_k)


def tool_calculate_percentage(part: float, whole: float) -> float:
    """Calculate the percentage of a part relative to a whole."""
    if whole == 0:
        raise ValueError("Cannot calculate percentage when whole is zero.")
    return round((part / whole) * 100.0, 2)


AVAILABLE_TOOLS = {
    "search_company_document": {
        "function": tool_search_documents,
        "description": "Searches company documents and returns matching chunks.",
        "parameters": {"query": "str", "top_k": "int"},
    },
    "calculate_percentage": {
        "function": tool_calculate_percentage,
        "description": "Calculates (part / whole) * 100.",
        "parameters": {"part": "float", "whole": "float"},
    },
}


class AgentService:
    def __init__(self):
        self.generator = generator_service

    def run(self, prompt: str, session_id: str = "agent-default") -> Dict[str, Any]:
        """Execute an agent reasoning loop with available tools."""
        tools_used: List[Dict[str, Any]] = []

        # Tool 1: Always retrieve contextual knowledge for relevant domain questions
        retrieved = tool_search_documents(prompt, top_k=3)
        tools_used.append({
            "tool_name": "search_company_document",
            "tool_input": {"query": prompt, "top_k": 3},
            "tool_output": f"Retrieved {len(retrieved)} relevant chunks",
        })

        context_blocks = [f"[{r['source']}] {r['content']}" for r in retrieved]
        context_str = "\n".join(context_blocks) if context_blocks else "No relevant documents found."

        system_prompt = (
            "You are an intelligent Assistant capable of synthesizing document knowledge and calculations.\n"
            f"Retrieved Document Context:\n{context_str}\n\n"
            "If the question involves percentages or numerical comparisons, state the math clearly.\n"
            "Provide a comprehensive, direct, and well-structured answer."
        )

        try:
            client = self.generator._get_client()
            response = client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=800,
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            answer = f"Agent failed to complete reasoning: {str(e)}"

        return {
            "answer": answer,
            "session_id": session_id,
            "tools_used": tools_used,
        }


agent_service = AgentService()
