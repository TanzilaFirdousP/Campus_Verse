"""P-FIT-inspired information integration layer (an engineering analogy, not a literal brain model)."""
from .memory import build_context
from .db import get_character

class PfitContextIntegrator:
    """Integrates distributed sources before generation: recent context, memories, goals, world, state."""
    def assemble(self, character_id, user_message, *, visitor_id):
        character = get_character(character_id)
        if not character:
            raise ValueError(f"Unknown character: {character_id}")
        context = build_context(character_id, user_message, visitor_id=visitor_id)
        active_goals = [g for g in context["goals"] if g["status"] == "active"]
        context["integration"] = {
            "character_identity": {k: character.get(k) for k in ("name", "personality", "year", "major", "location", "voice")},
            "active_goals": active_goals,
            "current_state": context["state"],
            "working_context": context["short_term_memory"],
            "retrieved_long_term": context["long_term_memory"],
            "social_context": context["relationships"],
            "shared_world": context["events"],
        }
        return character, context
