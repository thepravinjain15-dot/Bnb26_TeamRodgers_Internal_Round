# DESI --- Distributed Speech Intelligence

> Real-time, speaker-aware captions for physical group conversations.

## Overview

DESI is a distributed speech intelligence system designed for
**in-person group conversations**. Instead of relying on a single
microphone, DESI allows multiple nearby phones or laptops to act as
independent audio viewpoints.

The system processes these audio perspectives to identify speakers and
produce low-latency, speaker-attributed transcripts.

### Core idea

``` text
Multiple Participant Devices
            ↓
      Distributed Audio
            ↓
   Speech / Audio Processing
            ↓
      Speaker Identification
            ↓
    Multi-Device Evidence
            ↓
       Speaker Attribution
            ↓
       Speech-to-Text
            ↓
    Speaker-Aware Captions
```

DESI is currently focused on **physical meetings and conversations**.
Online meeting integrations such as Google Meet, Zoom, or Teams are
outside the current scope.

------------------------------------------------------------------------

## Problem

In physical group conversations, a single microphone often performs
poorly because:

-   Participants are at different distances from the microphone.
-   Background noise affects speech recognition.
-   Multiple people may speak from different positions.
-   Speakers can change frequently.
-   A transcript without speaker identity is difficult to follow.
-   A participant may temporarily disconnect and need to rejoin without
    losing session context.

DESI addresses this by using multiple nearby devices as distributed
audio sources and combining speaker identity with audio evidence.

------------------------------------------------------------------------

## Key Features

### 1. Room Management

-   Create a conversation room.
-   Generate a room code.
-   Generate a QR code for joining.
-   Maintain a persistent session.
-   Allow participants to leave and rejoin.

### 2. Participant Identity

-   Participant enters their name.
-   Participant records a short voice sample.
-   A speaker embedding is generated from the sample.
-   The embedding is associated with the participant's user ID.

### 3. Distributed Audio Capture

Each participant device captures the surrounding conversation.

A device is **not assumed to hear only its owner**. Every device can
capture multiple people, providing different perspectives of the same
conversation.

### 4. Speaker Identification

Incoming speech segments are compared with enrolled speaker profiles.

Example:

``` json
{
  "user_id": "u001",
  "name": "Princess",
  "confidence": 0.91
}
```

If the system cannot confidently identify a speaker, it returns:

``` text
Unknown Speaker
```

### 5. Audio Segments

Each processed speech segment is associated with:

-   Segment ID
-   Room ID
-   Speaker ID
-   Speaker name
-   Confidence
-   Audio file
-   Start timestamp
-   End timestamp

Example:

``` json
{
  "segment_id": "seg_0042",
  "room_id": "ROOM123",
  "user_id": "u001",
  "speaker_name": "Princess",
  "confidence": 0.91,
  "audio_file": "chunk_0042.wav",
  "start_time": 12.4,
  "end_time": 15.8,
  "transcription_status": "pending",
  "transcript": null
}
```

### 6. Live Transcription

The identified audio segment is passed to the speech-to-text pipeline.

Example:

``` text
Princess — "Let's begin the discussion."
```

Each transcript remains linked to its original audio segment.

### 7. Dashboard

The dashboard provides:

-   Active participants
-   Audio quality
-   Speaking time
-   Audio segment count
-   Live transcript
-   Speaker confidence
-   Audio playback
-   Participant activity
-   Speaker activity
-   Session history

------------------------------------------------------------------------

## System Architecture

``` text
                         DESI
                          │
             ┌────────────┴────────────┐
             │                         │
       Participant Devices        DESI Backend
             │                         │
       ┌─────┼─────┐              FastAPI
       │     │     │                 │
     Phone Phone Laptop          WebSocket
       │     │     │                 │
       └─────┼─────┘                 ↓
             │                 Audio Processing
             ↓                       │
       Audio Streams                VAD
             │                       │
             └───────────────────────┤
                                     ↓
                              Speaker Recognition
                                     │
                              ECAPA-TDNN
                                     │
                                     ↓
                              Speaker Attribution
                                     │
                                     ↓
                                Speech-to-Text
                                     │
                                     ↓
                                Transcript
                                     │
                                     ↓
                               DESI Dashboard
```

