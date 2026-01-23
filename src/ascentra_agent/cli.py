"""Ascentra MVP CLI.

Only supports `uv run ascentra chat` for a continuous conversation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
import typer

from ascentra_agent.config import settings
from ascentra_agent.contracts.questions import Question
from ascentra_agent.orchestrator.agent import Agent

# Force a command group so the UX is always `ascentra chat ...`
# (Typer otherwise collapses single-command apps into `ascentra ...`).
app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Ascentra CLI."""
    return


def _load_questions(data_dir: Path) -> list[Question]:
    questions_path = data_dir / "questions.json"
    raw = json.loads(questions_path.read_text())
    if isinstance(raw, list):
        return [Question.model_validate(q) for q in raw]
    if isinstance(raw, dict) and "questions" in raw:
        return [Question.model_validate(q) for q in raw["questions"]]
    raise ValueError("Invalid questions.json format")


def _load_scope(data_dir: Path) -> Optional[str]:
    scope_path = data_dir / "scope.md"
    if scope_path.exists():
        return scope_path.read_text()
    return None


@app.command()
def chat(
    data: Path = typer.Option(Path("data/demo"), "--data", "-d", help="Path to data directory"),
) -> None:
    """Start a continuous chat session (type 'quit' to exit)."""

    if not data.exists():
        typer.echo(f"Data directory not found: {data}")
        raise typer.Exit(1)

    if not settings.is_configured:
        typer.echo("Azure OpenAI not configured. Set env vars or a .env file.")
        raise typer.Exit(1)

    questions = _load_questions(data)
    responses_path = data / "responses.csv"
    df = pd.read_csv(responses_path)
    scope = _load_scope(data)

    agent = Agent(questions=questions, responses_df=df, scope=scope)

    typer.echo("Ascentra chat. Type 'quit' to exit.")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            break

        resp = agent.handle_message(user_input)
        if resp.success and resp.message:
            typer.echo(resp.message)
        elif resp.errors:
            typer.echo("\n".join(resp.errors))
        else:
            typer.echo("Error")


