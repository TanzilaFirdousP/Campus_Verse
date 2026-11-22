from campusverse.db import init_db, get_characters, get_locations, add_message, get_messages, clear_messages

V = "a" * 32

def test_seed_data():
    init_db()
    assert len(get_characters()) == 5
    assert {x["name"] for x in get_locations()} == {"Library","Cafeteria","Courtyard"}

def test_messages_persist():
    init_db()
    add_message("aarav","user","test message", visitor_id=V)
    assert get_messages("aarav", visitor_id=V)[-1]["content"] == "test message"
    clear_messages("aarav", visitor_id=V)
