from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import redis

from tools import search_company_document, calculate_percentage

load_dotenv()

def load_messages(session_id):
    data = redis_client.get(f"session: {session_id}")
    if data:
        return json.loads(data)
    return []

def save_messages(session_id, messages):
    redis_client.set(f"session: {session_id}", json.dumps(session_id))

client = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=os.getenv('API_KEY'))
model = 'inclusionai/ling-3.0-flash-fin:free'

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

available_tools = {
    "search_company_documents" : search_company_document,
    "calculate_percentage" : calculate_percentage
}

def summarize_messages(messages):
    prompt = """
Summarize the important information from this conversation.

Keep:
- Important facts provided by the user
- Important facts retrieved from tools
- User preferences or information that may be useful later
- Important decisions or ongoing context

Do not include unnecessary greetings or repetitive conversation.
Return only the summary.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role" : "system",
            "content" : prompt
        },{
            "role" : "user",
            "content" : str(messages)
        }]
    )
    return response.choices[0].message.content

session_id = 'karthik'
messages = load_messages(session_id)
if not messages:
    messages = [{
        "role" : "system",
        "content" : """
    You are a company policy assistant.

    Rules:
    1. Use search_company_documents for questions about
    company policies, rules, benefits, leave, employees,
    or interns.

    2. Answer company-policy questions ONLY using information
    returned by the search_company_documents tool.

    3. If the retrieved documents do not contain the answer,
    say that you don't know based on the available company
    policy documents.

    4. Do not invent or assume company policies.

    5. Do not use general knowledge to fill missing information.

    6. You may answer normal conversational or opinion questions
    without using the company documents, but clearly distinguish
    your opinion from company policy.
    """
    }]

tools = [
    {
        "type" : "function",
        "function" : {
            "name" : "search_company_documents",
            "description" : (
                "Search company poolicy documents for information "
                "needed to answer the user's question"
            ),
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "question" : {
                        "type" : "string",
                        "description" : "The question to search for in company documents."
                    }
                },
                "required" : ["question"]
            }
        }
    },
    {
        "type" : "function",
        "function" : {
            "name" : "calculate_percentage",
            "description" : ("return the calculated percentage."),
            "parameters" : {
                "type" : "object",
                "properties" : {
                    "part" : {"type" : "number"},
                    "whole" : {"type" : "number"}
                },
                "required" : ["part", "whole"]
            }
        }
    }
]

while True:
    question = input("You: ")

    if question.lower() == 'exit':
        break

    messages.append({
        "role" : "user",
        "content" : question
    })

    while True:
        if len(messages) > 12:
            summary = summarize_messages(messages[:-6])
            messages = [messages[0],
                        {
                            "role" : "system",
                            "content" : f"Conversation summary:\n{summary}"
                        }] + messages[-6:]

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )
        message = response.choices[0].message
        assistant_message = {
            "role" : "assistant",
            "content" : message.content,
            "tool_calls" : [{
                "id" : tool_call.id,
                "type" : "function",
                "function" : {
                    "name" : tool_call.function.name,
                    "arguments" : tool_call.function.arguments
                }
            }
            for tool_call in (message.tool_calls or [])
            ]
        }
        messages.append(assistant_message)

        if not message.tool_calls:
            print(message.content)
            break

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            try:
                function_name = available_tools[tool_name]
                result = function_name(**arguments)
            except Exception as err:
                result = f"Tool error: {str(err)}"
            messages.append({
                "role" : "tool",
                "tool_call_id" : tool_call.id,
                "content" : str(result)
            })