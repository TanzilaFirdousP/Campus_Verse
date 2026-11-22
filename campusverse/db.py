import sqlite3
from .config import DB_PATH
from .baseline import CHARACTERS, LOCATIONS, RELATIONSHIPS, EVENTS

# Per-visitor data (chats, memories, state, goals) is always tagged with a visitor id so that
# different people using the same deployment never see each other's data. The campus world
# (characters, locations, relationships, events, kind='shared' memories) is common to everyone.
LEGACY_VISITOR = "local"

CHARACTER_STATE_SQL = """CREATE TABLE IF NOT EXISTS character_state (
  character_id TEXT, visitor_id TEXT NOT NULL DEFAULT 'local', mood TEXT DEFAULT 'neutral',
  focus TEXT DEFAULT '', current_activity TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (character_id, visitor_id))"""

def _need(visitor_id):
    if not isinstance(visitor_id, str) or not visitor_id.strip():
        raise ValueError("visitor_id is required: per-visitor data must never be read or written without it")
    return visitor_id

def _columns(c, table):
    return {r["name"] for r in c.execute(f"PRAGMA table_info({table})")}

def _migrate_visitor_columns(c):
    """Upgrade databases created before visitor separation. Old rows become visitor 'local'."""
    for table in ("messages", "memories", "character_goals"):
        if "visitor_id" not in _columns(c, table):
            c.execute(f"ALTER TABLE {table} ADD COLUMN visitor_id TEXT NOT NULL DEFAULT 'local'")
    if "visitor_id" not in _columns(c, "character_state"):
        # The primary key must change, which SQLite can only do by rebuilding the table.
        c.execute("ALTER TABLE character_state RENAME TO character_state_old")
        c.execute(CHARACTER_STATE_SQL)
        c.execute("""INSERT INTO character_state(character_id,visitor_id,mood,focus,current_activity,updated_at)
                     SELECT character_id,'local',mood,focus,current_activity,updated_at FROM character_state_old""")
        c.execute("DROP TABLE character_state_old")
    c.execute("CREATE INDEX IF NOT EXISTS idx_messages_visitor ON messages(visitor_id, character_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_memories_visitor ON memories(visitor_id, character_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_goals_visitor ON character_goals(visitor_id, character_id)")

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
          created_at TEXT DEFAULT CURRENT_TIMESTAMP, visitor_id TEXT NOT NULL DEFAULT 'local');
        CREATE TABLE IF NOT EXISTS memories (
          id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, content TEXT,
          kind TEXT DEFAULT 'personal', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          visitor_id TEXT NOT NULL DEFAULT 'local');
        CREATE TABLE IF NOT EXISTS events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, description TEXT,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS character_goals (
          id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, goal TEXT, status TEXT DEFAULT 'active',
          progress_note TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          visitor_id TEXT NOT NULL DEFAULT 'local');
        """)
        c.execute(CHARACTER_STATE_SQL)
        _migrate_visitor_columns(c)
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
def add_message(cid, role, content, *, visitor_id):
    _need(visitor_id)
    with connect() as c:
        c.execute("INSERT INTO messages(character_id,visitor_id,role,content) VALUES (?,?,?,?)",
                  (cid, visitor_id, role, content))
def get_messages(cid, limit=100, *, visitor_id):
    _need(visitor_id)
    with connect() as c:
        rows = c.execute("SELECT role,content,created_at FROM messages WHERE character_id=? AND visitor_id=? ORDER BY id DESC LIMIT ?",
                         (cid, visitor_id, limit)).fetchall()
    return [dict(x) for x in reversed(rows)]
def clear_messages(cid, *, visitor_id):
    """Delete this visitor's chat history with one character. Long-term memories are deliberately kept."""
    _need(visitor_id)
    with connect() as c:
        c.execute("DELETE FROM messages WHERE character_id=? AND visitor_id=?", (cid, visitor_id))

def clear_memories(cid, *, visitor_id):
    """Explicitly forget this visitor's memories of one character. Shared world memories are not touched."""
    _need(visitor_id)
    with connect() as c:
        c.execute("DELETE FROM memories WHERE character_id=? AND visitor_id=? AND kind != 'shared'", (cid, visitor_id))
def add_memory(cid, content, kind="personal", memory_type="episodic", importance=2, keywords="", layer="long_term", *, visitor_id):
    _need(visitor_id)
    with connect() as c:
        c.execute("""INSERT INTO memories(character_id,visitor_id,content,kind,memory_type,importance,keywords,layer)
        VALUES (?,?,?,?,?,?,?,?)""", (cid, visitor_id, content, kind, memory_type, importance, keywords, layer))
def get_memories(cid, *, visitor_id):
    """This visitor's memories for this character, plus world-level kind='shared' memories."""
    _need(visitor_id)
    with connect() as c:
        rows = c.execute("""SELECT content,kind,memory_type,importance,keywords,layer,created_at
        FROM memories WHERE (character_id=? AND visitor_id=?) OR kind='shared' ORDER BY id DESC""",
                         (cid, visitor_id)).fetchall()
    return [dict(x) for x in rows]
def get_relationships(cid):
    with connect() as c:
        rows = c.execute("SELECT a,b,description FROM relationships WHERE a=? OR b=?",(cid,cid)).fetchall()
    return [dict(x) for x in rows]


def get_character_state(cid, *, visitor_id):
    _need(visitor_id)
    with connect() as c:
        row = c.execute("SELECT * FROM character_state WHERE character_id=? AND visitor_id=?", (cid, visitor_id)).fetchone()
    return dict(row) if row else {"character_id": cid, "visitor_id": visitor_id, "mood": "neutral", "focus": "", "current_activity": ""}

def update_character_state(cid, mood=None, focus=None, current_activity=None, *, visitor_id):
    old = get_character_state(cid, visitor_id=visitor_id)
    with connect() as c:
        c.execute("""INSERT OR REPLACE INTO character_state
        (character_id,visitor_id,mood,focus,current_activity,updated_at) VALUES (?,?,?,?,?,CURRENT_TIMESTAMP)""",
        (cid, visitor_id, mood if mood is not None else old["mood"], focus if focus is not None else old["focus"],
         current_activity if current_activity is not None else old["current_activity"]))

def ensure_character_goals(visitor_id, cid=None):
    """Give a visitor their own copy of each character's starting goal the first time it is needed."""
    _need(visitor_id)
    with connect() as c:
        for x in CHARACTERS:
            if cid is not None and x["id"] != cid:
                continue
            exists = c.execute("SELECT 1 FROM character_goals WHERE character_id=? AND visitor_id=?", (x["id"], visitor_id)).fetchone()
            if not exists:
                c.execute("INSERT INTO character_goals(character_id,visitor_id,goal) VALUES (?,?,?)", (x["id"], visitor_id, x["goal"]))

def get_character_goals(cid, *, visitor_id):
    ensure_character_goals(visitor_id, cid)
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT * FROM character_goals WHERE character_id=? AND visitor_id=? ORDER BY id", (cid, visitor_id))]
