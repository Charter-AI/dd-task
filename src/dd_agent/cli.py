"""CLI for DD Agent."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dd_agent.util.logging import init_default_logging

app = typer.Typer(
    name="dd-agent",
    help="DD Analytics Agent - Survey data analysis with LLM-powered planning",
)
console = Console()


@app.command()
def demo():
    """Run the autoplan flow on the demo dataset."""
    init_default_logging()

    console.print(Panel.fit(
        "[bold blue]DD Analytics Agent Demo[/bold blue]\n"
        "Running autoplan on demo dataset...",
        border_style="blue",
    ))

    # Check for demo data
    demo_dir = Path("data/demo")
    if not demo_dir.exists():
        console.print("[red]Demo data not found at data/demo/[/red]")
        console.print("Please ensure questions.json and responses.csv exist.")
        raise typer.Exit(1)

    from dd_agent.config import settings

    if not settings.is_configured:
        console.print("[yellow]Warning: Azure OpenAI not configured.[/yellow]")
        console.print("Please set environment variables or create a .env file.")
        console.print("See .env.example for required configuration.")
        raise typer.Exit(1)

    from dd_agent.orchestrator.pipeline import Pipeline

    try:
        pipeline = Pipeline(data_dir=demo_dir)
        result = pipeline.run_autoplan()

        if result.success:
            console.print(f"\n[green]✅ Success![/green]")
            console.print(f"Run ID: {result.run_id}")
            console.print(f"Run Dir: {result.run_dir}")
            console.print(f"Cuts Executed: {len(result.cuts_planned)}")

            if result.execution_result:
                table = Table(title="Results Summary")
                table.add_column("Cut ID")
                table.add_column("Metric")
                table.add_column("Question")
                table.add_column("Base N")

                for t in result.execution_result.tables:
                    table.add_row(
                        t.cut_id,
                        t.metric_type,
                        t.question_id,
                        str(t.base_n),
                    )

                console.print(table)
        else:
            console.print(f"\n[red]❌ Failed[/red]")
            for error in result.errors:
                console.print(f"  - {error}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def run(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data directory"),
    prompt: str = typer.Option(..., "--prompt", "-p", help="Analysis request"),
):
    """Run a single analysis request."""
    init_default_logging()

    console.print(Panel.fit(
        f"[bold blue]DD Analytics Agent[/bold blue]\n"
        f"Running: {prompt}",
        border_style="blue",
    ))

    from dd_agent.config import settings

    if not settings.is_configured:
        console.print("[yellow]Warning: Azure OpenAI not configured.[/yellow]")
        raise typer.Exit(1)

    from dd_agent.orchestrator.pipeline import Pipeline

    try:
        pipeline = Pipeline(data_dir=data)
        result = pipeline.run_single(prompt)

        if result.success:
            console.print(f"\n[green]✅ Success![/green]")
            console.print(f"Run ID: {result.run_id}")
            console.print(f"Run Dir: {result.run_dir}")

            if result.execution_result and result.execution_result.tables:
                table_result = result.execution_result.tables[0]
                console.print(f"\nMetric: {table_result.metric_type}")
                console.print(f"Question: {table_result.question_id}")
                console.print(f"Base N: {table_result.base_n}")
                console.print(f"\nResult: {table_result.result_data}")
        else:
            console.print(f"\n[red]❌ Failed[/red]")
            for error in result.errors:
                console.print(f"  - {error}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def autoplan(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data directory"),
    scope: Optional[Path] = typer.Option(
        None, "--scope", "-s", help="Path to scope.md file"
    ),
    max_cuts: int = typer.Option(20, "--max-cuts", "-m", help="Maximum cuts to execute"),
):
    """Generate and execute a full analysis plan."""
    init_default_logging()

    console.print(Panel.fit(
        "[bold blue]DD Analytics Agent - Autoplan[/bold blue]\n"
        f"Data: {data}",
        border_style="blue",
    ))

    from dd_agent.config import settings

    if not settings.is_configured:
        console.print("[yellow]Warning: Azure OpenAI not configured.[/yellow]")
        raise typer.Exit(1)

    from dd_agent.orchestrator.pipeline import Pipeline

    try:
        pipeline = Pipeline(data_dir=data)
        result = pipeline.run_autoplan(max_cuts=max_cuts)

        if result.success:
            console.print(f"\n[green]✅ Success![/green]")
            console.print(f"Run ID: {result.run_id}")
            console.print(f"Run Dir: {result.run_dir}")
            console.print(f"Intents: {len(result.plan.intents) if result.plan else 0}")
            console.print(f"Cuts Executed: {len(result.cuts_planned)}")
            console.print(f"Cuts Failed: {len(result.cuts_failed)}")
        else:
            console.print(f"\n[red]❌ Failed[/red]")
            for error in result.errors:
                console.print(f"  - {error}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data directory"),
):
    """Validate the data directory structure and contents."""
    init_default_logging()

    console.print("[bold]Validating data directory...[/bold]\n")

    # Check required files
    questions_path = data / "questions.json"
    responses_path = data / "responses.csv"
    scope_path = data / "scope.md"

    checks = []

    # Check questions.json
    if questions_path.exists():
        try:
            import json
            from dd_agent.contracts.questions import Question

            with open(questions_path) as f:
                q_data = json.load(f)

            if isinstance(q_data, list):
                questions = [Question.model_validate(q) for q in q_data]
            elif isinstance(q_data, dict) and "questions" in q_data:
                questions = [Question.model_validate(q) for q in q_data["questions"]]
            else:
                raise ValueError("Invalid format")

            checks.append(("questions.json", "✅", f"{len(questions)} questions"))
        except Exception as e:
            checks.append(("questions.json", "❌", str(e)))
    else:
        checks.append(("questions.json", "❌", "Not found"))

    # Check responses.csv
    if responses_path.exists():
        try:
            import pandas as pd

            df = pd.read_csv(responses_path)
            checks.append(("responses.csv", "✅", f"{len(df)} rows, {len(df.columns)} columns"))
        except Exception as e:
            checks.append(("responses.csv", "❌", str(e)))
    else:
        checks.append(("responses.csv", "❌", "Not found"))

    # Check scope.md (optional)
    if scope_path.exists():
        content = scope_path.read_text()
        checks.append(("scope.md", "✅", f"{len(content)} characters"))
    else:
        checks.append(("scope.md", "⚠️", "Not found (optional)"))

    # Display results
    table = Table(title="Data Validation Results")
    table.add_column("File")
    table.add_column("Status")
    table.add_column("Details")

    for name, status, details in checks:
        table.add_row(name, status, details)

    console.print(table)


@app.command()
def eval(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data directory"),
    cases: Path = typer.Option(..., "--cases", "-c", help="Path to eval_cases.yaml"),
):
    """Run evaluation cases against the pipeline."""
    init_default_logging()

    console.print(Panel.fit(
        "[bold blue]DD Analytics Agent - Evaluation[/bold blue]",
        border_style="blue",
    ))

    console.print("[yellow]Evaluation harness not yet implemented.[/yellow]")
    console.print("See eval/ directory for the evaluation framework.")

@app.command()
def interactive(
    data: Path = typer.Option(..., "--data", "-d", help="Path to data directory"),
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Analysis request (optional, will prompt if not provided)"),
):
    """Run analysis with interactive ambiguity resolution."""
    init_default_logging()

    console.print(Panel.fit(
        "[bold blue]DD Analytics Agent - Interactive Mode[/bold blue]",
        border_style="blue",
    ))

    from dd_agent.config import settings

    if not settings.is_configured:
        console.print("[yellow]Warning: Azure OpenAI not configured.[/yellow]")
        raise typer.Exit(1)

    from dd_agent.orchestrator.pipeline import Pipeline
    import json
    
    try:
        pipeline = Pipeline(data_dir=data)
        
        # Use the interactive pipeline method
        result = pipeline.run_interactive(prompt=prompt, save_run=True)
        
        if result.success:
            console.print(Panel.fit("[bold green]✅ Analysis Complete[/bold green]"))
            console.print(f"[bold]Run ID:[/bold] {result.run_id}")
            console.print(f"[bold]Run Dir:[/bold] {result.run_dir}")
            
            if result.execution_result and result.execution_result.tables:
                table = result.execution_result.tables[0]
                console.print(f"\n[bold]Metric:[/bold] {table.metric_type}")
                console.print(f"[bold]Question:[/bold] {table.question_id}")
                console.print(f"[bold]Base N:[/bold] {table.base_n}")
                
                # Show results summary
                if hasattr(table, 'result_data'):
                    console.print(f"\n[bold]Result:[/bold]")
                    console.print(json.dumps(table.result_data, indent=2))
        else:
            console.print(Panel.fit("[bold red]❌ Analysis Failed[/bold red]"))
            for error in result.errors:
                console.print(f"- {error}")
                
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
