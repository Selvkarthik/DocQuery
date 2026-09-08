from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from database import SessionLocal

model = SentenceTransformer('all-MiniLM-L6-v2')

def retrieve_chunks(question, top_k = 2, similarity_threshold = 0.5):
    query_embedding = model.encode(question)

    db = SessionLocal()

    try:
        result = db.execute(
            text(f"""
                SELECT content, source, chunk_index,
                embedding <=> CAST(:query_embedding AS vector) AS distance
                FROM document_chunks
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT {top_k}
            """),
            {
                'query_embedding' : str(query_embedding.tolist())
            }
        )

        sources = []
        for row in result:
            similarity = 1 - row[3]
            if similarity >= similarity_threshold:
                sources.append({
                    'content' : row[0],
                    'source' : row[1],
                    'chunk_index' : row[2],
                    'distance' : row[3]
                })

        return sources

    finally:
        db.close()

# if __name__ == "__main__":
#     result = retrieve_chunks(
#         question="How many annual leave days do interns receive?",
#         top_k=2
#     )
#     for row in result:
#         print(row)