from campusverse import db
from campusverse.config import DB_PATH as REAL_DB_PATH
from campusverse.db import (init_db, add_memory, get_memories, add_message, get_messages,
                            clear_messages, clear_memories)
from campusverse.pipeline import clear_chat, clear_memory

V = "a" * 32


def test_tests_never_use_the_real_database():
    assert db.DB_PATH != REAL_DB_PATH
    init_db()
    assert not REAL_DB_PATH.exists() or db.DB_PATH.exists()


def test_each_test_starts_with_no_leftover_memories():
    # Previously test_memory.py left memories in the real DB that leaked into later runs.
    init_db()
    assert get_memories("aarav", visitor_id=V) == []


def test_clear_messages_keeps_long_term_memory():
    init_db()
    add_memory("naina", "The user promised to visit her sister", memory_type="commitment", importance=5, visitor_id=V)
    add_message("naina", "user", "hi", visitor_id=V)
    clear_messages("naina", visitor_id=V)
    assert get_messages("naina", visitor_id=V) == []
    assert len(get_memories("naina", visitor_id=V)) == 1


def test_clear_chat_pipeline_keeps_memory():
    init_db()
    add_memory("naina", "The user likes chai", memory_type="preference", visitor_id=V)
    add_message("naina", "user", "hello", visitor_id=V)
    clear_chat("naina", visitor_id=V)
    assert get_messages("naina", visitor_id=V) == []
    assert len(get_memories("naina", visitor_id=V)) == 1


def test_clear_memories_only_forgets_that_character():
    init_db()
    add_memory("naina", "naina private fact", visitor_id=V)
    add_memory("aarav", "aarav private fact", visitor_id=V)
    clear_memories("naina", visitor_id=V)
    assert get_memories("naina", visitor_id=V) == []
    assert [m["content"] for m in get_memories("aarav", visitor_id=V)] == ["aarav private fact"]


def test_clear_memory_keeps_shared_memories():
    init_db()
    add_memory("naina", "campus-wide fact", kind="shared", visitor_id=V)
    add_memory("naina", "private fact", visitor_id=V)
    clear_memory("naina", visitor_id=V)
    contents = [m["content"] for m in get_memories("naina", visitor_id=V)]
    assert contents == ["campus-wide fact"]