------------------------------------------------------------------------

## Technology Stack

### Frontend

-   Next.js
-   TypeScript
-   Tailwind CSS
-   Web Audio API / MediaRecorder
-   WebSocket

### Backend

-   Python
-   FastAPI
-   WebSocket

### Audio / AI

-   Silero VAD --- voice activity detection
-   SpeechBrain ECAPA-TDNN --- speaker recognition
-   PyTorch --- model inference
-   faster-whisper --- speech-to-text

### Data

-   PostgreSQL
-   Redis

### Deployment

-   Vercel --- frontend
-   Railway or equivalent backend hosting --- FastAPI/AI service
-   PostgreSQL/Supabase --- persistent database

------------------------------------------------------------------------

## Speaker Identification Pipeline

### Enrollment

``` text
Participant enters name
        ↓
Record 5–10 second voice sample
        ↓
Preprocess audio
        ↓
ECAPA-TDNN
        ↓
Speaker embedding
        ↓
Store embedding + user ID
```

### Recognition

``` text
Incoming audio
       ↓
Voice Activity Detection
       ↓
Speech segment
       ↓
ECAPA-TDNN embedding
       ↓
Compare with enrolled embeddings
       ↓
Similarity / confidence
       ↓
Speaker identity
```

Speaker thresholds should be calibrated using real recordings rather
than relying on an arbitrary universal threshold.

------------------------------------------------------------------------

## Audio-to-Transcript Pipeline

``` text
Audio Chunk
    ↓
VAD
    ↓
Speaker Identification
    ↓
Speaker + Confidence + Timestamp
    ↓
Speech-to-Text
    ↓
Transcript
    ↓
Dashboard
```

The speaker identification module does **not** need to generate the
transcript itself. It provides the audio segment and speaker metadata to
the transcription service.

------------------------------------------------------------------------

## Output Contract

The speaker/audio pipeline should expose structured segment data:

``` json
{
  "segment_id": "seg_0042",
  "room_id": "ROOM123",
  "user_id": "u001",
  "speaker_name": "Princess",
  "confidence": 0.91,
  "audio_file": "chunk_0042.wav",
  "start_time": 12.4,
  "end_time": 15.8
}
```

After transcription:

``` json
{
  "segment_id": "seg_0042",
  "room_id": "ROOM123",
  "user_id": "u001",
  "speaker_name": "Princess",
  "confidence": 0.91,
  "audio_file": "chunk_0042.wav",
  "start_time": 12.4,
  "end_time": 15.8,
  "transcription_status": "completed",
  "transcript": "Let's begin the discussion."
}
```

------------------------------------------------------------------------

## Suggested API

``` text
POST /rooms
POST /rooms/{room_id}/join

POST /users/{user_id}/voice

WS   /rooms/{room_id}/audio

POST /audio/identify

GET  /rooms/{room_id}/transcript
GET  /rooms/{room_id}/history
```

Exact endpoints may be adapted to the existing implementation.

------------------------------------------------------------------------

## Dashboard

The DESI dashboard is designed around a live physical conversation.

### Main areas

-   Room status
-   Participant overview
-   Audio quality
-   Speaking time
-   Audio segments
-   Live speaker-aware transcript
-   Participant list
-   Speaker activity
-   Audio playback
-   Session history

### Transcript entry

Each transcript item should expose:

``` text
Timestamp
Speaker
Confidence
Transcript
Play original audio
```

If transcription has not completed:

``` text
Transcription pending
```

The system must never invent transcript content.

------------------------------------------------------------------------

## Session Continuity

A room remains active even when a participant disconnects.

When the participant rejoins:

``` text
Rejoin room
    ↓
Restore user identity
    ↓
Restore participant state
    ↓
Continue receiving live conversation
    ↓
Access previous session transcript/history
```

------------------------------------------------------------------------

## Privacy & Security

DESI should follow privacy-first principles:

