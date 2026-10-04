from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import errors
import os
import time

load_dotenv()

app = FastAPI(
    title="Roundtable AI Chatbot",
    description="AI assistant for live group conversations",
    version="1.0.0"
)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

# Primary + fallback models
PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-3.5-flash-lite"


TRANSCRIPT = """
[10:01] Rahul: We should launch the website on Monday.

[10:02] Priya: Monday is too early. We still need more testing.

[10:03] Aman: I agree with Priya. Wednesday would be safer.

[10:04] Rahul: Okay, let's launch on Wednesday then.

[10:05] Priya: I'll handle the final testing before Tuesday evening.

[10:06] Aman: I'll prepare the deployment checklist.
"""


class ChatRequest(BaseModel):
    question: str


def ask_gemini(prompt: str):

    # Try primary model
    try:

        response = client.models.generate_content(
            model=PRIMARY_MODEL,
            contents=prompt
        )

        return response.text

    except errors.ServerError as e:

        print("Primary model unavailable:", e)

    # Small delay before fallback
    time.sleep(2)

    # Try fallback model
    try:

        response = client.models.generate_content(
            model=FALLBACK_MODEL,
            contents=prompt
        )

        return response.text

    except errors.ServerError as e:

        print("Fallback model unavailable:", e)

        return (
            "The AI service is temporarily busy. "
            "Please try again in a few seconds."
        )


def build_prompt(question: str):

    return f"""
You are Roundtable AI, an intelligent assistant for live group conversations.

CURRENT CONVERSATION TRANSCRIPT:

{TRANSCRIPT}

USER QUESTION:

{question}

RULES:

1. Use the transcript as the primary source.
2. Do not invent information.
3. If the answer is not present, say:
   "I couldn't find that information in the conversation."
4. Correctly identify speakers.
5. Use timestamps when useful.
6. For summaries, provide concise important points.
7. For decisions, identify the final decision.
8. For action items, identify the person and task.
9. For explanations, use simple language.
10. For recap requests, explain the flow of the discussion.
11. If asked for another language, answer in that language.
12. If a sentence is incomplete, use surrounding context only
    when the meaning is reasonably clear.
13. Never invent missing speech.

Answer the user's question clearly.
"""


@app.get("/")
def home():

    return {
        "message": "Roundtable AI Chatbot is running!"
    }


@app.get("/test")
def test():

    answer = ask_gemini(
        "Say exactly: Roundtable AI is working!"
    )

    return {
        "response": answer
    }


@app.post("/chat")
def chat(request: ChatRequest):

    if not request.question.strip():

        return {
            "answer": "Please enter a question."
        }

    prompt = build_prompt(request.question)

    answer = ask_gemini(prompt)

    return {
        "question": request.question,
        "answer": answer
    }