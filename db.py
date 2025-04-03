

import aiosqlite
import datetime

DB_PATH = "mentalx.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                summary TEXT

            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_user_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                age INTEGER,
                sex TEXT,
                country TEXT,
                language TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        await db.commit()

        


# Create a new session
async def create_session(user_id: int, name: str) -> int:
    created_at = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO sessions (user_id, name, created_at)
            VALUES (?, ?, ?)
        """, (user_id, name, created_at))
        await db.commit()
        return cursor.lastrowid  # return new session_id

# Get all sessions for a user
async def get_sessions(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT id, name, summary
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        return await cursor.fetchall()


# Save message to session
async def save_message(user_id: int, session_id: int, message: str, response: str):
    timestamp = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO messages (session_id, user_id, message, response, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, user_id, message, response, timestamp))
        await db.commit()

# Get session message history
async def get_session_history(session_id: int, limit: int = 5):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT message, response FROM messages
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (session_id, limit))
        return await cursor.fetchall()

async def update_session_summary(session_id: int, summary: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE sessions
            SET summary = ?
            WHERE id = ?
        """, (summary, session_id))
        await db.commit()


async def add_user(tg_user_id: int, full_name: str = ""):
    created_at = datetime.datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (tg_user_id, full_name, created_at)
            VALUES (?, ?, ?)
        """, (tg_user_id, full_name, created_at))
        await db.commit()

async def update_user_field(tg_user_id: int, field: str, value):
    async with aiosqlite.connect(DB_PATH) as db:
        query = f"UPDATE users SET {field} = ? WHERE tg_user_id = ?"
        await db.execute(query, (value, tg_user_id))
        await db.commit()

async def get_user_lang(user_id: int) -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT language FROM users WHERE tg_user_id = ?", (user_id,))
        row = await cursor.fetchone()
        return row[0] if row else "ru"

