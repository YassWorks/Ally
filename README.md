# Ally 🗿

Ally is an AI-powered CLI tool that can assist you with everyday tasks or coding projects or any wild ideas you have.

## Key Features

- Multi-agent collaborative approach to project generation
- Support for various programming languages and frameworks
- Automated project scaffolding and file generation
- Web research integration for up-to-date best practices
- Rich terminal interface with progress visualization

## Tutorial

Currently, the best way to test this project in a sandboxed environment is by launching a Docker container and then entering it via the terminal to experiment with the agent without any risks.

First, start the container:
```bash
docker compose up --build
```

Then enter the container:
```bash
docker exec -it projectgen-projectgen-1 /bin/sh
```

You may modify the `main.py` file as needed or run it directly:
```bash
python main.py
```
