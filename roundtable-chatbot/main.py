import os

import json

import re

from typing import Optional



from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from groq import Groq



from database import (

    create_tables,

    add_message,

    get_messages,

    search_messages,

    get_speaker_messages,

    get_speakers,

    create_room,

    get_rooms,

    get_room,

    close_room,

)





# =========================================================

# CONFIG

# =========================================================



load_dotenv()



GROQ_API_KEY = os.getenv("GROQ_API_KEY")



if not GROQ_API_KEY:

    raise RuntimeError("GROQ_API_KEY is missing in .env")



client = Groq(api_key=GROQ_API_KEY)



MODEL_NAME = "openai/gpt-oss-120b"





# =========================================================

# FASTAPI

# =========================================================



app = FastAPI(

    title="Roundtable AI Backend",

    description="Roundtable Meeting Intelligence + General AI Assistant",

    version="1.0.0",

)



app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)



create_tables()





# =========================================================

# REQUEST MODELS

# =========================================================



class TranscriptRequest(BaseModel):

    room_id: str

    speaker: str

    text: str

    device_id: Optional[str] = None





class RoomRequest(BaseModel):

    room_id: str

    name: str





class ChatRequest(BaseModel):

    room_id: str

    message: str





class TranslateRequest(BaseModel):

    room_id: str

    target_language: str





# =========================================================

# HELPERS

# =========================================================



def clean_conversation(messages):

    cleaned = []



    for message in messages:



        if not cleaned:

            cleaned.append(message)

            continue



        previous = cleaned[-1]



        if (

            previous.get("speaker") == message.get("speaker")

            and previous.get("text") == message.get("text")

        ):

            continue



        cleaned.append(message)



    return cleaned





def format_transcript(messages):



    if not messages:

        return "No meeting transcript is available."



    lines = []



    for message in messages:



        timestamp = message.get("timestamp", "")

        speaker = message.get("speaker", "Unknown")

        text = message.get("text", "")



        lines.append(

            f"[{timestamp}] {speaker}: {text}"

        )



    return "\n".join(lines)





def get_room_or_404(room_id):



    room = get_room(room_id)



    if not room:

        raise HTTPException(

            status_code=404,

            detail="Room not found"

        )



    return room





def call_ai(

    system_prompt,

    user_prompt,

    temperature=0.2

):



    try:



        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=[

                {

                    "role": "system",

                    "content": system_prompt

                },

                {

                    "role": "user",

                    "content": user_prompt

                }

            ],

            temperature=temperature

        )



        return response.choices[0].message.content.strip()



    except Exception as e:



        raise HTTPException(

            status_code=500,

            detail=f"AI service error: {str(e)}"

        )





def parse_json(text):



    try:

        return json.loads(text)



    except Exception:

        pass



    match = re.search(

        r"**\\{**.***\\}**",

        text,

        re.DOTALL

    )



    if match:



        try:

            return json.loads(match.group(0))



        except Exception:

            pass



    return None





# =========================================================

# QUESTION CLASSIFIER

# =========================================================



def classify_question(question):
    q = question.lower().strip()

    # Explicit meeting requests MUST be checked before generic
    # "what is/what are" patterns. Otherwise questions such as
    # "What are the key points of the meeting?" are incorrectly
    # classified as general knowledge questions.

    meeting_phrases = [
        "summarize it", "summarise it",
        "summarize this", "summarise this",
        "summarize the meeting", "summarise the meeting",
        "meeting summary", "summary of the meeting",
        "give me a summary", "give summary",
        "key points", "key point", "main points",
        "important points", "important things",
        "main takeaways", "key takeaways", "takeaways",
        "recap it", "recap this", "recap the meeting", "meeting recap",
        "decisions", "what was decided", "what did we decide",
        "what have we decided",
        "action items", "action item", "tasks from the meeting",
        "what needs to be done",
        "what happened in the meeting", "what happened here",
        "what happened", "from the transcript",
        "according to the transcript",
        "timeline", "meeting timeline",
        "who said", "what did", "who mentioned", "who decided",
        "who agreed", "who is responsible", "who will handle",
        "who is handling",
    ]

    explicit_meeting_context = [
        "in the meeting", "in our meeting", "during the meeting",
        "from the meeting", "this meeting",
        "in our conversation", "in this conversation",
        "this conversation", "according to the meeting",
        "according to the transcript", "from the transcript",
    ]

    # Meeting phrases have priority over generic definition patterns.
    if any(phrase in q for phrase in meeting_phrases):
        return "meeting"

    general_patterns = [
        r"^what does .+ mean\??$",
        r"^what is .+\??$",
        r"^what are .+\??$",
        r"^define .+",
        r"^explain .+",
        r"^meaning of .+",
        r"^what do you mean by .+",
        r"^how does .+ work\??$",
        r"^how do .+ work\??$",
    ]

    is_general_definition = any(
        re.search(pattern, q)
        for pattern in general_patterns
    )

    if is_general_definition:
        if any(phrase in q for phrase in explicit_meeting_context):
            return "mixed"
        return "general"

    meeting_keywords = [
        "speaker", "speakers", "transcript",
        "decision", "decisions",
        "action item", "action items",
        "deadline", "agreed", "rejected", "proposed",
        "launch date", "responsible for", "handling",
        "deployment done by",
    ]

    if any(keyword in q for keyword in meeting_keywords):
        return "meeting"

    if any(phrase in q for phrase in explicit_meeting_context):
        return "mixed"

    return "general"



