#!/usr/bin/env python3
"""Render only the LAST user question and Claude's answer from the current
Claude Code session transcript (JSONL) to Markdown on stdout.

Usage:
    last_response_to_md.py [SESSION_ID_OR_PATH]

If no arg is given, uses $CLAUDE_CODE_SESSION_ID. A session id is resolved by
globbing ~/.claude/projects/*/<id>.jsonl; a path ending in .jsonl is used
directly.

"Last question" = the last real user prose turn (tool results and the bare
slash-command trigger are ignored). "Answer" = every assistant text block that
follows it. Tool calls and thinking are omitted.

Self-check:  last_response_to_md.py --selfcheck
"""
import glob
import json
import os
import re
import sys


def find_transcript(arg):
    """Return the JSONL path for a session id, an explicit path, or None."""
    if arg and arg.endswith(".jsonl"):
        return arg if os.path.exists(arg) else None
    session_id = arg or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    matches = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session_id}.jsonl"))
    return matches[0] if matches else None


def _user_text(content):
    """Return the user's prose for an entry, or None if it carries no prose
    (a tool_result or a bare slash-command / skill trigger)."""
    if isinstance(content, str):
        body = content.strip()
        if not body or re.fullmatch(r"/[\w:.-]+", body):
            return None  # bare /command invocation, e.g. the trigger itself
        return body
    if isinstance(content, list):
        parts = [b.get("text", "").strip() for b in content
                 if isinstance(b, dict) and b.get("type") == "text"]
        joined = "\n".join(p for p in parts if p)
        return joined or None
    return None


def extract_last_qa(transcript_path):
    """Return (question, answer) for the final Q&A pair, or (None, None)."""
    question = None
    answer = []  # assistant text blocks accumulated since the last question
    with open(transcript_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = entry.get("type")
            if t not in ("user", "assistant"):
                continue
            content = (entry.get("message") or {}).get("content")

            if t == "user":
                prose = _user_text(content)
                if prose is not None:  # a real new question — start a fresh pair
                    question = prose
                    answer = []
            elif t == "assistant" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "text":
                        txt = b.get("text", "").strip()
                        if txt:
                            answer.append(txt)
    return question, ("\n\n".join(answer) or None)


def render(transcript_path):
    question, answer = extract_last_qa(transcript_path)
    if question is None:
        return None
    out = ["## \U0001F464 Question\n", question]
    out.append("\n## \U0001F916 Answer\n")
    out.append(answer or "_(no answer captured)_")
    return "\n".join(out).strip() + "\n"


def _selfcheck():
    import tempfile

    sample = [
        {"type": "user", "message": {"role": "user", "content": "First question."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "First answer."},
        ]}},
        {"type": "user", "message": {"role": "user", "content": "Second question."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "ponder"},
            {"type": "text", "text": "Part one."},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
        ]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": [{"type": "text", "text": "file.py"}]},
        ]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Part two."},
        ]}},
        {"type": "user", "message": {"role": "user", "content": "/response-capture:response-capture"}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for row in sample:
            f.write(json.dumps(row) + "\n")
        path = f.name
    md = render(path)
    os.unlink(path)

    # Only the LAST question survives; the first pair is gone.
    assert "Second question." in md, "missing last question"
    assert "First question." not in md and "First answer." not in md, "earlier pair leaked"
    # A tool_result between answer chunks must not reset the pair.
    assert "Part one." in md and "Part two." in md, "tool_result split the answer"
    # Tools / thinking omitted; the bare trigger is not treated as the question.
    assert "Bash" not in md and "ponder" not in md, "noise leaked"
    assert "/response-capture" not in md, "trigger treated as question"
    print("selfcheck OK")


def main(argv):
    if argv[1:2] == ["--selfcheck"]:
        _selfcheck()
        return 0
    path = find_transcript(argv[1] if len(argv) > 1 else None)
    if not path:
        sys.stderr.write(
            "transcript not found: set $CLAUDE_CODE_SESSION_ID or pass a session id / .jsonl path\n"
        )
        return 1
    md = render(path)
    if md is None:
        sys.stderr.write("no user question found in this session yet\n")
        return 1
    sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
