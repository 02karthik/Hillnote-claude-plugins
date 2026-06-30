# Hillnote Plugins

Claude Code plugins for [Hillnote](https://hillnote.com).

## Installation

Add this marketplace, then install the plugin:

```
/plugin marketplace add 02karthik/Hillnote-Plugins
/plugin install session-capture@hillnote-plugins
```

`/plugin` is a slash command inside Claude Code. The first line registers this
repo as a plugin marketplace; the second installs the plugin from it.

The plugin bundles an MCP server (`https://hillnote.com/mcp`) that needs a
one-time login. After installing, run `/mcp` and authenticate the `notes`
server in your browser.

## Usage

**session-capture** — run `/session-capture` in any Claude Code session. It
renders the full transcript to Markdown, lists your Hillnote workspaces so you
can pick one, and saves the session as a dated document under
`documents/claude-sessions/`.

**response-capture** — run `/response-capture` to save just the last question you asked and
Claude's answer (skipping tool calls and thinking). Same workspace picker,
saved under `documents/claude-qa/`.

## Plugins

| Plugin | Description |
| --- | --- |
| `session-capture` | Save the entire Claude Code session transcript into a chosen Hillnote workspace as a dated document. |
| `response-capture` | Save the last user question and Claude's answer into a chosen Hillnote workspace as a dated document. |

## Roadmap

- Listing on `claude-plugins-official` so the plugins are installable without
  adding this marketplace manually.
