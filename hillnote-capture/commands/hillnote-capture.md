---
description: Save the entire current Claude Code session to a chosen Hillnote workspace as a dated document.
---

Capture this entire Claude Code session and save it into a Hillnote workspace the user picks. Follow these steps exactly.

1. **Build the document title.** Run:

   ```bash
   date "+Session %Y-%m-%d %H:%M"
   ```

   Use the output verbatim as the document title (e.g. `Session 2026-06-26 17:53`).

2. **Render the session transcript to Markdown.** Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/transcript_to_md.py"
   ```

   The script reads `$CLAUDE_CODE_SESSION_ID`, finds this session's `.jsonl`, and prints the full conversation (user/assistant turns, thinking, tool calls and results) as Markdown to stdout. Capture that stdout — it is the document body. If the script exits non‑zero, show its error and stop.

3. **List Hillnote workspaces and let the user choose.** Call the Hillnote `list_workspaces` tool, present the workspaces (name + id), and ask the user which one to save into. Do not guess — wait for their choice.

4. **Save the document.** Call the Hillnote `add_document` tool with:
   - `workspace`: the id of the workspace the user chose
   - `title`: the title from step 1
   - `content`: the Markdown body from step 2
   - `folder`: `"claude-sessions"` (saves under `documents/claude-sessions/`)
   - `tags`: `["claude-code-session"]`
   - `emoji`: `"🎪"`

5. **Confirm.** Tell the user the document title and which workspace it was saved to.

Notes:
- The transcript on disk includes everything up to (but not including) this `/hillnote-capture` turn itself — that's expected.
- The Hillnote tools come from the bundled `hillnote` MCP server (`https://hillnote.com/mcp`). If they aren't available or return an auth error, the user needs to authenticate the server — Claude Code prompts on first use, or they can run `/mcp`. Tell them and stop.
