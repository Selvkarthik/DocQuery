from typing import List, Dict, Any, Generator, Optional
from openai import OpenAI
from app.core.config import settings
from app.core.logging import logger


class LLMGeneratorService:
    def __init__(self):
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        if not settings.API_KEY:
            raise RuntimeError("API_KEY is not configured in .env. Please configure it to enable LLM generation.")
        if self._client is None:
            self._client = OpenAI(
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.API_KEY,
                timeout=30.0,
            )
        return self._client

    def _build_messages(
        self,
        question: str,
        context_text: str,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        system_instruction = (
            "You are DocQuery, an intelligent and precise Enterprise Document Assistant. "
            "Your task is to answer the user's question accurately using ONLY the provided document context. "
            "Follow these strict guidelines:\n"
            "1. Ground your response strictly in the provided context.\n"
            "2. If the context does not contain enough information to answer the question, clearly state: "
            "'I do not have enough information in the provided documents to answer that question.'\n"
            "3. Maintain a helpful, professional, and clear tone.\n"
            "4. Consider the ongoing conversation history when answering follow-up questions."
        )

        messages = [{"role": "system", "content": system_instruction}]

        # Inject recent conversation turns
        if history:
            for msg in history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})

        # Inject current question with retrieved context
        user_prompt = (
            f"Document Context:\n{context_text}\n\n"
            f"User Question: {question}"
        )
        messages.append({"role": "user", "content": user_prompt})

        return messages

    def generate_answer(
        self,
        question: str,
        context_text: str,
        history: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> str:
        """Generate answer via OpenRouter API."""
        client = self._get_client()
        active_model = model or settings.OPENROUTER_MODEL
        messages = self._build_messages(question, context_text, history)

        try:
            response = client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=0.2,
                max_tokens=800,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise RuntimeError(f"Error generating answer from LLM: {str(e)}")

    def generate_answer_stream(
        self,
        question: str,
        context_text: str,
        history: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """Stream generated answer tokens via OpenRouter API."""
        client = self._get_client()
        active_model = model or settings.OPENROUTER_MODEL
        messages = self._build_messages(question, context_text, history)

        try:
            stream = client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=0.2,
                max_tokens=800,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"LLM streaming failed: {e}")
            yield f"\n[Generation error: {str(e)}]"


generator_service = LLMGeneratorService()