# =========================================================

# ROOT

# =========================================================



@app.get("/")

def root():



    return {

        "status": "online",

        "service": "Roundtable AI Backend",

        "model": MODEL_NAME,

        "docs": "/docs"

    }





# =========================================================

# ROOMS

# =========================================================



@app.post("/rooms")

def create_room_api(request: RoomRequest):



    existing = get_room(request.room_id)



    if existing:



        return {

            "message": "Room already exists",

            "room": existing

        }



    create_room(

        request.room_id,

        request.name

    )



    return {

        "message": "Room created successfully",

        "room": get_room(request.room_id)

    }





@app.get("/rooms")

def rooms_api():



    return {

        "rooms": get_rooms()

    }





@app.get("/rooms/{room_id}")

def room_api(room_id: str):



    room = get_room(room_id)



    if not room:



        raise HTTPException(

            status_code=404,

            detail="Room not found"

        )



    return room





@app.post("/rooms/{room_id}/close")

def close_room_api(room_id: str):



    room = get_room_or_404(room_id)



    if room["status"] == "closed":



        return {

            "message": "Room already closed",

            "room": room

        }



    close_room(room_id)



    return {

        "message": "Room closed successfully",

        "room": get_room(room_id)

    }





# =========================================================

# TRANSCRIPT

# =========================================================



@app.post("/transcript")

def add_transcript(request: TranscriptRequest):



    get_room_or_404(request.room_id)



    if not request.text.strip():



        raise HTTPException(

            status_code=400,

            detail="Transcript text cannot be empty"

        )



    add_message(

        room_id=request.room_id,

        speaker=request.speaker,

        text=request.text,

        device_id=request.device_id

    )



    return {

        "message": "Transcript added successfully",

        "room_id": request.room_id,

        "speaker": request.speaker,

        "device_id": request.device_id,

        "text": request.text

    }





@app.get("/transcript/{room_id}")

def transcript_api(room_id: str):



    get_room_or_404(room_id)



    messages = get_messages(room_id)



    return {

        "room_id": room_id,

        "count": len(messages),

        "messages": messages

    }





# =========================================================

# SPEAKERS

# =========================================================



@app.get("/speakers/{room_id}")

def speakers_api(room_id: str):



    get_room_or_404(room_id)



    return {

        "room_id": room_id,

        "speakers": get_speakers(room_id)

    }





@app.get("/speakers/{room_id}/{speaker}")

def speaker_messages_api(

    room_id: str,

    speaker: str

):



    get_room_or_404(room_id)



    messages = get_speaker_messages(

        room_id,

        speaker

    )



    return {

        "room_id": room_id,

        "speaker": speaker,

        "count": len(messages),

        "messages": messages

    }





# =========================================================

# SEARCH

# =========================================================



@app.get("/search/{room_id}")

def search_api(

    room_id: str,

    keyword: str

):



    get_room_or_404(room_id)



    if not keyword.strip():



        raise HTTPException(

            status_code=400,

            detail="Keyword cannot be empty"

        )



    results = search_messages(

        room_id,

        keyword

    )



    return {

        "room_id": room_id,

        "keyword": keyword,

        "count": len(results),

        "results": results

    }





@app.get("/search-ai/{room_id}")

def search_ai_api(

    room_id: str,

    keyword: str

):



    get_room_or_404(room_id)



    results = search_messages(

        room_id,

        keyword

    )



    if not results:



        return {

            "room_id": room_id,

            "keyword": keyword,

            "answer": "I couldn't find anything matching that keyword in the meeting.",

            "results": []

        }



    transcript = format_transcript(results)



    answer = call_ai(

        """

You are Roundtable AI.



Analyze the supplied meeting search results.



Explain what was found and who said it.



Do not invent information.

""",

        f"""

Keyword:



{keyword}



Matching transcript:



{transcript}

"""

    )



    return {

        "room_id": room_id,

        "keyword": keyword,

        "answer": answer,

        "results": results

    }





# =========================================================

