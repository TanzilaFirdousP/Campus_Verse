# Campus_Verse

# CampusVerse

AI characters on a virtual campus that remember, interact and make decisions,
built with a four-stage pipeline inspired by P-FIT.

## Setup (once per person)

1. Clone the repo into a simple folder (not OneDrive):
   git clone <repo-url>
2. Open the folder in VS Code.
3. In the terminal:
   python -m venv venv
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   venv\Scripts\activate
   pip install -r requirements.txt
4. Install Ollama (ollama.com), then run: ollama pull llama3.2

## Daily workflow

1. git pull
2. git checkout -b feature/<your-task>
3. Work, then: git add . / git commit -m "message" / git push -u origin feature/<your-task>
4. Open a pull request on GitHub and ask a teammate to review it.
5. 
