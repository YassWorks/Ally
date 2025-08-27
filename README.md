# Ally 🗿

Ally is an AI-powered CLI tool that can assist you with everyday tasks or coding projects or any wild ideas you have.
Currently running on Cerebras models through an API, but local model support (Ollama) is coming soon.

## Key Features

#### The default chat interface exposes a general-purpose agent that can:
- Read/write/modify/delete files and directories.
- Has access to the internet.
- Can execute commannds and code. (All with your permission)

#### Full coding project generation:
- use the `--create-project` flag or use the `/project` command in the chat interface.

- Complete workflow:
    - Asks for your project idea. This can be as simple or complex as you want.

    - Runs the ***Brainstormer Agent***, a capable AI assistant that will create the context space and the full project spec for the ***Codegen Agent***. (in the form of `.md` files)

    - Asks if you want to include further context (will open an interactive chatting interface with the ***Brainstormer Agent*** with the same context carried over from last step.)

    - Runs the ***Codegen Agent*** powered with the newly generated `.md` files.

    - Once the initial generation is over, an interactive chatting interface with the ***Codegen Agent*** will open (with the same context carried over from last step.)

## Tutorial

Currently, the best way to test this project in a sandboxed environment is by launching a Docker container and then entering it via the terminal to experiment with the agent without any risks.

First, start the container:
```bash
docker compose up --build
```

Then enter the container:
```bash
docker exec -it ally-ally-1 /bin/sh
```

Start the CLI (use `-h` for help):
```bash
python main.py
```

