import sqlite3
from .config import DB_PATH
from .baseline import CHARACTERS, LOCATIONS, RELATIONSHIPS, EVENTS

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS characters (
          id TEXT PRIMARY KEY, name TEXT, emoji TEXT, archetype TEXT, year TEXT, major TEXT,
          location TEXT, bio TEXT, personality TEXT, goal TEXT, fear TEXT, voice TEXT);
        CREATE TABLE IF NOT EXISTS locations (name TEXT PRIMARY KEY, emoji TEXT, description TEXT);
        CREATE TABLE IF NOT EXISTS relationships (
          id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT, description TEXT, UNIQUE(a,b));
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, role TEXT, content TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS memories (
          id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, content TEXT,
          kind TEXT DEFAULT 'personal', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, description TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS character_state (
          character_id TEXT PRIMARY KEY, mood TEXT DEFAULT 'neutral', focus TEXT DEFAULT '',
          current_activity TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS character_goals (
          id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, goal TEXT, status TEXT DEFAULT 'active',
          progress_note TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        # Add structured-memory fields safely to databases created by earlier versions.
        columns = {r["name"] for r in c.execute("PRAGMA table_info(memories)").fetchall()}
        if "layer" not in columns:
            c.execute("ALTER TABLE memories ADD COLUMN layer TEXT DEFAULT 'long_term'")
        if "memory_type" not in columns:
            c.execute("ALTER TABLE memories ADD COLUMN memory_type TEXT DEFAULT 'episodic'")
        if "importance" not in columns:
            c.execute("ALTER TABLE memories ADD COLUMN importance INTEGER DEFAULT 2")
        if "keywords" not in columns:
            c.execute("ALTER TABLE memories ADD COLUMN keywords TEXT DEFAULT ''")

        if c.execute("SELECT COUNT(*) FROM characters").fetchone()[0] == 0:
            for x in CHARACTERS:
                c.execute("""INSERT INTO characters VALUES
                (:id,:name,:emoji,:archetype,:year,:major,:location,:bio,:personality,:goal,:fear,:voice)""", x)
        else:
            # Refresh descriptive fields while preserving the user's location changes.
            for x in CHARACTERS:
                c.execute("""UPDATE characters SET personality=?,goal=?,fear=?,voice=?,bio=?
                WHERE id=?""", (x["personality"],x["goal"],x["fear"],x["voice"],x["bio"],x["id"]))
        if c.execute("SELECT COUNT(*) FROM locations").fetchone()[0] == 0:
            c.executemany("INSERT INTO locations VALUES (:name,:emoji,:description)", LOCATIONS)
        if c.execute("SELECT COUNT(*) FROM relationships").fetchone()[0] == 0:
            c.executemany("INSERT INTO relationships(a,b,description) VALUES (?,?,?)", RELATIONSHIPS)
        if c.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
            c.executemany("INSERT INTO events(title,location,description) VALUES (:title,:location,:description)", EVENTS)

    ensure_character_goals()

def get_characters():
    with connect() as c: return [dict(x) for x in c.execute("SELECT * FROM characters ORDER BY name")]
def get_character(cid):
    with connect() as c:
        x = c.execute("SELECT * FROM characters WHERE id=?", (cid,)).fetchone()
        return dict(x) if x else None
def get_locations():
    with connect() as c: return [dict(x) for x in c.execute("SELECT * FROM locations")]
def get_events():
    with connect() as c: return [dict(x) for x in c.execute("SELECT * FROM events ORDER BY id DESC")]
def move_character(cid, location):
    with connect() as c: c.execute("UPDATE characters SET location=? WHERE id=?", (location,cid))
def add_message(cid, role, content):
    with connect() as c: c.execute("INSERT INTO messages(character_id,role,content) VALUES (?,?,?)", (cid,role,content))
def get_messages(cid, limit=100):
    with connect() as c:
        rows = c.execute("SELECT role,content,created_at FROM messages WHERE character_id=? ORDER BY id DESC LIMIT ?",(cid,limit)).fetchall()
    return [dict(x) for x in reversed(rows)]
def clear_messages(cid):
    with connect() as c:
        c.execute("DELETE FROM messages WHERE character_id=?", (cid,))
        c.execute("DELETE FROM memories WHERE character_id=?", (cid,))
def add_memory(cid, content, kind="personal", memory_type="episodic", importance=2, keywords="", layer="long_term"):
    with connect() as c:
        c.execute("""INSERT INTO memories(character_id,content,kind,memory_type,importance,keywords,layer)
        VALUES (?,?,?,?,?,?,?)""",(cid,content,kind,memory_type,importance,keywords,layer))
def get_memories(cid):
    with connect() as c:
        rows = c.execute("""SELECT content,kind,memory_type,importance,keywords,layer,created_at
        FROM memories WHERE character_id=? OR kind='shared' ORDER BY id DESC""",(cid,)).fetchall()
    return [dict(x) for x in rows]
def get_relationships(cid):
    with connect() as c:
        rows = c.execute("SELECT a,b,description FROM relationships WHERE a=? OR b=?",(cid,cid)).fetchall()
    return [dict(x) for x in rows]


def get_character_state(cid):
    with connect() as c:
        row = c.execute("SELECT * FROM character_state WHERE character_id=?", (cid,)).fetchone()
    return dict(row) if row else {"character_id": cid, "mood": "neutral", "focus": "", "current_activity": ""}

def update_character_state(cid, mood=None, focus=None, current_activity=None):
    old = get_character_state(cid)
    with connect() as c:
        c.execute("""INSERT OR REPLACE INTO character_state
        (character_id,mood,focus,current_activity,updated_at) VALUES (?,?,?,?,CURRENT_TIMESTAMP)""",
        (cid, mood if mood is not None else old["mood"], focus if focus is not None else old["focus"],
         current_activity if current_activity is not None else old["current_activity"]))

def ensure_character_goals():
    with connect() as c:
        for x in CHARACTERS:
            exists = c.execute("SELECT 1 FROM character_goals WHERE character_id=?", (x["id"],)).fetchone()
            if not exists:
                c.execute("INSERT INTO character_goals(character_id,goal) VALUES (?,?)", (x["id"], x["goal"]))

def get_character_goals(cid):
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM character_goals WHERE character_id=? ORDER BY id", (cid,))]
