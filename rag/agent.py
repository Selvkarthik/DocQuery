"""Interactive client for the RAG pipeline.

Run with ``python -m rag.agent``
"""

from app.services.memory import memory_service
from app.services.rag_service import rag_service


def run_chat(session_id: str = "local") -> None:
    """Answer policy questions and retain a compact per-session transcript in Redis."""
    print("========================================================")
    print(" DocQuery Policy Assistant (CLI Mode)")
    print(f" Session ID: {session_id}")
    print(" Type 'exit' to quit.")
    print("========================================================")

    while True:
        try:
            question = input("\nYou: ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit"):
                print("Goodbye!")
                return

            result = rag_service.answer_question(
                question=question,
                session_id=session_id,
            )

            print(f"\nAssistant: {result['answer']}")

            if result.get("sources"):
                print("\n[Sources Cited]:")
                for s in result["sources"]:
                    print(f" - {s['source']} (Chunk {s['chunk_index']}, Sim: {s['similarity']:.2f})")

        except KeyboardInterrupt:
            print("\nExiting...")
            return
        except Exception as e:
            print(f"\n[Error]: {e}")


if __name__ == "__main__":
    run_chat()