# TIMELINE

# =========================================================



@app.get("/timeline/{room_id}")

def timeline_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    return {

        "room_id": room_id,

        "timeline": messages

    }





@app.get("/timeline-ai/{room_id}")

def timeline_ai_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    if not messages:



        return {

            "room_id": room_id,

            "timeline": []

        }



    response = call_ai(

        """

Create a chronological meeting timeline.



Return ONLY JSON:



{

  "timeline": [

    {

      "time": "",

      "speaker": "",

      "summary": ""

    }

  ]

}



Never invent events.

""",

        format_transcript(messages)

    )



    data = parse_json(response)



    return {

        "room_id": room_id,

        **(

            data

            if data

            else {

                "timeline": []

            }

        )

    }





# =========================================================

# MAIN CHAT

# =========================================================



@app.post("/chat")

def chat_api(request: ChatRequest):



    get_room_or_404(request.room_id)



    question = request.message.strip()



    if not question:



        raise HTTPException(

            status_code=400,

            detail="Message cannot be empty"

        )





    # =====================================================

    # CLASSIFY

    # =====================================================



    intent = classify_question(question)





    # =====================================================

    # LOAD TRANSCRIPT

    # =====================================================



    messages = clean_conversation(

        get_messages(request.room_id)

    )



    transcript = format_transcript(messages)





    # =====================================================

    # GENERAL AI + RELEVANT MEETING CONTEXT
    # =====================================================

    if intent == "general":

        system_prompt = """
You are Roundtable AI, a general-purpose AI assistant with
access to the current meeting transcript as additional context.

Answer the user's question using your normal AI knowledge.

The transcript is NOT a restriction and the answer does not
need to be contained in the transcript.

If the transcript contains information clearly relevant to the
user's question, connect the normal answer to that meeting
context.

Examples:
- "What is testing?" -> explain testing normally. If the
  transcript discusses testing, briefly connect the concept
  to that discussion.
- "What is TCP?" -> explain TCP normally. If TCP is not in
  the transcript, do not invent meeting context.
- "What is a key point?" -> define the term normally.

Return ONLY valid JSON:

{
  "answer": "natural language answer",
  "evidence": [
    {
      "speaker": "speaker name",
      "text": "relevant transcript statement"
    }
  ]
}

Use an empty evidence array when the transcript is not relevant.
Do not invent meeting information.
"""

        response = call_ai(
            system_prompt,
            f"""
CURRENT MEETING TRANSCRIPT:

{transcript}

USER QUESTION:

{question}
"""
        )

        data = parse_json(response)

        if not data:
            return {
                "room_id": request.room_id,
                "intent": "general",
                "question": question,
                "answer": response,
                "evidence": []
            }

        return {
            "room_id": request.room_id,
            "intent": "general",
            "question": question,
            "answer": data.get("answer", response),
            "evidence": data.get("evidence", [])
        }


    # =====================================================

    # MEETING AI

    # =====================================================



    if intent == "meeting":



        system_prompt = """

You are Roundtable AI, a MEETING INTELLIGENCE ASSISTANT.



The user is asking about the current meeting.



Use the supplied transcript as the primary source.



Answer questions such as:



- Summarize it

- Key points

- Important points

- Decisions

- Action items

- Who said something

- Who is responsible

- What happened

- What was decided

- Why was Monday rejected?

- What did Priya say?

- Who is handling deployment?



Meeting-specific claims MUST be supported by the transcript.



Never invent:

- speakers

- statements

- decisions

- tasks

- deadlines

- events



Return ONLY valid JSON:



{

  "answer": "natural language answer",

  "evidence": [

    {

      "speaker": "speaker name",

      "text": "relevant transcript statement"

    }

  ]

}



Evidence should contain only relevant statements.



For summary/key-point requests, provide a clean summary or

bullet-style answer based on the transcript.



Do not explain what a "key point" means unless the user asks

for the definition of the term itself.

"""



        response = call_ai(

            system_prompt,

            f"""

CURRENT MEETING TRANSCRIPT:



{transcript}



USER QUESTION:



{question}

"""

        )



        data = parse_json(response)



        if not data:



            return {

                "room_id": request.room_id,

                "intent": "meeting",

                "question": question,

                "answer": response,

                "evidence": []

            }



        return {

            "room_id": request.room_id,

            "intent": "meeting",

            "question": question,

            "answer": data.get(

                "answer",

                response

            ),

            "evidence": data.get(

                "evidence",

                []

            )

        }





    # =====================================================

    # MIXED AI

    # =====================================================



    system_prompt = """

You are Roundtable AI.



The user wants BOTH:



1\. A general explanation

2\. Relevant meeting context



First explain the concept normally.



Then connect it to the current meeting.



Example:



User:

"What does deployment mean in our meeting?"



Answer:



"Deployment means putting software into a live or

production environment so users can use it.



In your meeting, Amit agreed to handle the deployment

and send the release notes."



Return ONLY valid JSON:



{

  "answer": "natural language answer",

  "evidence": [

    {

      "speaker": "speaker name",

      "text": "relevant transcript statement"

    }

  ]

}



Do not invent meeting information.

"""



    response = call_ai(

        system_prompt,

        f"""

CURRENT MEETING TRANSCRIPT:



{transcript}



USER QUESTION:



{question}

"""

    )



    data = parse_json(response)



    if not data:



        return {

            "room_id": request.room_id,

            "intent": "mixed",

            "question": question,

            "answer": response,

            "evidence": []

        }



    return {

        "room_id": request.room_id,

        "intent": "mixed",

        "question": question,

        "answer": data.get(

            "answer",

            response

        ),

        "evidence": data.get(

            "evidence",

            []

        )

    }





