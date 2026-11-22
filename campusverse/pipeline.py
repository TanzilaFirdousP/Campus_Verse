from .db import add_message, get_messages, clear_messages
from .pfit import PfitContextIntegrator
from .memory import remember_exchange
from .llm import get_backend
from .evaluation import evaluate_response

_integrator = PfitContextIntegrator()

def send_message(cid, user_text):
    add_message(cid, "user", user_text)
    character, context = _integrator.assemble(cid, user_text)
    try:
        answer = get_backend().reply(character, user_text, context)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc
    checks = evaluate_response(character, answer, context)
    add_message(cid, "assistant", answer)
    remember_exchange(cid, user_text, answer)
    return answer

def get_history(cid): return get_messages(cid)
def clear_chat(cid): clear_messages(cid)
