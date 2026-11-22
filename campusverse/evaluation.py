"""Transparent, lightweight checks; these are indicators, not proof of correctness."""
import re

def evaluate_response(character, answer, context):
    text = (answer or "").strip()
    memories = context.get("long_term_memory", context.get("memories", []))
    goals = context.get("goals", [])
    active_goals = [g["goal"] for g in goals if g.get("status") == "active"]
    return {
        "non_empty": bool(text),
        "reasonable_length": len(text) <= 1200,
        "identity_context_supplied": bool(character.get("personality")),
        "memory_context_supplied": bool(memories),
        "goal_context_supplied": bool(active_goals),
        "rule_compliance": not bool(re.search(r"\b(as an AI|language model|system prompt)\b", text, re.I)),
        "checks_note": "Context-presence checks do not prove the response used the information correctly; human review is still required.",
    }
