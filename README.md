# CampusVerse

A virtual campus with five fictional students and three locations. Built with Python, Streamlit and SQLite. The application uses a modular, **P-FIT-inspired information-integration pipeline** so character responses can be conditioned on recent context, persistent memories, goals, relationships and shared campus events.

## Local setup

1. Install Python 3.10+ and Git.
2. Install Ollama from https://ollama.com on the computer that will run the app.
3. In PowerShell, from the project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
ollama pull llama3.2:3b
Copy-Item .env.example .env
```

4. Keep Ollama running, then start CampusVerse:

```powershell
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. The model runs locally through Ollama; no API key is required. `llama3.2:3b` is a small starting model; teammates can change `OLLAMA_MODEL` in `.env` to another model they have pulled.

## Backend modes

- `CAMPUSVERSE_BACKEND=ollama` (default): local Ollama model.
- `CAMPUSVERSE_BACKEND=mock`: UI/database development without a model; not for final behaviour evaluation.
- `CAMPUSVERSE_BACKEND=gemini`: optional hosted provider; requires a private key in `.env`.

Never commit `.env`, API keys, or `data/campusverse.db`.

## Architecture and scope

Read [ARCHITECTURE_PFIT.md](ARCHITECTURE_PFIT.md) for the module-by-module design, memory layers, current limitations and evaluation plan. P-FIT is a human-intelligence theory; our software architecture is inspired by its information-integration idea, not an official software implementation of the theory.

## Tests

```powershell
python -m pytest -q
```

## Team workflow

Work on feature branches, not `main`:

```powershell
git switch feature/campusverse-mvp
git status
```

Commit only intended source files. Do not add `.env` or the SQLite database.
