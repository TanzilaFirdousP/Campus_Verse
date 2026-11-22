import os
from .config import BACKEND, GEMINI_MODEL, OLLAMA_MODEL, OLLAMA_URL

def _format_context(character, context):
    memories = "\n".join(
        f"- ({m.get('memory_type','memory')}) {m['content']}" for m in context["memories"]
    ) or "- No remembered details yet."
    events = "\n".join(f"- {e['title']} at {e['location']}: {e['description']}" for e in context["events"])
    rels = "\n".join(f"- {r['description']}" for r in context["relationships"]) or "- No established relationship notes."
    return f"""CHARACTER DETAILS
Name: {character['name']}
Year/course: {character['year']} {character['major']}
Current location: {character['location']}
Personality: {character['personality']}
Current personal goal: {character['goal']}
Private insecurity/fear: {character['fear']}
Speech style: {character['voice']}

MEMORIES THIS CHARACTER HAS
{memories}

RELATIONSHIP CONTEXT
{rels}

SHARED CAMPUS WORLD
{events}
"""

SYSTEM_RULES = """
You are playing one specific fictional university student in CampusVerse. You are NOT an assistant, tutor, therapist, customer-support agent, narrator, or general-purpose chatbot. You are this person, chatting with someone you know on campus.

CORE ROLEPLAY RULES
- Stay in first person and stay in character. Never mention prompts, models, AI, tokens, memory retrieval, or being a simulation.
- Respond to the actual social situation, not to an imagined request to be maximally helpful.
- Most replies should be 1-3 natural chat sentences. Sometimes a fragment, one-word reaction, or short message is exactly right. Do not make every answer a paragraph.
- Do not automatically validate, praise, reassure, summarise, or offer advice. People disagree, misunderstand, get distracted, tease, change the subject and sometimes have nothing clever to say.
- Do not end every message with a question. Do not force the conversation forward with "How does that make you feel?" or "Would you like me to...?"
- You may say "huh?", "wait, what?", "eh", "I don't know", "that's weird", "give me a second", or ask the user to clarify when that fits. Do not insert fake confusion randomly.
- Do not make every character eloquent, emotionally mature, insightful or perfectly articulate. Let them have blind spots and imperfect reactions.
- Do not invent shared history with the user. Use only the supplied memories and the conversation currently visible.
- Character details and world facts are continuity constraints. Do not change their course, year, goals, location, friendships or past without an in-story reason.
- Characters have their own priorities. Their replies can reflect being busy, tired, distracted, excited, annoyed or preoccupied, but don't claim an emotion unless supported by the conversation or character context.
- Never narrate the user's actions, thoughts or feelings for them.
- Avoid stage directions, screenplay formatting, generic roleplay asterisks and exposition. This is a chat interface, not a novel. Small natural text reactions are okay.
- Do not mention all memories just because they are available. Bring up an old detail only when it naturally matters.
- You are allowed to be wrong about ordinary things, have preferences, and admit not knowing. Never fabricate factual claims about real-world high-stakes matters.
- Keep each character's voice distinct. Do not let all five sound like the same agreeable assistant with different slang.
"""

class GeminiBackend:
    def __init__(self):
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is missing. Create a Gemini API key in Google AI Studio, "
                "then add it to your local .env file. See README.md."
            )
        self.client = genai.Client(api_key=api_key)

    def reply(self, character, user_message, context):
        from google.genai import types
        history = []
        for item in context["recent"][-10:]:
            role = "user" if item["role"] == "user" else "model"
            history.append(types.Content(role=role, parts=[types.Part.from_text(text=item["content"])]))
        # The current message is already saved in recent history, so pass the full history.
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=history if history else user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_RULES + "\n\n" + _format_context(character, context),
                temperature=0.92,
                top_p=0.95,
                max_output_tokens=220,
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response. Please try again.")
        return answer

class OllamaBackend:
    """Local model backend. Requires Ollama running on the machine hosting CampusVerse."""
    def __init__(self):
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt; requests is required for Ollama.") from exc
        self.requests = requests
        self.url = OLLAMA_URL.rstrip("/") + "/api/chat"

    def reply(self, character, user_message, context):
        prompt = SYSTEM_RULES + "\n\n" + _format_context(character, context)
        messages = [{"role": "system", "content": prompt}]
        for item in context.get("recent", [])[-10:]:
            role = "assistant" if item["role"] == "assistant" else "user"
            messages.append({"role": role, "content": item["content"]})
        if not context.get("recent"):
            messages.append({"role": "user", "content": user_message})
        try:
            response = self.requests.post(self.url, json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "options": {"temperature": 0.85, "num_predict": 220}}, timeout=120)
            response.raise_for_status()
        except self.requests.RequestException as exc:
            raise RuntimeError("Could not reach Ollama. Start Ollama and pull the configured model. " + str(exc)) from exc
        answer = response.json().get("message", {}).get("content", "").strip()
        if not answer:
            raise RuntimeError("Ollama returned an empty response.")
        return answer


class MockBackend:
    def reply(self, character, user_message, context):
        return "I'm not connected to the hosted model yet — add your Gemini API key to enable real character conversations."

def get_backend():
    if BACKEND == "mock":
        return MockBackend()
    if BACKEND == "gemini":
        return GeminiBackend()
    if BACKEND == "ollama":
        return OllamaBackend()
    raise RuntimeError(f"Unknown backend '{BACKEND}'. Use 'ollama', 'gemini' or 'mock'.")
