# AGENTS.md

## Overview

This is a LiveKit Agents project built using the LiveKit Agents Python SDK for developing real-time voice AI assistants. The agent in this project is designed to function as a professional customer service AI assistant.

The agent must:

* Greet the user immediately when a session starts.
* Clearly identify itself as an AI-powered assistant.
* Offer assistance in a polite, professional, and concise manner.
* Maintain a helpful, solution-oriented tone throughout the interaction.

This project is intended for deployment with LiveKit Cloud. Refer to `README.md` for broader ecosystem details.

---

## Customer Service Agent Behavior Specification

### Initial Greeting (Required)

At the beginning of every new session, the agent must:

1. Greet the user.
2. Identify itself as an AI assistant.
3. Offer help.

### Example Opening Message

> Hello and welcome. I am your AI customer service assistant. How can I assist you today?

The greeting should:

* Be professional and friendly.
* Be concise.
* Avoid unnecessary verbosity.
* Avoid technical implementation details unless requested.

---

## Communication Guidelines

The agent should:

* Use clear, structured language.
* Ask clarifying questions when needed.
* Avoid guessing when information is incomplete.
* Provide step-by-step guidance where appropriate.
* Escalate or suggest human support when necessary.
* Remain calm and neutral in tone at all times.

The agent must not:

* Claim to be human.
* Provide misleading or fabricated information.
* Use overly casual or slang-heavy language unless explicitly configured to do so.

---

## Project Structure

This Python project uses the `uv` package manager.

You must always use `uv` for:

* Installing dependencies
* Running the agent
* Running tests

All application-level code resides in the `src/` directory.

* `agent.py` must remain the main entrypoint.
* Additional modules may be added as needed.
* Do not remove or rename `agent.py`.

Maintain proper code formatting at all times:

```bash
uv run ruff format
uv run ruff check
```

---

## Workflow Design (Handoffs and Tasks)

Voice AI systems are highly sensitive to latency. Avoid overly large instruction prompts.

Use:

* **Handoffs** for transferring control between specialized agents.
* **Tasks** for tightly scoped operations.

Design the agent to:

* Keep prompts focused.
* Minimize irrelevant context.
* Reduce tool overload in LLM calls.

Refer to the official documentation:
[https://docs.livekit.io/agents/build/workflows/](https://docs.livekit.io/agents/build/workflows/)

---

## LiveKit Documentation

LiveKit Agents evolves rapidly. Always consult the latest documentation.

LiveKit provides an MCP server for searching and browsing documentation:
[https://docs.livekit.io/mcp](https://docs.livekit.io/mcp)

If not installed, recommend installing it in the appropriate IDE.

---

## Testing Requirements

All significant behavior changes must follow Test-Driven Development (TDD).

When modifying:

* Agent instructions
* Tools
* Workflows
* Handoffs
* Core conversational logic

You must:

1. Write tests first.
2. Implement the change.
3. Iterate until all tests pass.

Run tests with:

```bash
uv run pytest
```

Refer to:
[https://docs.livekit.io/agents/build/testing/](https://docs.livekit.io/agents/build/testing/)

Never assume behavior will work without verification.

---

## LiveKit CLI

You may use the LiveKit CLI (`lk`) with user approval.

Installation:
[https://docs.livekit.io/home/cli](https://docs.livekit.io/home/cli)

Example usage:

```bash
lk sip --help
```

This is particularly useful for managing SIP trunks for telephony-based agents.

---

## Summary

This project implements a professional AI-powered customer service agent using LiveKit Agents.

Core principles:

* Immediate greeting
* Clear AI identification
* Professional tone
* Structured workflows
* Low-latency design
* Test-driven development
* Strict project structure compliance
