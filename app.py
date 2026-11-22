import streamlit as st
from campusverse.db import init_db, get_characters, get_locations, get_events, move_character
from campusverse.pipeline import send_message, get_history
from campusverse.memory import get_context_preview

st.set_page_config(page_title="CampusVerse", page_icon="🎓", layout="wide")
init_db()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root { --forest:#203c32; --moss:#526d56; --sage:#dce6d7; --cream:#f7f1e5; --paper:#fffdf8; --ink:#26372e; --muted:#68746b; --rose:#d9a5a0; }
.stApp { background:var(--cream); color:var(--ink); }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
[data-testid="stSidebar"] { background:#e5eadf; border-right:1px solid #cbd5c6; }
[data-testid="stSidebar"] * { color:#26372e !important; }
h1,h2,h3 { color:var(--forest) !important; font-family:'Playfair Display',serif !important; }
p, label, .stMarkdown, [data-testid="stCaptionContainer"] { color:var(--ink); }
.stButton>button { background:var(--forest); color:#fff; border:0; border-radius:12px; font-weight:600; min-height:2.65rem; }
.stButton>button:hover { background:var(--moss); color:#fff; border:0; }
.stTextInput input, [data-testid="stChatInput"] textarea { background:#fffdf8 !important; color:#26372e !important; }
.hero { background:linear-gradient(115deg,#203c32,#49664f); color:#fff; padding:1.45rem 1.8rem; border-radius:20px; margin-bottom:1rem; box-shadow:0 8px 22px #203c3218; }
.hero h1 { color:#fff !important; font-size:2.5rem; margin:0; }
.hero p { color:#edf2e9 !important; margin:.35rem 0 0; }
.location-card { background:#fffdf8; border:1px solid #d8dfd3; border-radius:16px; padding:1rem; }
.person-card { background:#fffdf8; border:1px solid #d9dfd4; border-radius:16px; padding:1rem; min-height:150px; }
.portrait { background:linear-gradient(145deg,#dce6d7,#f4e5d9); border:1px solid #c8d5c6; border-radius:20px; min-height:340px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; padding:1rem; }
.portrait .emoji { font-size:7rem; line-height:1.2; }
.portrait h2 { margin:.7rem 0 .1rem; }
.dialogue-shell { background:#fffdf8; border:1px solid #ddd8cc; border-radius:18px; padding:1rem 1.2rem; }
.small-muted { color:#68746b; font-size:.9rem; }
.map-wrap { background:#e8eddf; border:1px solid #cbd7c6; border-radius:22px; padding:12px; box-shadow:0 8px 24px #203c3212; }
.map-wrap a { text-decoration:none; }
.stChatMessage { background:#fffdf8; border:1px solid #e6e0d5; border-radius:14px; }
</style>
""", unsafe_allow_html=True)

if "selected_character" not in st.session_state:
    st.session_state.selected_character = None

def home():
    st.query_params.clear()
    st.session_state.selected_character = None
    st.rerun()

def get_selected():
    cid = st.session_state.selected_character
    return next((x for x in get_characters() if x["id"] == cid), None)

with st.sidebar:
    st.markdown("## 🎓 CampusVerse")
    st.caption("A shared campus, five student lives.")
    if st.button("🗺️ Campus map", use_container_width=True):
        home()
    if st.button("🌱 Shared campus events", use_container_width=True):
        st.session_state.selected_character = None
        st.query_params["view"] = "events"
        st.rerun()
    st.divider()
    st.caption("Prototype build · Local SQLite")
    st.caption("Chats and memories are stored on this computer.")

selected = get_selected()
place = st.query_params.get("place")
view = st.query_params.get("view")

if selected:
    st.markdown(f"### {selected['emoji']} A conversation with {selected['name']}")
    if st.button("← Back to the campus"):
        home()
    left, right = st.columns([1, 2.15], gap="large")
    with left:
        st.markdown(f"""
        <div class="portrait">
          <div class="emoji">{selected['emoji']}</div>
          <h2>{selected['name']}</h2>
          <b>{selected['archetype']}</b>
          <div class="small-muted">{selected['year']} · {selected['major']}</div>
          <p style="margin-top:1rem">{selected['bio']}</p>
        </div>""", unsafe_allow_html=True)
        with st.expander("Character details & memory"):
            st.write("**What they're working toward:**", selected["goal"])
            st.write("**What they worry about:**", selected["fear"])
            st.json(get_context_preview(selected["id"]), expanded=False)
        with st.expander("🧠 P-FIT-inspired integration trace"):
            st.caption("The response pipeline combines separate information sources before generation.")
            st.markdown("1. **Input / perception** — current message + selected character")
            st.markdown("2. **Short-term memory** — recent conversation window")
            st.markdown("3. **Long-term memory** — relevant persistent facts and commitments")
            st.markdown("4. **Integration** — goals, character state, relationships and shared events")
            st.markdown("5. **Generation** — local Ollama model conditioned on integrated context")
            st.markdown("6. **Evaluation** — lightweight response checks; human evaluation still required")
            st.caption("P-FIT is the inspiration for information integration, not a literal software framework.")
    with right:
        st.markdown('<div class="dialogue-shell">', unsafe_allow_html=True)
        st.markdown(f"#### 💬 {selected['name'].split()[0]}")
        st.caption("You're chatting one-on-one. This conversation is saved.")
        for msg in get_history(selected["id"]):
            with st.chat_message(msg["role"], avatar=selected["emoji"] if msg["role"] == "assistant" else "🧑"):
                st.markdown(msg["content"])
        prompt = st.chat_input(f"Say something to {selected['name'].split()[0]}...")
        if prompt:
            try:
                with st.spinner(f"{selected['name'].split()[0]} is thinking..."):
                    send_message(selected["id"], prompt)
                st.rerun()
            except Exception as exc:
                st.error(f"The character couldn't reply: {exc}")
        st.markdown('</div>', unsafe_allow_html=True)

elif view == "events":
    st.markdown('<div class="hero"><h1>Campus noticeboard</h1><p>Little things happening around the shared campus.</p></div>', unsafe_allow_html=True)
    if st.button("← Back to map"): home()
    for event in get_events():
        st.markdown(f"""<div class="location-card"><h3>{event['title']}</h3>
        <b>📍 {event['location']}</b><p>{event['description']}</p></div>""", unsafe_allow_html=True)
        st.write("")

elif place:
    loc = next((x for x in get_locations() if x["name"] == place), None)
    if not loc:
        home()
    st.markdown(f'<div class="hero"><h1>{loc["emoji"]} {loc["name"]}</h1><p>{loc["description"]}</p></div>', unsafe_allow_html=True)
    if st.button("← Back to campus map"): home()
    here = [x for x in get_characters() if x["location"] == place]
    if not here:
        st.info("It's quiet here right now. You can move students to this location from their profile.")
    else:
        st.markdown("### Who would you like to talk to?")
        cols = st.columns(min(3, len(here)))
        for i, ch in enumerate(here):
            with cols[i % len(cols)]:
                st.markdown(f"""<div class="person-card">
                <div style="font-size:3.2rem">{ch['emoji']}</div>
                <h3>{ch['name']}</h3><b>{ch['archetype']}</b>
                <p class="small-muted">{ch['year']} · {ch['major']}</p>
                <p>{ch['bio']}</p></div>""", unsafe_allow_html=True)
                if st.button(f"Talk to {ch['name'].split()[0]} →", key=f"meet_{ch['id']}", use_container_width=True):
                    st.session_state.selected_character = ch["id"]
                    st.rerun()

else:
    st.markdown('<div class="hero"><h1>Welcome to CampusVerse</h1><p>Explore the campus, find your people, and see where a conversation takes you.</p></div>', unsafe_allow_html=True)
    st.markdown("### Choose where to go")
    st.caption("Tap one of the three places on the illustrated campus map.")
    # Inline SVG map: each landmark is an actual link back into the Streamlit app.
    map_html = """
    <div class="map-wrap">
    <svg viewBox="0 0 1000 570" width="100%" role="img" aria-label="Illustrated CampusVerse map">
      <defs>
        <pattern id="grass" width="38" height="38" patternUnits="userSpaceOnUse"><circle cx="7" cy="8" r="2" fill="#c7d8bb"/><circle cx="27" cy="25" r="1.7" fill="#c7d8bb"/></pattern>
        <filter id="shadow"><feDropShadow dx="0" dy="5" stdDeviation="5" flood-color="#344b38" flood-opacity=".18"/></filter>
      </defs>
      <rect x="0" y="0" width="1000" height="570" rx="24" fill="#dce8d2"/>
      <rect x="0" y="0" width="1000" height="570" rx="24" fill="url(#grass)"/>
      <path d="M-20 410 C180 320 220 510 430 390 S720 300 1030 420" stroke="#f8f0dc" stroke-width="72" fill="none" stroke-linecap="round"/>
      <path d="M220 -30 C300 140 460 170 500 300 S680 430 760 610" stroke="#f8f0dc" stroke-width="64" fill="none" stroke-linecap="round"/>
      <path d="M-20 410 C180 320 220 510 430 390 S720 300 1030 420" stroke="#d8cdb2" stroke-width="3" fill="none" stroke-dasharray="8 12"/>
      <path d="M220 -30 C300 140 460 170 500 300 S680 430 760 610" stroke="#d8cdb2" stroke-width="3" fill="none" stroke-dasharray="8 12"/>
      <!-- trees -->
      <g fill="#73936c" stroke="#557653" stroke-width="3">
        <circle cx="90" cy="100" r="31"/><circle cx="145" cy="150" r="24"/><circle cx="850" cy="90" r="34"/>
        <circle cx="920" cy="155" r="26"/><circle cx="115" cy="500" r="32"/><circle cx="900" cy="500" r="35"/>
        <circle cx="820" cy="300" r="23"/><circle cx="350" cy="75" r="22"/><circle cx="610" cy="80" r="25"/>
      </g>
      <g fill="#f2e8d5" stroke="#b9ad96" stroke-width="3" filter="url(#shadow)">
        <rect x="90" y="205" width="245" height="125" rx="16"/>
        <rect x="670" y="185" width="245" height="125" rx="16"/>
        <rect x="380" y="390" width="245" height="115" rx="16"/>
      </g>
      <g font-family="Arial" text-anchor="middle" fill="#284436">
        <text x="212" y="255" font-size="45">📚</text><text x="212" y="290" font-size="23" font-weight="bold">LIBRARY</text>
        <text x="792" y="235" font-size="45">☕</text><text x="792" y="270" font-size="23" font-weight="bold">CAFETERIA</text>
        <text x="502" y="435" font-size="45">🌳</text><text x="502" y="470" font-size="23" font-weight="bold">COURTYARD</text>
        <text x="500" y="45" font-size="18" fill="#60775b" letter-spacing="4">CAMPUSVERSE</text>
      </g>
      <a href="?place=Library"><rect x="90" y="205" width="245" height="125" rx="16" fill="#fff" opacity="0" /><title>Visit Library</title></a>
      <a href="?place=Cafeteria"><rect x="670" y="185" width="245" height="125" rx="16" fill="#fff" opacity="0"/><title>Visit Cafeteria</title></a>
      <a href="?place=Courtyard"><rect x="380" y="390" width="245" height="115" rx="16" fill="#fff" opacity="0"/><title>Visit Courtyard</title></a>
    </svg>
    </div>
    """
    st.markdown(map_html, unsafe_allow_html=True)
    st.caption("Tip: click a building on the map. You can return here whenever you want.")
    with st.expander("Campus directory"):
        for ch in get_characters():
            st.write(f"{ch['emoji']} **{ch['name']}** — {ch['location']}")
