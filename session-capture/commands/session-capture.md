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

   The script reads `$CLAUDE_CODE_SESSION_ID`, finds this session's `.jsonl`, and prints the conversation — user messages and Claude's text replies — as Markdown to stdout. Tool calls, tool results, and thinking are omitted by default for a clean read; prefix `TRANSCRIPT_FULL=1` to the command to include them. Capture that stdout — it is the document body. If the script exits non‑zero, show its error and stop.

3. **List Hillnote workspaces and let the user choose — interactively.** Call the Hillnote `list_workspaces` tool. Then present the choice with the `AskUserQuestion` tool (a clickable menu) instead of asking them to type — this keeps the turn alive so the command doesn't quit.

   - Header: `Workspace`. Question: which workspace to save the transcript into.
   - Options: the up-to-4 workspaces that best fit this session's content (judge from what was discussed). Use the workspace **name** as the label and a short hint (`Owned` / `Shared`, plus why it fits) as the description.
   - `AskUserQuestion` always adds an "Other" choice, which lets the user name any workspace not shown — so the 4-option limit doesn't hide the rest.
   - Map the chosen name back to its workspace **id** from `list_workspaces`. If the user picked "Other" and named a workspace, match it by name; if it's ambiguous or not found, ask again with `AskUserQuestion`. Do not guess the id.

4. **Save the document.** Call the Hillnote `add_document` tool with:
   - `workspace`: the id of the workspace the user chose
   - `title`: the title from step 1
   - `content`: the Markdown body from step 2
   - `folder`: `"claude-sessions"` (saves under `documents/claude-sessions/`)
   - `tags`: `["claude-code-session"]`
   - `emoji`: `"🎪"`

5. **Confirm.** Tell the user the document title and which workspace it was saved to.

Notes:
- The transcript on disk includes everything up to (but not including) this `/session-capture` turn itself — that's expected.
- The Hillnote tools come from the bundled `notes` MCP server (`https://hillnote.com/mcp`). If they aren't available or return an auth error, the user needs to authenticate the server — Claude Code prompts on first use, or they can run `/mcp`. Tell them and stop.
