from campusverse.db import init_db, add_memory
from campusverse.memory import retrieve_memories

def test_relevant_memory_retrieval():
    init_db()
    add_memory("aarav", "The user prefers quiet places to study", memory_type="preference", importance=4, keywords="quiet places study")
    add_memory("aarav", "The user likes mango ice cream", memory_type="preference", importance=3, keywords="mango ice cream")
    results = retrieve_memories("aarav", "I need somewhere quiet to study", limit=5)
    assert results
    assert "quiet" in results[0]["content"].lower()
