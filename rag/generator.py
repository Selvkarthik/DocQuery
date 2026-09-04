from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.getenv('API_KEY'))

def generate_answer(question, context):
    instruction = """Answer the question only using the provided context.
    If the answer cannot be found in the context, say you don't know."""

    prompt = f"""{instruction}

        Context:
        {context}

        Question:
        {question}
    """

    response = client.chat.completions.create(
        model = 'inclusionai/ling-3.0-flash-fin:free',
        messages=[{
            'role' : 'user',
            'content' : prompt
        }]
    )

    return response.choices[0].message.content