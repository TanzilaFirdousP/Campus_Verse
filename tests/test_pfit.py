from campusverse.db import init_db
from campusverse.pfit import PfitContextIntegrator
from campusverse.evaluation import evaluate_response

V = "a" * 32

def test_integrator_assembles_distributed_context():
    init_db()
    character, context = PfitContextIntegrator().assemble("aarav", "What are you working on?", visitor_id=V)
    assert character["name"] == "Aarav Mehta"
    assert "short_term_memory" in context
    assert "long_term_memory" in context
    assert "active_goals" in context["integration"]
    assert "social_context" in context["integration"]
    assert context["integration"]["active_goals"]  # goals are created on first use for a new visitor

def test_evaluation_checks_are_transparent():
    init_db()
    character, context = PfitContextIntegrator().assemble("naina", "hey", visitor_id=V)
    result = evaluate_response(character, "No way, really?", context)
    assert result["non_empty"] is True
    assert result["identity_context_supplied"] is True
    assert "do not prove" in result["checks_note"]
