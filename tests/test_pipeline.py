from campusverse.db import init_db
from campusverse.pipeline import send_message, get_history, clear_chat
import campusverse.pipeline as pipeline

V = "a" * 32

class FakeBackend:
    def reply(self, character, user_text, context):
        assert context["integration"]["active_goals"]
        return "Doing alright. Just catching up on things."

def test_mock_pipeline(monkeypatch):
    init_db()
    clear_chat("naina", visitor_id=V)
    monkeypatch.setattr(pipeline, "get_backend", lambda: FakeBackend())
    answer = send_message("naina", "Hey, how are you?", visitor_id=V)
    assert answer
    history = get_history("naina", visitor_id=V)
    assert history[-2]["role"] == "user"
    assert history[-1]["role"] == "assistant"
    clear_chat("naina", visitor_id=V)
