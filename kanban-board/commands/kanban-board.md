---
description: Parse the last Claude answer for TODO items and create a kanban board in a chosen Hillnote workspace.
---

Turn the TODO items from the most recent exchange in this session into a Hillnote kanban board. A Hillnote kanban board is a **database** (a folder of markdown rows with frontmatter columns) with a kanban view grouped by status. Follow these steps exactly.

1. **Render the last exchange.** Run:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/last_response_to_md.py"
   ```

   It reads `$CLAUDE_CODE_SESSION_ID`, finds this session's `.jsonl`, and prints the last user question and Claude's answer as Markdown. If the script exits non-zero, show its error and stop.

2. **Extract the tasks.** Read the answer (and the question, if the TODOs were pasted there) and pull out every TODO / action item. For each task decide:
   - **title** — short imperative phrase (≤ 60 chars), e.g. `Add Scribe v2 URL to elevenlabs.js`
   - **description** — one sentence of the essential detail
   - **status** — map completion markers: ✅ / "done" / "exists" → `Done`; ⚙️ / "partial" / "not wired" / "in progress" → `In Progress`; ❌ / everything else → `To Do`. Items explicitly parked/deferred also go to `To Do` with Low priority.
   - **priority** — gating/blocking work → `High`; parked/optional/nice-to-have → `Low`; otherwise `Medium`.

   Preserve any stated ordering (e.g. "items 1–4 gate everything") in the descriptions. If the exchange contains no TODO-like items, tell the user and stop.

3. **List Hillnote workspaces and let the user choose — interactively.** Call the Hillnote `list_workspaces` tool. Then present the choice with the `AskUserQuestion` tool (a clickable menu) instead of asking them to type.

   - Header: `Workspace`. Question: which workspace to create the board in.
   - Options: the up-to-4 workspaces that best fit the content. Use the workspace **name** as the label and a short hint (`Owned` / `Shared`, plus why it fits) as the description. The automatic "Other" choice covers workspaces not shown.
   - Map the chosen name back to its workspace **id** from `list_workspaces`. If ambiguous or not found, ask again. Do not guess the id.

4. **Pick the board name.** Derive a short topic name from the content, ending in "Board" (e.g. `Scribe v2 Board`). Call `find_databases` for the chosen workspace; if that path is already taken, append the output of `date "+%Y-%m-%d %H%M"`.

5. **Create one row per task.** For each task, call `add_document` with:
   - `workspace`: the chosen workspace id
   - `title`: the task title
   - `folder`: the board name (this folder becomes the database)
   - `content`: YAML frontmatter followed by a body — quote frontmatter values that contain colons:

     ```
     ---
     status: To Do
     priority: High
     description: "One-sentence summary"
     ---

     # Task title

     Fuller detail from the answer, if any.
     ```

   The rows **must exist before step 6** — the config is saved onto the folder they create.

6. **Turn the folder into a kanban database.** Call `save_database_config` with `workspace`, `databasePath` = the board name, and this config (change only `name`):

   ```json
   {
     "name": "<board name>",
     "emoji": "🗂️",
     "columns": [
       {"id": "title", "name": "Title", "type": "title", "width": 300},
       {"id": "status", "name": "Status", "type": "status", "width": 150,
        "options": ["To Do", "In Progress", "Done"],
        "optionColors": {"To Do": "red", "In Progress": "amber", "Done": "emerald"},
        "optionStates": {"To Do": "normal", "In Progress": "normal", "Done": "done"}},
       {"id": "description", "name": "Description", "type": "text", "width": 250},
       {"id": "priority", "name": "Priority", "type": "select", "width": 120,
        "options": ["High", "Medium", "Low"],
        "optionColors": {"High": "red", "Medium": "amber", "Low": "gray"}}
     ],
     "views": [
       {"id": "default", "name": "All Tasks", "type": "table", "filters": [], "sorts": []},
       {"id": "kanban", "name": "Board", "type": "kanban", "groupBy": "status", "filters": [], "sorts": []}
     ],
     "defaultView": "kanban"
   }
   ```

7. **Confirm.** Tell the user the board name, the workspace, and the card count per column (e.g. `To Do 7 · In Progress 1 · Done 2`).

Notes:
- The frontmatter keys (`status`, `priority`, `description`) are the column ids — they must match the config exactly.
- The Hillnote tools come from the bundled `notes` MCP server (`https://hillnote.com/mcp`). If they aren't available or return an auth error, the user needs to authenticate the server — Claude Code prompts on first use, or they can run `/mcp`. Tell them and stop.
