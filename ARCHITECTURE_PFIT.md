# CampusVerse architecture: P-FIT-inspired information integration

## Important terminology
CampusVerse uses **design principles inspired by the Parieto-Frontal Integration Theory (P-FIT)**. P-FIT is a theory of human intelligence, not a software framework with an official set of coding modules. The modules below are our engineering interpretation of the project's stated goal: integrate distributed information (memory, current context, goals and world state) before selecting a response.

## Runtime pipeline

1. **Input / perception** (`pipeline.py`): receives the user's message and identifies the active character.
2. **Short-term / working context** (`memory.py`): the most recent 10 messages for the active conversation. This is transient context, not permanent memory.
3. **Long-term memory retrieval** (`memory.py`): retrieves relevant persistent facts, preferences, commitments and notable episodes from SQLite using keyword relevance, importance and recency. This is currently a transparent baseline retriever, not embeddings/semantic search.
4. **Information integration** (`pfit.py`): combines identity/personality, recent conversation, retrieved long-term memories, active goals, relationship context, character state and shared campus events into one structured context.
5. **Goal and constraint conditioning** (`llm.py`): passes the integrated context and character-specific behaviour rules to the local language model.
6. **Response checks** (`evaluation.py`): records simple checks for non-empty output, length, supplied identity/memory/goal context and obvious out-of-character AI meta-language. These are proxy indicators, not a guarantee of factual consistency.
7. **Persistence** (`db.py`): stores conversation history and durable memories in SQLite.

## Current implementation vs next work

| Area | Current state | Next meaningful upgrade |
|---|---|---|
| Short-term memory | Last 10 messages | Token-budgeted working memory / session summary |
| Long-term memory | Persistent SQLite facts; keyword retrieval | Embeddings + semantic retrieval; deduplication and memory consolidation |
| Memory extraction | Rule-based stable-fact/commitment detection | Structured extraction with confidence, source, timestamp and user correction |
| Goals | Character goals stored as active records | Goal milestones, progress updates and goal-conflict reasoning |
| Character state | Persistent mood/focus/activity fields | Controlled state transitions based on events and interactions |
| Relationships | Static initial relationship descriptions | Interaction-driven relationship values and shared history |
| Shared world | Seed events | Event lifecycle and consequences across characters |
| Evaluation | Context-presence proxy checks | Scenario suite scoring memory accuracy, behavioural consistency, goal alignment and rule compliance |
| Model | Local Ollama backend | Model comparison; model is replaceable and not the memory system |

## How to demonstrate the research idea
Run the same scripted scenarios in two modes:
- **Baseline:** recent conversation only; do not inject retrieved long-term memories/goals/social context.
- **Integrated:** use the complete `PfitContextIntegrator` output.

Compare memory recall accuracy, consistency with earlier commitments, goal alignment and rule compliance. Keep prompts, model, temperature and test messages identical. Report the limitations and use human-labelled expected outcomes; the current automatic checks alone are not enough to claim improvement.

## Local model setup
Install Ollama on the machine that runs Streamlit, then run `ollama pull llama3.2:3b`. Keep Ollama running. Configure `.env` with `CAMPUSVERSE_BACKEND=ollama`. A teammate without a local model can use `CAMPUSVERSE_BACKEND=mock` for UI/database development, but mock mode is not a valid conversational evaluation.
