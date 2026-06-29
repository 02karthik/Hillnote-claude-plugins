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

**weblink-capture** — run `/weblink-capture <url>`. It converts the page to
Markdown with Microsoft's [markitdown](https://github.com/microsoft/markitdown),
lets you pick a workspace, and saves it under `documents/web-captures/`.
markitdown needs Python 3.10+; if it (and uv) aren't installed, the command
offers to bootstrap [uv](https://github.com/astral-sh/uv) with a single
`pip3 install --user uv` — uv then fetches a Python 3.10+ and markitdown for you
(cached), so an older system Python is fine. For URLs that point at a PDF or
Office file, prefix `MARKITDOWN_SPEC=markitdown[all]` for full document support.

## Plugins

| Plugin | Description |
| --- | --- |
| `session-capture` | Save the entire Claude Code session transcript into a chosen Hillnote workspace as a dated document. |
| `weblink-capture` | Convert any website or weblink into Markdown (via markitdown) and save it into a chosen Hillnote workspace. |

## Roadmap

- Listing on `claude-plugins-official` so the plugins are installable without
  adding this marketplace manually.
