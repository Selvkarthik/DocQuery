from .retriever import retrieve_chunks
from .generator import generate_answer

"""The complete rag pipeline"""

def question_answer(question, top_k=2):
    sources = retrieve_chunks(question, top_k)

    if not sources:
        return {"answer" : "I don't know",
                "sources" : []}

    context = [row['content'] for row in sources]
    context_text = '\n'.join(context)

    answer = generate_answer(context=context_text, question=question)

    return {
        'answer' : answer,
        'sources' : sources
    }

if __name__ == "__main__":
    result = question_answer(
        "How many days leave do interns receive?",
        top_k=2
    )

    print("Answer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(source)