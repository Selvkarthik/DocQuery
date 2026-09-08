from retriever import retrieve_chunks

def search_company_document(question):
    results = retrieve_chunks(question, top_k=2)

    return [
        {
            "content" : row['content'],
            'source' : row['source'],
            'chunk_index' : row['chunk_index'],
            'distance' : row['distance']
        }
        for row in results
    ]

def calculate_percentage(part, whole):
    if whole == 0:
        raise ValueError("The whole value cannot be zero.")
    return (part / whole) * 100