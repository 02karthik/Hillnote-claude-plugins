---
description: Save the last user question and Claude's answer to a chosen Hillnote workspace, titled after what was asked.
---

Capture the most recent question-and-answer exchange from this Claude Code session and save it into a Hillnote workspace the user picks. Follow these steps exactly.

1. **Render the last Q&A to Markdown.** Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/last_response_to_md.py"
   ```

   The script reads `$CLAUDE_CODE_SESSION_ID`, finds this session's `.jsonl`, and prints the **last** user question and Claude's answer as Markdown to stdout. Earlier turns, tool calls, tool results, and thinking are omitted. Capture that stdout — it is the document body. If the script exits non‑zero, show its error and stop.

2. **Build the document title from the Q&A.** Read the rendered question and answer and compose a short, descriptive Title Case name — 3 to 8 words capturing what was asked or resolved (e.g. `Why Docker Builds Fail on ARM`, `Renaming a Git Branch Safely`). Rules:
   - Derive it from the captured question/answer; do not invent detail that isn't there.
   - Plain text only — no dates, emoji, quotes, slashes, or other punctuation that could upset a filename.
   - Only if the exchange is too thin to name, fall back to a dated title by running `date "+Q&A %Y-%m-%d %H:%M"` and using its output verbatim.

3. **List Hillnote workspaces and let the user choose — interactively.** Call the Hillnote `list_workspaces` tool. Then present the choice with the `AskUserQuestion` tool (a clickable menu) instead of asking them to type — this keeps the turn alive so the command doesn't quit.

   - Header: `Workspace`. Question: which workspace to save the Q&A into.
   - Options: the up-to-4 workspaces that best fit the content (judge from the question and answer). Use the workspace **name** as the label and a short hint (`Owned` / `Shared`, plus why it fits) as the description.
   - `AskUserQuestion` always adds an "Other" choice, which lets the user name any workspace not shown — so the 4-option limit doesn't hide the rest.
   - Map the chosen name back to its workspace **id** from `list_workspaces`. If the user picked "Other" and named a workspace, match it by name; if it's ambiguous or not found, ask again with `AskUserQuestion`. Do not guess the id.

4. **Save the document.** Call the Hillnote `add_document` tool with:
   - `workspace`: the id of the workspace the user chose
   - `title`: the title from step 2
   - `content`: the Markdown body from step 1
   - `folder`: `"claude-qa"` (saves under `documents/claude-qa/`)
   - `tags`: `["claude-code-qa"]`
   - `emoji`: `"💬"`

5. **Confirm.** Tell the user the document title and which workspace it was saved to.

Notes:
- The transcript on disk includes everything up to (but not including) this `/response-capture` turn itself, so the "last question" is the one you just answered before this command was run.
- The Hillnote tools come from the bundled `notes` MCP server (`https://hillnote.com/mcp`). If they aren't available or return an auth error, the user needs to authenticate the server — Claude Code prompts on first use, or they can run `/mcp`. Tell them and stop.
