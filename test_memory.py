from memory.redis_memory import save_messages, load_messages

session_id = 'karthik'

messages = [
    {
        'role' : 'user',
        'content' : 'my name is karthik'
    },
    {
        'role' : 'assistant',
        'content' : 'Nice to meet you!'
    }
]

save_messages(session_id, messages)
loaded_message = load_messages(session_id)
print(loaded_message)