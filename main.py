from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

from rag.rag_pipeline import question_answer

app = FastAPI()

class QuestionRequest(BaseModel):
    question : str

class Source(BaseModel):
    source : str
    chunk_index : int
    similarity : float

class AnswerResponse(BaseModel):
    answer : str
    sources : List[Source]

@app.post('/ask', response_model=AnswerResponse)
def ask_question(request : QuestionRequest):
    result = question_answer(request.question)

    sources = []
    for source in result['sources']:
        sources.append({
            'source' : source['source'],
            'chunk_index' : source['chunk_index'],
            'similarity' : 1 - source['distance']
        })

    return {
        'answer' : result['answer'],
        'sources' : sources
    }