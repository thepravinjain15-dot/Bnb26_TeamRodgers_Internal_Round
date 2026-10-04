import sqlite3

DATABASE_NAME = "roundtable.db"


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_connection()

    # Conversation messages
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            device_id TEXT,
            text TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Rooms / Sessions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_at DATETIME
        )
    """)

    conn.commit()
    conn.close()


# =========================
# CONVERSATION FUNCTIONS
# =========================

def add_message(room_id, speaker, text, device_id=None):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO conversations
        (room_id, speaker, device_id, text)
        VALUES (?, ?, ?, ?)
        """,
        (room_id, speaker, device_id, text)
    )

    conn.commit()
    conn.close()


def get_messages(room_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT
            id,
            room_id,
            speaker,
            device_id,
            text,
            timestamp
        FROM conversations
        WHERE room_id = ?
        ORDER BY id ASC
        """,
        (room_id,)
    )

    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return messages


def search_messages(room_id, keyword):
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT
            id,
            room_id,
            speaker,
            device_id,
            text,
            timestamp
        FROM conversations
        WHERE room_id = ?
        AND text LIKE ?
        ORDER BY id ASC
        """,
        (room_id, f"%{keyword}%")
    )

    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return messages


# =========================
# SPEAKER FUNCTIONS
# =========================

def get_speaker_messages(room_id, speaker):
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT
            id,
            room_id,
            speaker,
            device_id,
            text,
            timestamp
        FROM conversations
        WHERE room_id = ?
        AND speaker = ?
        ORDER BY id ASC
        """,
        (room_id, speaker)
    )

    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return messages


def get_speakers(room_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT DISTINCT
            speaker,
            device_id
        FROM conversations
        WHERE room_id = ?
        ORDER BY speaker ASC
        """,
        (room_id,)
    )

    speakers = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return speakers


# =========================
# ROOM / SESSION FUNCTIONS
# =========================

def create_room(room_id, name):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO rooms (room_id, name)
        VALUES (?, ?)
        """,
        (room_id, name)
    )

    conn.commit()
    conn.close()


def get_rooms():
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT
            room_id,
            name,
            status,
            created_at,
            closed_at
        FROM rooms
        ORDER BY created_at DESC
        """
    )

    rooms = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return rooms


def get_room(room_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        SELECT
            room_id,
            name,
            status,
            created_at,
            closed_at
        FROM rooms
        WHERE room_id = ?
        """,
        (room_id,)
    )

    room = cursor.fetchone()

    conn.close()

    return dict(room) if room else None


def close_room(room_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE rooms
        SET
            status = 'closed',
            closed_at = CURRENT_TIMESTAMP
        WHERE room_id = ?
        """,
        (room_id,)
    )

    conn.commit()
    conn.close()