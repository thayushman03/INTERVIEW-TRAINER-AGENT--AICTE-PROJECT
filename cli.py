"""
cli.py
------
Command-line interface for the Interview Trainer Agent.
Interactive terminal session with rich formatting.

Usage:
    python cli.py
    python cli.py --name "Alice" --role "Data Scientist" --level mid
    python cli.py --resume ./my_resume.pdf --role "Software Engineer"
"""

import argparse
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from src.config import validate_config
from src.agent import InterviewTrainerAgent
from src.knowledge_base import EXPERIENCE_LEVELS
from src.utils import setup_logging, format_session_report

setup_logging()

console = Console() if RICH_AVAILABLE else None


def print_header():
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold cyan]🎯 IBM Interview Trainer Agent[/bold cyan]\n"
            "[dim]Powered by IBM Granite & RAG • Problem Statement #22[/dim]",
            border_style="cyan",
        ))
    else:
        print("=" * 60)
        print("  IBM Interview Trainer Agent")
        print("  Powered by IBM Granite & RAG")
        print("=" * 60)


def print_questions(session: dict):
    tech_qs = session.get("technical_questions", [])
    behav_qs = session.get("behavioral_questions", [])

    if RICH_AVAILABLE:
        # Technical Questions Table
        if tech_qs:
            table = Table(title="📌 Technical Questions", show_lines=True, border_style="blue")
            table.add_column("#", style="dim", width=3)
            table.add_column("Question", style="white")
            table.add_column("Topic", style="cyan", width=20)
            table.add_column("Source", style="dim", width=12)
            for i, q in enumerate(tech_qs, 1):
                table.add_row(
                    str(i),
                    q["question"],
                    q.get("topic", "General"),
                    q.get("source", "kb"),
                )
            console.print(table)

        # Behavioral Questions Table
        if behav_qs:
            table2 = Table(title="🧠 Behavioral Questions", show_lines=True, border_style="green")
            table2.add_column("#", style="dim", width=3)
            table2.add_column("Question", style="white")
            table2.add_column("Framework", style="green", width=12)
            table2.add_column("Tip", style="yellow")
            for i, q in enumerate(behav_qs, 1):
                table2.add_row(
                    str(i),
                    q["question"],
                    q.get("framework", "STAR"),
                    q.get("tip", ""),
                )
            console.print(table2)
    else:
        print(format_session_report(session))


