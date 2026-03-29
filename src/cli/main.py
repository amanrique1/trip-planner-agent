import os
import asyncio
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.status import Status
from rich.markdown import Markdown
from agents.trip_agent import TripPlannerAgent

console = Console()

async def chat() -> None:
    console.print(Panel.fit(
        "[bold blue]Trip Planner Agent[/bold blue]\n"
        "[italic]Your AI assistant for planning the perfect journey.[/italic]",
        border_style="bright_blue"
    ))

    user_id = "cli_user"
    agent = TripPlannerAgent()

    # Let the session service create & track the session
    session_id = await agent.create_session(user_id)

    while True:
        try:
            query = Prompt.ask("\n[bold cyan]How can I help you plan your trip?[/bold cyan] (type 'exit' to quit)")

            if query.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not query.strip():
                continue

            with Status("[bold green]Agent is thinking...[/bold green]", console=console):
                events = await agent.run(
                    user_id=user_id,
                    session_id=session_id,
                    message=query
                )

                final_itinerary = ""
                async for event in events:
                    if hasattr(event, "content") and event.content:
                        final_itinerary = str(event.content)

            if final_itinerary:
                console.print("\n")
                console.print(Panel(Markdown(final_itinerary), title="[bold green]Your Trip Plan[/bold green]", border_style="green"))
            else:
                console.print("[red]No itinerary was generated. Please try a different query.[/red]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise e

def web() -> None:
    """Shortcut entry point for `adk web`."""
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"

    try:
        subprocess.run(["adk", "web", "adk-app"], check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error running adk web: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print("Error: 'adk' command not found.", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass

def app() -> None:
    """Entry point for the CLI."""
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    app()
