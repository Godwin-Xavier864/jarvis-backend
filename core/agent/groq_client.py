from groq import Groq
import os

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

def run_groq_agent(messages):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content