def interactive_mode(agent: InterviewTrainerAgent):
    """Full interactive CLI session."""
    print_header()

    # ── Check credentials ───────────────────────────────────────────
    missing = validate_config()
    if missing and RICH_AVAILABLE:
        console.print(f"[yellow]⚠️  Warning:[/yellow] Missing credentials ({missing}). "
                      "Running in fallback mode (RAG-only, no Granite LLM).")
    elif missing:
        print(f"Warning: Missing credentials ({missing}). Running in fallback mode.")

    # ── Collect profile ─────────────────────────────────────────────
    if RICH_AVAILABLE:
        console.print("\n[bold]Let's set up your interview session.[/bold]\n")
        name = Prompt.ask("👤 Your name")
        role = Prompt.ask("💼 Target job role", default="Software Engineer")

        level_choices = list(EXPERIENCE_LEVELS.keys())
        console.print("\nExperience levels: " + ", ".join(level_choices))
        level = Prompt.ask("📊 Experience level", choices=level_choices, default="junior")

        skills_raw = Prompt.ask(
            "🛠️  Your top skills (comma-separated, or press Enter to skip)",
            default=""
        )
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None

        num_tech = int(Prompt.ask("# Technical questions", default="5"))
        num_behav = int(Prompt.ask("# Behavioral questions", default="3"))
    else:
        print("\nEnter your interview details:\n")
        name = input("Your name: ").strip() or "Candidate"
        role = input("Target job role [Software Engineer]: ").strip() or "Software Engineer"
        level = input("Experience level (fresher/junior/mid/senior/lead) [junior]: ").strip() or "junior"
        skills_raw = input("Your top skills (comma-separated, optional): ").strip()
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else None
        num_tech = int(input("Number of technical questions [5]: ").strip() or "5")
        num_behav = int(input("Number of behavioral questions [3]: ").strip() or "3")

    # ── Generate session ─────────────────────────────────────────────
    if RICH_AVAILABLE:
        with console.status("[bold green]Generating your personalised question set...[/bold green]"):
            session = agent.start_session(
                name=name, role=role, experience_level=level,
                skills=skills, num_technical=num_tech, num_behavioral=num_behav,
            )
    else:
        print("\nGenerating your personalised question set...")
        session = agent.start_session(
            name=name, role=role, experience_level=level,
            skills=skills, num_technical=num_tech, num_behavioral=num_behav,
        )

    # ── Display results ──────────────────────────────────────────────
    print_questions(session)

    if RICH_AVAILABLE:
        console.print("\n[bold]📅 Preparation Strategy:[/bold]")
        console.print(Markdown(session.get("preparation_strategy", "")))
        console.print("\n[bold]🎯 Improvement Tips:[/bold]")
        console.print(Markdown(session.get("improvement_tips", "")))
    else:
        print("\n--- Preparation Strategy ---")
        print(session.get("preparation_strategy", ""))
        print("\n--- Improvement Tips ---")
        print(session.get("improvement_tips", ""))

    # ── Model answer loop ────────────────────────────────────────────
    all_questions = (
        [q["question"] for q in session.get("technical_questions", [])] +
        [q["question"] for q in session.get("behavioral_questions", [])]
    )

    if RICH_AVAILABLE:
        while Confirm.ask("\n\nWould you like a model answer for a question?", default=True):
            console.print("\nAvailable questions:")
            for i, q in enumerate(all_questions, 1):
                console.print(f"  [dim]{i}.[/dim] {q}")
            choice = Prompt.ask("Enter question number (or 0 to exit)", default="0")
            if choice == "0":
                break
            try:
                idx = int(choice) - 1
                question = all_questions[idx]
                with console.status("[bold green]Generating model answer...[/bold green]"):
                    result = agent.get_model_answer(question, role, level, skills)
                console.print(Panel(
                    f"[bold]Q:[/bold] {question}\n\n[bold]A:[/bold] {result['model_answer']}",
                    title="Model Answer", border_style="green",
                ))
            except (ValueError, IndexError):
                console.print("[red]Invalid choice.[/red]")
    else:
        while True:
            cont = input("\nGet model answer for a question? (y/n): ").strip().lower()
            if cont != "y":
                break
            for i, q in enumerate(all_questions, 1):
                print(f"  {i}. {q}")
            try:
                idx = int(input("Question number: ")) - 1
                question = all_questions[idx]
                result = agent.get_model_answer(question, role, level, skills)
                print(f"\nQ: {question}\n\nA: {result['model_answer']}\n")
            except (ValueError, IndexError):
                print("Invalid choice.")

    if RICH_AVAILABLE:
        console.print("\n[bold green]✅ Good luck with your interview, {}![/bold green]".format(name))
    else:
        print(f"\nGood luck with your interview, {name}!")


def main():
    parser = argparse.ArgumentParser(
        description="IBM Interview Trainer Agent – CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py
  python cli.py --name "Alice" --role "Data Scientist" --level mid
  python cli.py --resume ./resume.pdf --role "Software Engineer" --level junior
        """,
    )
    parser.add_argument("--name", help="Candidate name")
    parser.add_argument("--role", help="Target job role")
    parser.add_argument("--level", choices=list(EXPERIENCE_LEVELS.keys()), help="Experience level")
    parser.add_argument("--skills", help="Comma-separated list of skills")
    parser.add_argument("--resume", help="Path to resume file (PDF/DOCX/TXT)")
    parser.add_argument("--num-technical", type=int, default=5, help="Number of technical questions")
    parser.add_argument("--num-behavioral", type=int, default=3, help="Number of behavioral questions")

    args = parser.parse_args()
    agent = InterviewTrainerAgent()

    # Non-interactive mode if all args provided
    if args.name and args.role and args.level and not args.resume:
        skills = [s.strip() for s in args.skills.split(",")] if args.skills else None
        session = agent.start_session(
            name=args.name, role=args.role, experience_level=args.level,
            skills=skills, num_technical=args.num_technical, num_behavioral=args.num_behavioral,
        )
        print(format_session_report(session))
    elif args.resume:
        role = args.role or "Software Engineer"
        level = args.level or "junior"
        session = agent.start_session_from_resume(
            file_path=args.resume, role=role, experience_level=level,
            num_technical=args.num_technical, num_behavioral=args.num_behavioral,
        )
        print(format_session_report(session))
    else:
        interactive_mode(agent)


if __name__ == "__main__":
    main()
