#!/usr/bin/env python3
"""Render the current Claude Code session transcript (JSONL) to Markdown on stdout.

Usage:
    transcript_to_md.py [SESSION_ID_OR_PATH]

If no arg is given, uses $CLAUDE_CODE_SESSION_ID. A session id is resolved by
globbing ~/.claude/projects/*/<id>.jsonl (robust against cwd-slug guessing); a
path ending in .jsonl is used directly.

By default only the conversation is rendered: user messages and Claude's text
replies. Set TRANSCRIPT_FULL=1 to also include thinking, tool calls, and tool
results (the verbose everything-mode).

Self-check:  transcript_to_md.py --selfcheck
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


def _textify(content):
    """Flatten a tool_result content field (str | list of blocks) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "image":
                    parts.append("[image]")
                else:
                    parts.append(json.dumps(b, ensure_ascii=False))
            else:
                parts.append(str(b))
        return "\n".join(parts)
    return json.dumps(content, ensure_ascii=False)


def _fence(text, lang=""):
    # Avoid breaking out of the code fence if the body contains ```.
    ticks = "```"
    while ticks in text:
        ticks += "`"
    return f"{ticks}{lang}\n{text}\n{ticks}"


def render(transcript_path, full=False):
    out = []
    last_speaker = None  # 'user' | 'assistant' — only emit an H2 on change

    def speaker(name, emoji, label):
        nonlocal last_speaker
        if last_speaker != name:
            out.append(f"\n## {emoji} {label}\n")
            last_speaker = name

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
                continue  # metadata lines (mode, attachment, ai-title, ...)
            if entry.get("isMeta"):
                continue  # system-injected turn, e.g. an expanded slash-command body
            content = (entry.get("message") or {}).get("content")

            if t == "user":
                if isinstance(content, str):
                    body = content.strip()
                    # Skip a bare slash-command / skill invocation (e.g. the
                    # /session-capture trigger itself); keep prose that merely mentions one.
                    if re.fullmatch(r"/[\w:.-]+", body):
                        continue
                    if "<command-name>" in body or "<command-message>" in body:
                        continue  # slash-command trigger wrapper (command with a prompt body)
                    speaker("user", "\U0001F464", "User")
                    out.append(body)
                elif isinstance(content, list):
                    for b in content:
                        if not isinstance(b, dict):
                            continue
                        bt = b.get("type")
                        if bt == "text":  # user prose attached to images/files
                            txt = b.get("text", "").strip()
                            if txt:
                                speaker("user", "\U0001F464", "User")
                                out.append(txt)
                        elif bt == "tool_result" and full:
                            body = _textify(b.get("content", "")).strip()
                            out.append("\n#### \U0001F4E4 Tool Result\n")
                            out.append(_fence(body) if body else "_(no output)_")
            elif t == "assistant" and isinstance(content, list):
                for b in content:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    if bt == "text":
                        speaker("assistant", "\U0001F916", "Assistant")
                        out.append(b.get("text", "").strip())
                    elif bt == "thinking" and full:
                        think = b.get("thinking", "").strip()
                        if think:
                            out.append(
                                "\n<details><summary>\U0001F4AD Thinking</summary>\n\n"
                                + think
                                + "\n\n</details>"
                            )
                    elif bt == "tool_use" and full:
                        name = b.get("name", "tool")
                        args = json.dumps(b.get("input", {}), indent=2, ensure_ascii=False)
                        out.append(f"\n#### \U0001F527 {name}\n")
                        out.append(_fence(args, "json"))
    return "\n".join(out).strip() + "\n"


def _selfcheck():
    import tempfile

    sample = [
        {"type": "mode", "mode": "default"},
        {"type": "user", "message": {"role": "user", "content": "Add a cache."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "use lru_cache"},
            {"type": "text", "text": "On it."},
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
        ]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "content": [{"type": "text", "text": "file.py"}]},
        ]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Done."},
        ]}},
        # A slash-command-with-body is recorded as a wrapper string followed by
        # an isMeta expansion of the command's prompt. Neither is a real turn.
        {"type": "user", "message": {"role": "user", "content":
            "<command-message>session-capture:session-capture</command-message>\n"
            "<command-name>/session-capture:session-capture</command-name>"}},
        {"type": "user", "isMeta": True, "message": {"role": "user", "content": [
            {"type": "text", "text": "Save the entire current Claude Code session ..."},
        ]}},
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        for row in sample:
            f.write(json.dumps(row) + "\n")
        path = f.name
    md = render(path)            # default: conversation only
    full = render(path, full=True)
    os.unlink(path)

    # Default mode: user + assistant text kept; tools/results/thinking dropped.
    assert "## \U0001F464 User" in md, "missing user header"
    assert "## \U0001F916 Assistant" in md, "missing assistant header"
    assert "Add a cache." in md and "On it." in md and "Done." in md
    assert "#### \U0001F527 Bash" not in md, "tool_use leaked into default mode"
    assert "Tool Result" not in md and "file.py" not in md, "tool_result leaked"
    assert "Thinking" not in md, "thinking leaked into default mode"
    # speaker header collapses consecutive same-speaker turns
    assert md.count("## \U0001F916 Assistant") == 1, "assistant header not collapsed"
    # bare slash-command invocation is stripped from the saved doc
    assert "/session-capture" not in md, "bare invocation not stripped"
    # the slash-command wrapper and its isMeta expansion are stripped too
    assert "command-name" not in md, "command wrapper leaked into saved doc"
    assert "Save the entire current" not in md, "expanded command body leaked"

    # Full mode: everything present.
    assert "#### \U0001F527 Bash" in full and '"command": "ls"' in full
    assert "#### \U0001F4E4 Tool Result" in full and "file.py" in full
    assert "Thinking" in full and "use lru_cache" in full
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
    full = os.environ.get("TRANSCRIPT_FULL", "").lower() in ("1", "true", "yes", "full")
    sys.stdout.write(render(path, full=full))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