# =========================================================

# INSIGHTS

# =========================================================



@app.get("/insights/{room_id}")

def insights_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    if not messages:



        return {

            "room_id": room_id,

            "summary": "No conversation available.",

            "key_topics": [],

            "important_points": [],

            "decisions": [],

            "action_items": []

        }



    response = call_ai(

        """

Analyze the meeting.



Return ONLY JSON:



{

  "summary": "",

  "key_topics": [],

  "important_points": [],

  "decisions": [],

  "action_items": [

    {

      "person": "",

      "task": "",

      "deadline": ""

    }

  ]

}



Never invent information.

""",

        format_transcript(messages)

    )



    data = parse_json(response)



    return {

        "room_id": room_id,

        **(

            data

            if data

            else {

                "summary": response,

                "key_topics": [],

                "important_points": [],

                "decisions": [],

                "action_items": []

            }

        )

    }





# =========================================================

# DECISIONS

# =========================================================



@app.get("/decisions/{room_id}")

def decisions_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    if not messages:



        return {

            "room_id": room_id,

            "decisions": []

        }



    response = call_ai(

        """

Find explicit decisions in the meeting.



Return ONLY JSON:



{

  "decisions": [

    {

      "decision": "",

      "speaker": "",

      "timestamp": ""

    }

  ]

}



Do not infer or invent decisions.

""",

        format_transcript(messages)

    )



    data = parse_json(response)



    return {

        "room_id": room_id,

        **(

            data

            if data

            else {

                "decisions": []

            }

        )

    }





# =========================================================

# ACTION ITEMS

# =========================================================



@app.get("/action-items/{room_id}")

def action_items_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    if not messages:



        return {

            "room_id": room_id,

            "action_items": []

        }



    response = call_ai(

        """

Find explicitly assigned action items.



Return ONLY JSON:



{

  "action_items": [

    {

      "person": "",

      "task": "",

      "deadline": ""

    }

  ]

}



Do not invent assignments.

""",

        format_transcript(messages)

    )



    data = parse_json(response)



    return {

        "room_id": room_id,

        **(

            data

            if data

            else {

                "action_items": []

            }

        )

    }





# =========================================================

# TRANSLATION

# =========================================================



@app.post("/translate")

def translate_api(request: TranslateRequest):



    get_room_or_404(request.room_id)



    messages = clean_conversation(

        get_messages(request.room_id)

    )



    if not messages:



        return {

            "room_id": request.room_id,

            "target_language": request.target_language,

            "translation": "No conversation available."

        }



    translation = call_ai(

        f"""

Translate the meeting transcript into

{request.target_language}.



Rules:



- Preserve speaker names.

- Preserve chronological order.

- Preserve meaning.

- Do not add information.

- Do not remove information.

""",

        format_transcript(messages)

    )



    return {

        "room_id": request.room_id,

        "target_language": request.target_language,

        "translation": translation

    }





# =========================================================

# INCOMPLETE SENTENCE RECOVERY

# =========================================================



@app.get("/recover/{room_id}")

def recover_api(room_id: str):



    get_room_or_404(room_id)



    messages = clean_conversation(

        get_messages(room_id)

    )



    if not messages:



        return {

            "room_id": room_id,

            "recoveries": []

        }



    response = call_ai(

        """

Find incomplete or truncated transcript sentences.



Return ONLY JSON:



{

  "recoveries": [

    {

      "speaker": "",

      "original": "",

      "recovered": "",

      "confidence": "high"

    }

  ]

}



Only reconstruct when strongly supported by context.



Never invent speech.

""",

        format_transcript(messages)

    )



    data = parse_json(response)



    return {

        "room_id": room_id,

        **(

            data

            if data

            else {

                "recoveries": []

            }

        )

    }