from .db import add_message, get_messages, clear_messages, clear_memories
from .pfit import PfitContextIntegrator
from .memory import remember_exchange
from .llm import get_backend
from .evaluation import evaluate_response

_integrator = PfitContextIntegrator()

def send_message(cid, user_text, *, visitor_id):
    add_message(cid, "user", user_text, visitor_id=visitor_id)
    character, context = _integrator.assemble(cid, user_text, visitor_id=visitor_id)
    try:
        answer = get_backend().reply(character, user_text, context)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    checks = evaluate_response(character, answer, context)
    add_message(cid, "assistant", answer, visitor_id=visitor_id)
    remember_exchange(cid, user_text, answer, visitor_id=visitor_id)
    return answer

def get_history(cid, *, visitor_id): return get_messages(cid, visitor_id=visitor_id)
def clear_chat(cid, *, visitor_id): clear_messages(cid, visitor_id=visitor_id)  # chat history only; memories survive
def clear_memory(cid, *, visitor_id): clear_memories(cid, visitor_id=visitor_id)  # explicit, separate action
