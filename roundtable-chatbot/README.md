# Roundtable_bot
# Roundtable AI Chatbot

AI chatbot for the Roundtable meeting platform.  
It works with the meeting transcript and helps users understand, search and summarize conversations.

## Features

- **Meeting Summary**
  - Gives a short summary of the complete conversation.
  - Can summarize the important discussion points.

- **Key Points**
  - Extracts the main points discussed during the meeting.
  - Helps users quickly understand what was discussed.

- **Contextual Questions**
  - Users can ask questions about the current meeting.
  - Answers are based on the available meeting transcript.

- **General Questions**
  - Can answer normal/general questions also.
  - Meeting transcript is used as additional context when relevant.

- **Speaker Information**
  - Shows which participant said something.
  - Can answer questions related to a particular speaker.

- **Conversation Timeline**
  - Keeps messages in chronological order.
  - Helps track who said what during the meeting.

- **Action Items**
  - Identifies tasks mentioned during the conversation.
  - Can identify the person responsible for a task when mentioned.

- **Decisions**
  - Helps identify important decisions made during the meeting.

- **Transcript Search**
  - Search for specific words or topics in the meeting transcript.
  - Returns matching conversation entries.

- **Transcript Recovery**
  - Helps recover incomplete sentences from partial transcripts.
  - Uses the surrounding conversation for context.

- **Multilingual Support**
  - Supports translation of conversation content into other languages.

- **Speaker and Device Tracking**
  - Stores speaker and device information with transcript messages.
  - Useful when multiple devices are being used in the same meeting.

## How It Works

1. Meeting devices send conversation messages to the backend.
2. The messages are stored with speaker, room and timestamp information.
3. The chatbot receives the user's question.
4. It checks the meeting transcript when the question is related to the conversation.
5. The AI generates the response.
6. Relevant meeting messages can be returned as evidence.

## Example Questions

```text
Summarize the meeting.

What are the key points?

What did Rahul say?

Who is responsible for deployment?

What decision was made about the launch?

What is testing?

What does deployment mean in our meeting?

Find mentions of testing.
