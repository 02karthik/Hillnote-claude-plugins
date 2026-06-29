---
description: Convert a website or weblink into Markdown (via markitdown) and save it into a chosen Hillnote workspace.
argument-hint: <url>
---

Convert the web page at a URL into Markdown and save it into a Hillnote workspace the user picks. Follow these steps exactly.

1. **Get the URL.** The URL is `$ARGUMENTS`. If it is empty, ask the user for the URL and stop until they provide one. Trim any surrounding whitespace or quotes.

2. **Convert the page to Markdown.** Run (substituting the real URL):

   ```bash
   bash "${CLAUDE_PLUGIN_ROOT}/scripts/url_to_md.sh" "<url>"
   ```

   Capture stdout — it is the document body.

   - **If it exits 127**, no markitdown runtime was found (markitdown needs Python 3.10+, which the system Python may not be). Offer to bootstrap it: ask permission, then run `pip3 install --user uv` and retry — `uv` auto-downloads a Python 3.10+ and markitdown on first run (cached after), so an older system Python is fine. If the user declines, show the manual options the helper printed and stop.
   - **If it exits non-zero for any other reason**, show its stderr and stop.
   - If the URL points at a PDF or Office document, re-run with `MARKITDOWN_SPEC=markitdown[all]` prefixed (heavier, but adds PDF/Word/Excel/PPT support).

3. **Choose a title.** Use the first top-level Markdown heading (`# …`) in the converted body. If there is none, use the URL's host and path (e.g. `paulgraham.com/greatwork`).

4. **Prepend a source line** to the body so the capture is attributable (run `date "+%Y-%m-%d"` for the date):

   ```
   > Source: <url> — captured <date>
   ```

5. **List Hillnote workspaces and let the user choose — interactively.** Call the Hillnote `list_workspaces` tool. Then present the choice with the `AskUserQuestion` tool (a clickable menu) instead of asking them to type — this keeps the turn alive so the command doesn't quit.

   - Header: `Workspace`. Question: which workspace to save this page into.
   - Options: the up-to-4 workspaces that best fit this page's topic (judge from the title and content). Use the workspace **name** as the label and a short hint (`Owned` / `Shared`, plus why it fits) as the description.
   - `AskUserQuestion` always adds an "Other" choice, which lets the user name any workspace not shown — so the 4-option limit doesn't hide the rest.
   - Map the chosen name back to its workspace **id** from `list_workspaces`. If the user picked "Other" and named a workspace, match it by name; if it's ambiguous or not found, ask again with `AskUserQuestion`. Do not guess the id.

6. **Save the document.** Call the Hillnote `add_document` tool with:
   - `workspace`: the id of the chosen workspace
   - `title`: the title from step 3
   - `content`: the source line + converted body
   - `folder`: `"web-captures"` (saves under `documents/web-captures/`)
   - `tags`: `["web-capture"]`
   - `emoji`: `"🔗"`

7. **Confirm.** Tell the user the title, the source URL, and which workspace it was saved to.

Notes:
- Conversion uses Microsoft's **markitdown**. The helper finds it via `markitdown` on PATH, else `uv`/`uvx` (which fetches Python 3.10+ and markitdown for you, cached after the first run).
- The Hillnote tools come from the bundled `notes` MCP server (`https://hillnote.com/mcp`). If they aren't available or return an auth error, the user needs to authenticate the server — Claude Code prompts on first use, or they can run `/mcp`. Tell them and stop.
