"""Different visitors must never see each other's chats, memories, state or goals."""
import sqlite3
import pytest
from campusverse import db
from campusverse.db import (init_db, add_message, get_messages, add_memory, get_memories,
                            get_character_state, update_character_state, get_character_goals,
                            clear_messages, clear_memories)
from campusverse.memory import remember_exchange, retrieve_long_term, build_context
from campusverse.pipeline import send_message
import campusverse.pipeline as pipeline

A = "a" * 32
B = "b" * 32


def test_messages_are_private_per_visitor():
    init_db()
    add_message("aarav", "user", "visitor A secret", visitor_id=A)
    assert [m["content"] for m in get_messages("aarav", visitor_id=A)] == ["visitor A secret"]
    assert get_messages("aarav", visitor_id=B) == []


def test_memories_are_private_per_visitor():
    init_db()
    add_memory("naina", "A's sister is called Riya", visitor_id=A)
    assert len(get_memories("naina", visitor_id=A)) == 1
    assert get_memories("naina", visitor_id=B) == []
    assert retrieve_long_term("naina", "sister Riya", visitor_id=B) == []


def test_shared_world_memories_are_visible_to_everyone():
    init_db()
    add_memory("naina", "The fest is on Friday", kind="shared", visitor_id=A)
    assert [m["content"] for m in get_memories("naina", visitor_id=B)] == ["The fest is on Friday"]


def test_remember_exchange_saves_only_for_that_visitor():
    init_db()
    remember_exchange("aarav", "I prefer studying in the quiet corner upstairs every night", visitor_id=A)
    assert len(get_memories("aarav", visitor_id=A)) == 1
    assert get_memories("aarav", visitor_id=B) == []


def test_character_state_is_per_visitor():
    init_db()
    update_character_state("aarav", mood="stressed", visitor_id=A)
    assert get_character_state("aarav", visitor_id=A)["mood"] == "stressed"
    assert get_character_state("aarav", visitor_id=B)["mood"] == "neutral"
    update_character_state("aarav", mood="happy", visitor_id=B)
    assert get_character_state("aarav", visitor_id=A)["mood"] == "stressed"


def test_each_visitor_gets_their_own_goals():
    init_db()
    goals_a = get_character_goals("aarav", visitor_id=A)
    goals_b = get_character_goals("aarav", visitor_id=B)
    assert goals_a and goals_b
    assert goals_a[0]["id"] != goals_b[0]["id"]
    assert len(get_character_goals("aarav", visitor_id=A)) == len(goals_a)  # not re-seeded on every read


def test_clearing_affects_only_that_visitor():
    init_db()
    for v in (A, B):
        add_message("aarav", "user", f"hi from {v[0]}", visitor_id=v)
        add_memory("aarav", f"fact {v[0]}", visitor_id=v)
    clear_messages("aarav", visitor_id=A)
    clear_memories("aarav", visitor_id=A)
    assert get_messages("aarav", visitor_id=A) == [] and get_memories("aarav", visitor_id=A) == []
    assert len(get_messages("aarav", visitor_id=B)) == 1 and len(get_memories("aarav", visitor_id=B)) == 1


def test_full_pipeline_context_never_contains_another_visitors_data(monkeypatch):
    init_db()
    seen = {}

    class Spy:
        def reply(self, character, user_text, context):
            seen["context"] = context
            return "ok"

    monkeypatch.setattr(pipeline, "get_backend", lambda: Spy())
    send_message("aarav", "I prefer studying in the quiet corner upstairs every night", visitor_id=A)
    send_message("aarav", "Where should I study tonight?", visitor_id=B)
    flat = repr(seen["context"])
    assert "quiet corner" not in flat


def test_visitor_id_is_mandatory():
    init_db()
    with pytest.raises(TypeError):
        add_message("aarav", "user", "x")            # forgetting it is an error, not a silent shared bucket
    with pytest.raises(TypeError):
        get_messages("aarav")
    for bad in ("", "   ", None):
        with pytest.raises(ValueError):
            get_messages("aarav", visitor_id=bad)
        with pytest.raises(ValueError):
            add_memory("aarav", "x", visitor_id=bad)


OLD_SCHEMA = """
CREATE TABLE characters (id TEXT PRIMARY KEY, name TEXT, emoji TEXT, archetype TEXT, year TEXT, major TEXT,
  location TEXT, bio TEXT, personality TEXT, goal TEXT, fear TEXT, voice TEXT);
CREATE TABLE locations (name TEXT PRIMARY KEY, emoji TEXT, description TEXT);
CREATE TABLE relationships (id INTEGER PRIMARY KEY AUTOINCREMENT, a TEXT, b TEXT, description TEXT, UNIQUE(a,b));
CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, role TEXT, content TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE memories (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, content TEXT,
  kind TEXT DEFAULT 'personal', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  layer TEXT DEFAULT 'long_term', memory_type TEXT DEFAULT 'episodic', importance INTEGER DEFAULT 2, keywords TEXT DEFAULT '');
CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, location TEXT, description TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE character_state (character_id TEXT PRIMARY KEY, mood TEXT DEFAULT 'neutral', focus TEXT DEFAULT '',
  current_activity TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE character_goals (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id TEXT, goal TEXT, status TEXT DEFAULT 'active',
  progress_note TEXT DEFAULT '', updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
INSERT INTO messages(character_id,role,content) VALUES ('naina','user','old chat line');
INSERT INTO memories(character_id,content,memory_type) VALUES ('naina','The user said: I promised my sister a visit','commitment');
INSERT INTO character_state(character_id,mood,focus) VALUES ('naina','excited','the fest');
INSERT INTO character_goals(character_id,goal) VALUES ('naina','an old goal');
"""


def test_existing_database_is_migrated_to_the_legacy_local_visitor():
    conn = sqlite3.connect(db.DB_PATH)
    conn.executescript(OLD_SCHEMA)
    conn.commit(); conn.close()

    init_db()
    init_db()  # running the migration twice must be harmless

    assert [m["content"] for m in get_messages("naina", visitor_id="local")] == ["old chat line"]
    assert len(get_memories("naina", visitor_id="local")) == 1
    assert get_character_state("naina", visitor_id="local")["mood"] == "excited"
    assert get_character_goals("naina", visitor_id="local")[0]["goal"] == "an old goal"
    # ...and none of it is visible to a new visitor
    assert get_messages("naina", visitor_id=A) == []
    assert get_memories("naina", visitor_id=A) == []
    assert get_character_state("naina", visitor_id=A)["mood"] == "neutral"
    # the rebuilt state table now supports one row per (character, visitor)
    update_character_state("naina", mood="calm", visitor_id=A)
    assert get_character_state("naina", visitor_id="local")["mood"] == "excited"
