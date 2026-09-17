"""RAG pipeline adapter for backward compatibility."""

from app.services.rag_service import rag_service


def question_answer(question: str, top_k: int = 2):
    """Execute standard RAG question answering pipeline."""
    result = rag_service.answer_question(
        question=question,
        top_k=top_k,
    )
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }


if __name__ == "__main__":
    result = question_answer(
        "How many days leave do interns receive?",
        top_k=2,
    )
    print("Answer:")
    print(result["answer"])
    print("\nSources:")
    for source in result["sources"]:
        print(source)