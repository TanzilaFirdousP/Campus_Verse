from campusverse.visitor import is_valid_visitor_id, new_visitor_id, resolve_visitor_id

GOOD = "0123456789abcdef" * 2


def test_new_ids_are_valid_and_unique():
    a, b = new_visitor_id(), new_visitor_id()
    assert is_valid_visitor_id(a) and is_valid_visitor_id(b) and a != b


def test_only_generated_looking_ids_are_accepted():
    for bad in ("local", "", None, 123, "../etc", GOOD.upper(), GOOD + "0", GOOD[:-1], GOOD[:-1] + "g", GOOD + "\n"):
        assert not is_valid_visitor_id(bad)


def test_cannot_impersonate_the_legacy_local_visitor_from_the_url():
    vid = resolve_visitor_id(query_value="local", session_value=None, single_user_id="")
    assert vid != "local" and is_valid_visitor_id(vid)


def test_resolution_order():
    other = "f" * 32
    assert resolve_visitor_id(GOOD, other) == GOOD            # URL first
    assert resolve_visitor_id(None, other) == other           # then session
    assert is_valid_visitor_id(resolve_visitor_id(None, None))  # else fresh
    assert resolve_visitor_id(GOOD, other, single_user_id="local") == "local"  # local mode wins
