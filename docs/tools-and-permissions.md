# Tools and permissions

Ally's agents act through tools: functions the model can call to read files, run commands or look things up. This page lists every tool, explains how approval works and shows what to expect when something goes wrong.

- [Approving tool calls](#approving-tool-calls)
- [Tool reference](#tool-reference)
- [Which agent has which tools](#which-agent-has-which-tools)
- [Running commands yourself](#running-commands-yourself)
- [Safety notes](#safety-notes)

## Approving tool calls

Before a tool that changes or reads your files or runs anything, Ally prints the call with its arguments and asks:

```text
Attempting to call 'execute_command'

   >  1. Yes, allow once
      2. No, deny access (request modifications)
      3. Yes, always allow this tool (execute_command) to run
      4. Yes, always allow all tools to run freely (USE AT YOUR OWN RISK)
```

| Answer | Effect |
| --- | --- |
| Allow once | Runs this call only. |
| Deny | Skips the call. The model is told it was denied and can try another approach or ask you what to change. |
| Always allow this tool | Runs this tool without asking for the rest of the session. |
| Always allow all tools | Turns approval off for the rest of the session, like `--allow-all-tools`. |

Long arguments, such as the content of a file, are shortened on screen. Answers that start with "always" last until Ally exits and are never saved.

When the model asks for several tools at once, they run one after another, each with its own prompt, so you can approve some and deny others.

If Ally cannot show the prompt, for example when its input is piped from another program, the call is denied and a warning explains how to allow tools. Start Ally with `--allow-all-tools` in that case.

## Tool reference

The model decides when to use a tool based on its description. Arguments that take a path accept absolute paths or paths relative to the working directory.

### Files

All file tools ask for approval.

| Tool | What it does |
| --- | --- |
| `read_file` | Returns the full text of a file. |
| `create_file` | Writes a file, replacing it if it exists, and creates missing parent folders. |
| `modify_file` | Replaces the first occurrence of an exact block of text in a file. |
| `append_file` | Adds text to the end of a file, creating it if needed. |
| `delete_file` | Deletes a file. |
| `create_wd` | Creates a folder and any missing parents. |
| `delete_directory` | Deletes a folder and everything in it. |
| `list_directory` | Shows a folder as a tree. Folders such as `.git`, `node_modules` and virtual environments are listed but not expanded. |

### Running code

Both tools ask for approval, run in the working directory by default and stop after one hour.

| Tool | What it does |
| --- | --- |
| `execute_command` | Runs a command in the system shell (`/bin/sh` on Linux and macOS, `cmd.exe` on Windows) and returns its output and exit code. |
| `execute_code` | Saves Python code to a temporary file, runs it with the same Python that runs Ally and returns its output. |

### Searching code

These tools only read, and they do not ask for approval.

| Tool | What it does |
| --- | --- |
| `find_references` | Finds lines containing a keyword under a folder, ignoring case. Falls back to close matches when nothing matches exactly. |
| `find_declaration` | Finds where a function, class, variable or type is declared, for Python, JavaScript, TypeScript, Go, Rust and C. |

Both return at most 30 results as `path:line: snippet`. They skip files that are not UTF-8 text, files over 10 MB, `.env` files and the same folders `list_directory` does not expand.

### Git

Read-only, no approval needed. Available to the coding agent.

| Tool | What it does |
| --- | --- |
| `diff` | Summarizes changed files with `git diff --stat`, for unstaged changes or between commits. |
| `blame` | Shows the commit and author that last changed each line of a file. |

### Web

These tools fetch public pages and do not ask for approval.

| Tool | What it does |
| --- | --- |
| `fetch_tool` | Downloads a page and returns its readable text, up to 10,000 characters. |
| `search_and_scrape` | Searches the web and returns the title, URL and first 4,000 characters of the top five results. See [web search](configuration.md#web-search). |
| `call_searcher` | Hands a question to the web searcher agent, which searches, reads and returns a summary with sources. |

## Which agent has which tools

| Agent | Tools |
| --- | --- |
| General (main chat) | Files, running code, searching code, `fetch_tool`, `call_searcher` |
| Coding | Files, running code, searching code, git, `call_searcher` |
| Brainstormer | Files, `call_searcher` |
| Web searcher | `search_and_scrape`, `fetch_tool` |

The coding agent and the brainstormer only run in the [project workflow](configuration.md#project-workflow). Each agent's prompt is in [`app/prompts`](../app/prompts).

## Running commands yourself

Start a message with `!` to run a shell command directly:

```text
> !git log --oneline -5
```

The command runs in the working directory, in your login shell on Linux and macOS (`$SHELL`) and in PowerShell on Windows. Its output is printed but not sent to the model, and nothing asks for approval because you typed it.

## Safety notes

- **Errors go back to the model.** When a tool fails, for example because a file does not exist or an argument is wrong, the error is returned to the model as the tool's result. It usually corrects itself on the next step.
- **A blocklist stops the worst commands.** `execute_command` and `execute_code` refuse a short list of destructive commands, such as wiping a disk, formatting a drive or shutting the machine down, before you are asked. It is a safety net, not a sandbox.
- **Web content can carry instructions.** Pages and documents can contain text meant to steer the model. Review tool calls carefully after the model has read untrusted content.
- **"Allow all" means all.** With `--allow-all-tools` or "always allow all tools", the model can change or delete anything your user account can. Use it in a disposable folder, a container or a virtual machine.

[SECURITY.md](../SECURITY.md) describes the security model in more detail and how to report a problem.
