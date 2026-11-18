# Security policy

## Supported versions

Security fixes are made on the `main` branch and shipped in the next release. Only the latest release is supported, so please upgrade before reporting a problem.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

Report it privately through [GitHub's vulnerability reporting](https://github.com/YassWorks/Ally/security/advisories/new) instead. Include:

- what an attacker can do, and what they need to do it,
- the steps or a minimal example that reproduces it,
- the Ally version (`ally --version`), your operating system and the provider you used.

Ally is maintained in spare time, so replies are best effort. You should hear back within a week. Once a fix is released, the advisory is published and you are credited unless you prefer not to be.

## Security model

Ally runs an AI model's decisions on your computer, with your user account's permissions. It helps to know where its safeguards are and where they end.

### What protects you

- **Approval before every tool call.** File, shell, Python and directory tools show what they are about to do and wait for your answer. A call is denied when the prompt cannot be shown, for example when input is piped.
- **A small blocklist of destructive commands.** Commands such as formatting a disk or shutting the machine down are refused before you are asked. This is a last line of defence, not a sandbox. Plenty of harmful commands are not on it.
- **Local storage.** Conversations, the knowledge base, embedding models and logs stay on your machine. API keys are read from `.env` or your environment and sent only to the provider they belong to.

### What does not

- **`--allow-all-tools`** and the "always allow" answers turn approval off. With them, the model can change or delete anything your account can.
- **Commands you type after `!`** run directly in your shell. The model is not involved and nothing is checked.
- **Prompt injection.** Web pages, search results and your own documents can contain text written to steer the model. Read tool calls before approving them, especially after the model has browsed the web or read files you did not write.
- **Read-only tools.** The code search and git tools do not ask before reading files under the working directory, and the web tools fetch pages without asking.
- **Plain-text storage.** Conversation history is kept unencrypted in a SQLite file in Ally's data directory. See [Configuration](docs/configuration.md#where-ally-keeps-its-data) for its location.

### In scope

- A tool that changes files, runs code or runs commands without your approval while approval is on.
- API keys or other secrets written to logs, history or the knowledge base, or sent anywhere other than their provider.
- A problem in the Docker image or the install scripts that puts your machine at risk.
- A vulnerable dependency that Ally actually exposes.

### Out of scope

- Anything the model does after you approved it or turned approval off.
- Model output that is wrong, harmful or misleading, unless it leads to one of the issues in scope.
- Commands missing from the destructive command blocklist.