-   Clearly indicate when audio capture is active.
-   Obtain participant consent before recording.
-   Protect stored speaker embeddings.
-   Restrict room/session access.
-   Avoid unnecessary permanent storage of raw voice recordings.
-   Provide appropriate data retention controls.
-   Support optional sensitive-information masking/redaction.

------------------------------------------------------------------------

## Project Scope

### In scope

-   Physical/in-person conversations
-   Multiple nearby participant devices
-   Room creation and joining
-   Voice enrollment
-   Speaker identification
-   Audio segmentation
-   Multi-device audio processing
-   Speaker attribution
-   Live transcription
-   Speaker-aware captions
-   Audio playback
-   Session history
-   Rejoining
-   Accessibility-focused dashboard

### Out of scope

-   Google Meet integration
-   Zoom integration
-   Microsoft Teams integration
-   Online meetings
-   Video conferencing
-   Browser meeting extensions
-   Remote participants

------------------------------------------------------------------------

## MVP

The minimum demonstrable version is:

``` text
Create Room
    ↓
Join via Code / QR
    ↓
Participant Name + Voice Enrollment
    ↓
Multiple Devices Capture Audio
    ↓
Speech Detection
    ↓
Speaker Identification
    ↓
Audio + Speaker Metadata
    ↓
Speech-to-Text
    ↓
Speaker-Aware Live Caption
    ↓
DESI Dashboard
```

### MVP success criteria

The system should demonstrate that:

1.  Multiple people can physically join one room.
2.  Each participant can enroll their voice.
3.  Multiple devices capture the same conversation.
4.  Speech segments are generated.
5.  Speakers can be identified.
6.  Identified audio is passed to transcription.
7.  Transcripts display the correct speaker.
8.  Each transcript can play its corresponding audio.
9.  Participants can leave and rejoin.
10. Previous session information remains available.

------------------------------------------------------------------------

## Development Principles

-   Keep speaker identification separate from transcription.
-   Keep audio and transcript segments linked.
-   Prefer real application data over mock data.
-   Do not hardcode dashboard statistics.
-   Do not generate fake transcript content.
-   Keep room state persistent.
-   Design APIs around clear data contracts.
-   Optimize for low-latency physical conversations.
-   Test with real-world noise and multiple speakers.

------------------------------------------------------------------------

## Project Structure

A possible structure:

``` text
desi/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── dashboard/
│   └── rooms/
│
├── backend/
│   ├── api/
│   ├── rooms/
│   ├── audio/
│   ├── speaker/
│   ├── transcription/
│   └── database/
│
├── models/
│   ├── speaker/
│   └── vad/
│
├── audio/
│   └── segments/
│
├── tests/
│
├── docs/
│
├── .env.example
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Team Module Separation

``` text
DESI
│
├── User / Authentication
│
├── Room Management
│
├── Audio Capture
│
├── Speaker Identification
│
├── Multi-Device Audio Processing
│
├── Transcription
│
├── Dashboard
│
└── AI Conversation Intelligence
```

### Speaker Identification Module

The speaker identification module is responsible for:

``` text
Voice Enrollment
      ↓
Speaker Embedding
      ↓
Incoming Audio
      ↓
Speaker Matching
      ↓
Name + User ID + Confidence
      ↓
Audio + Metadata
```

It is **not responsible for final transcription**.

------------------------------------------------------------------------

## Future Scope

Potential future improvements include:

-   Better overlapping-speech separation
-   Improved multilingual recognition
-   Offline/local inference
-   Advanced noise cancellation
-   More sophisticated multi-device source fusion
-   Speaker re-identification across sessions with explicit consent
-   AI-generated summaries and action items
-   Conversation Q&A
-   Enterprise/private deployment

------------------------------------------------------------------------

## License

Add the project's chosen license here before public release.

------------------------------------------------------------------------

## Status

**Project:** DESI --- Distributed Speech Intelligence\
**Focus:** Physical group conversations\
**Current priority:** Speaker-aware audio processing and live
transcription\
**Version:** MVP
