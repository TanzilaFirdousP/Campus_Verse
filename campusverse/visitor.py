"""Visitor identity: decides which private data set a browser session works with.

A visitor id is a random 32-character hex string (128 bits), so ids cannot be guessed.
This is a privacy boundary for a prototype, NOT authentication: anyone holding the
personal link (it carries ?v=<id>) can open that visitor's chats.
"""
import re
import uuid

_VALID = re.compile(r"[0-9a-f]{32}")


def is_valid_visitor_id(value):
    return isinstance(value, str) and _VALID.fullmatch(value) is not None


def new_visitor_id():
    return uuid.uuid4().hex


def resolve_visitor_id(query_value=None, session_value=None, single_user_id=""):
    """Pick the visitor id for this run.

    - single_user_id (from local config) wins: one fixed id for a private local install.
    - otherwise a valid id from the URL, then from the session, else a brand-new random id.
    - Anything that isn't a generated-looking id is ignored, so a visitor cannot type
      ?v=local to read the legacy local data.
    """
    if single_user_id:
        return single_user_id
    for candidate in (query_value, session_value):
        if is_valid_visitor_id(candidate):
            return candidate
    return new_visitor_id()
