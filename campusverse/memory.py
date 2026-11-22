"""Two-tier memory: short-term conversational window + persistent long-term facts."""
import re
from .config import RECENT_MESSAGES, RELEVANT_MEMORIES
from .db import (get_messages, get_memories, get_events, get_relationships, add_memory,
                 get_character_state, get_character_goals)

STOP = {"this","that","with","from","have","your","about","there","what","when","where","which","would","could","should","just","really","like","they","them","then","than","into","been","were","will","does","dont","didnt","it's","that's","im","ive","you","are","was","and","the","for","but","not"}
def terms(text):
    return {w.lower() for w in re.findall(r"[a-zA-Z']{3,}", text or "") if w.lower() not in STOP}
def _score(memory, q):
    overlap = len(q & terms(memory["content"] + " " + (memory.get("keywords") or "")))
    stable = 2 if memory.get("memory_type") in {"preference", "identity", "ongoing", "commitment"} else 0
    return overlap * 3 + int(memory.get("importance") or 2) * .5 + stable

def retrieve_long_term(cid, query="", limit=RELEVANT_MEMORIES, *, visitor_id):
    memories = get_memories(cid, visitor_id=visitor_id)
    q = terms(query)
    ranked = sorted(memories, key=lambda m: (_score(m, q), m["created_at"]), reverse=True)
    relevant = [m for m in ranked if not q or _score(m, q) > 1.5]
    return relevant[:limit]

def build_context(cid, user_message="", *, visitor_id):
    # STM: the live conversation window. It is not copied into durable memory.
    stm = get_messages(cid, RECENT_MESSAGES, visitor_id=visitor_id)
    ltm = retrieve_long_term(cid, user_message, visitor_id=visitor_id)
    return {
        "recent": stm, "short_term_memory": stm, "memories": ltm,
        "long_term_memory": ltm, "events": get_events()[:5],
        "relationships": get_relationships(cid), "state": get_character_state(cid, visitor_id=visitor_id),
        "goals": get_character_goals(cid, visitor_id=visitor_id),
    }

def get_context_preview(cid, *, visitor_id):
    ctx = build_context(cid, visitor_id=visitor_id)
    return {"Short-term memory": [f"{m['role']}: {m['content']}" for m in ctx["recent"][-4:]],
            "Long-term memory": [f"[{m['memory_type']}] {m['content']}" for m in ctx["memories"]],
            "Active goals": [g["goal"] for g in ctx["goals"] if g["status"] == "active"],
            "Campus events": [e["title"] for e in ctx["events"]],
            "Relationships": [r["description"] for r in ctx["relationships"]]}

def remember_exchange(cid, user_text, assistant_text="", *, visitor_id):
    text = (user_text or "").strip()
    if len(text) < 12: return
    low = text.lower()
    patterns = [r"\bi am\b", r"\bi'm\b", r"\bi study\b", r"\bmy name\b", r"\bi work\b", r"\bi have\b", r"\bi don't like\b", r"\bi hate\b", r"\bi love\b", r"\bi prefer\b", r"\bi want\b", r"\bi'm trying\b", r"\bi always\b", r"\bi usually\b", r"\bi promised\b", r"\bi need to\b"]
    stable = any(re.search(p, low) for p in patterns)
    if not stable and len(text) < 65: return
    mtype = "preference" if any(x in low for x in ["i like", "i love", "i hate", "i prefer", "i don't like"]) else ("commitment" if any(x in low for x in ["i promised", "i need to", "i will", "i'm going to"]) else ("identity" if stable else "episodic"))
    norm = re.sub(r"\W+", "", low)
    if any(re.sub(r"\W+", "", m["content"].lower()).find(norm[:50]) >= 0 for m in get_memories(cid, visitor_id=visitor_id) if len(norm) >= 50): return
    add_memory(cid, f"The user said: {text[:600]}", memory_type=mtype,
               importance=5 if stable else 2, keywords=" ".join(sorted(terms(text))), layer="long_term", visitor_id=visitor_id)

# Backwards-compatible name used by the first MVP tests and earlier callers.
def retrieve_memories(cid, query="", limit=RELEVANT_MEMORIES, *, visitor_id):
    return retrieve_long_term(cid, query, limit, visitor_id=visitor_id)
