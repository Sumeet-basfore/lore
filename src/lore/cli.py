"""Lore Command Line Interface."""

import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from lore import __version__
from lore.config import load_config, save_config, update_config
from lore.core.database import Database
from lore.core.exceptions import DatabaseError, LoreError
from lore.core.models import AtomType, Draft, DraftStatus, Platform, Project, VoiceSample
from lore.extraction.atom_extractor import AtomExtractor
from lore.generation.humanizer import Humanizer
from lore.generation.router import LLMRouter
from lore.generation.voice import VoiceCalibrator
from lore.intelligence.angle_finder import AngleFinder
from lore.intelligence.calendar import ContentCalendar
from lore.publishing.exporter import DraftExporter
from lore.project_context import find_git_root
from lore.scanner.git_scanner import GitScanner
from lore.scanner.project_walker import ProjectWalker

console = Console()


def _is_interactive() -> bool:
    """Return whether this process can safely ask the user questions."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _register_project(
    db: Database,
    path: Path,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Project:
    repo_path = find_git_root(path) or path
    repo_path = repo_path.expanduser().resolve()

    existing_path = db.get_project_by_path(repo_path)
    if existing_path:
        return existing_path

    project_name = name or repo_path.name
    existing_name = db.get_project(project_name)
    if existing_name:
        raise click.ClickException(
            f"Project name '{project_name}' is already used for {existing_name.path}. Choose another name with --name."
        )

    inspection = ProjectWalker.inspect(repo_path)
    project_description = description or inspection.get("readme_description") or "Developer project"
    project_id = f"proj_{project_name.lower().replace(' ', '_')}"
    if db.get_project(project_id):
        project_id = f"proj_{uuid.uuid4().hex[:12]}"

    project = Project(
        id=project_id,
        name=project_name,
        path=str(repo_path),
        description=project_description,
        tech_stack=inspection.get("tech_stack", []),
    )
    try:
        db.add_project(project)
    except DatabaseError as exc:
        existing_path = db.get_project_by_path(repo_path)
        if existing_path:
            return existing_path
        raise click.ClickException(str(exc)) from exc
    return project


def _resolve_project_scope(db: Database, explicit_project: Optional[str] = None) -> Optional[Project]:
    if explicit_project:
        project = db.get_project(explicit_project)
        if not project:
            raise click.ClickException(f"Project '{explicit_project}' was not found. Run `lore project list` to see registered projects.")
        return project

    repo_root = find_git_root()
    if repo_root is None:
        return None

    project = db.get_project_by_path(repo_root)
    if project:
        return project

    suggested_name = repo_root.name
    if db.get_project(suggested_name):
        suggested_name = f"{repo_root.name}-{repo_root.parent.name}"
    while db.get_project(suggested_name):
        suggested_name = f"{suggested_name}-2"
    setup_command = f'lore project add . --name "{suggested_name}"'
    if not _is_interactive():
        raise click.ClickException(f"This repository is not registered. From {repo_root}, run: {setup_command}")

    if not click.confirm(f"Register '{repo_root}' as Lore project '{suggested_name}'?", default=False):
        raise click.ClickException(f"No project was added. From {repo_root}, run: {setup_command} when ready.")

    project_name = suggested_name
    while db.get_project(project_name):
        project_name = click.prompt("Project name", default=f"{project_name}-2")

    project = _register_project(db, repo_root, name=project_name)
    console.print(
        Panel.fit(
            f"[bold]Project registered[/bold]\n[dim]{project.path}[/dim]",
            border_style="green",
        )
    )
    return project


def _show_home() -> None:
    db = Database()
    repo_root = find_git_root()
    project = db.get_project_by_path(repo_root) if repo_root else None

    details = Table.grid(padding=(0, 2))
    details.add_column(style="bold cyan", no_wrap=True)
    details.add_column(style="white")
    if project:
        details.add_row("Project", Text(project.name))
        details.add_row("Current repository", Text(str(repo_root)))
        details.add_row("Next", "lore scan  ·  lore atoms  ·  lore generate  ·  lore review")
    elif repo_root:
        details.add_row("Current repository", Text(str(repo_root)))
        details.add_row("Status", "Not registered")
        details.add_row("Next", f'From the root, run: lore project add . --name "{repo_root.name}"')
    else:
        details.add_row("Location", "Not inside a Git repository")
        details.add_row("Next", "Run lore init, then cd into a Git repository")

    console.print(
        Panel(
            details,
            title=f"[bold green]Lore[/bold green] [dim]v{__version__}[/dim]",
            subtitle="Local-first developer content",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )


def _is_sensitive_config_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in ("key", "token", "secret", "password"))


def _styled_table(title: str, header_style: str = "bold cyan") -> Table:
    return Table(
        title=title,
        show_header=True,
        header_style=header_style,
        box=box.ROUNDED,
        border_style="bright_black",
        padding=(0, 1),
        expand=True,
    )


@click.group(invoke_without_command=True, no_args_is_help=False)
@click.version_option(version=__version__, prog_name="lore")
@click.pass_context
def main(ctx: click.Context):
    """Lore: CLI-first developer content engine. Turn git commits into humanized posts."""
    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        _show_home()


# ---------------------------------------------------------------------------
# Setup & Configuration
# ---------------------------------------------------------------------------

@main.command("init")
def cmd_init():
    """Interactive onboarding and initial configuration."""
    console.print(Panel.fit("[bold cyan]Welcome to Lore![/bold cyan]\nSetting up your local content engine."))
    cfg = load_config()

    author_name = click.prompt("Your Name", default=cfg.author_name)
    author_handle = click.prompt("Your Twitter/X or LinkedIn Handle", default=cfg.author_handle)

    provider = click.prompt(
        "Default LLM Provider",
        type=click.Choice(["ollama", "openai", "anthropic", "openrouter", "gemini"]),
        default=cfg.llm_provider,
    )

    if provider == "ollama":
        default_model = click.prompt(
            "Ollama Model (e.g. gemma4:e2b, qwen3:4b, llama3.2:3b)",
            default=cfg.llm_model if cfg.llm_provider == "ollama" else "gemma4:e2b",
        )
    else:
        provider_name = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "openrouter": "OpenRouter",
            "gemini": "Gemini",
        }[provider]
        if cfg.llm_provider == provider:
            default_model = click.prompt(f"{provider_name} Model", default=cfg.llm_model)
        else:
            default_model = click.prompt(f"{provider_name} Model")

    update_config({
        "author_name": author_name,
        "author_handle": author_handle,
        "llm_provider": provider,
        "llm_model": default_model,
    })

    console.print("[bold green]✓ Configuration saved to ~/.lore/config.yml[/bold green]")


@main.group("config")
def group_config():
    """Manage configuration settings."""
    pass


@group_config.command("list")
def cmd_config_list():
    """Display current configuration."""
    cfg = load_config()
    table = Table(title="Lore Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting")
    table.add_column("Value")

    for k, v in cfg.model_dump(mode="json").items():
        display_value = "REDACTED" if _is_sensitive_config_key(k) and v else str(v)
        table.add_row(k, display_value)
    console.print(table)


@group_config.command("set")
@click.argument("key")
@click.argument("value")
def cmd_config_set(key: str, value: str):
    """Update a specific configuration setting."""
    try:
        update_config({key: value})
        if _is_sensitive_config_key(key):
            console.print(f"[bold green]✓ Updated {key} (value hidden)[/bold green]")
        else:
            console.print(f"[bold green]✓ Updated {key} = {value}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


# ---------------------------------------------------------------------------
# Project Management
# ---------------------------------------------------------------------------

@main.group("project")
def group_project():
    """Manage watched repositories and projects."""
    pass


@group_project.command("add")
@click.argument("path", type=click.Path(exists=True, file_okay=False, resolve_path=True))
@click.option("--name", "-n", help="Custom name for the project (defaults to directory name)")
@click.option("--description", "-d", help="Brief project description")
def cmd_project_add(path: str, name: Optional[str], description: Optional[str]):
    """Register a project repository to watch."""
    repo_path = Path(path)
    db = Database()
    normalized_path = find_git_root(repo_path) or repo_path.resolve()
    existing_path = db.get_project_by_path(normalized_path)
    if existing_path:
        console.print(f"[yellow]Project '{existing_path.name}' is already registered at {existing_path.path}[/yellow]")
        return
    project = _register_project(db, normalized_path, name=name, description=description)

    console.print(f"[bold green]✓ Registered project '{project.name}'[/bold green]")
    console.print(f"  Path: [dim]{project.path}[/dim]")
    console.print(f"  Stack: [cyan]{', '.join(project.tech_stack) or 'Generic'}[/cyan]")


@group_project.command("list")
def cmd_project_list():
    """List all registered projects."""
    db = Database()
    projects = db.list_projects()

    if not projects:
        console.print("[dim]No projects registered yet. Run `lore project add <path>` to get started.[/dim]")
        return

    table = _styled_table("Watched Projects")
    table.add_column("Name", style="bold")
    table.add_column("Path", style="dim")
    table.add_column("Tech Stack", style="cyan")
    table.add_column("Last Scanned")

    for p in projects:
        last_scan = p.last_scanned_at.strftime("%Y-%m-%d %H:%M") if p.last_scanned_at else "Never"
        table.add_row(p.name, p.path, ", ".join(p.tech_stack[:4]) or "—", last_scan)

    console.print(table)


@group_project.command("remove")
@click.argument("name")
def cmd_project_remove(name: str):
    """Remove a project from the registry."""
    db = Database()
    removed = db.remove_project(name)
    if removed:
        console.print(f"[bold green]✓ Removed project '{name}'[/bold green]")
    else:
        console.print(f"[bold red]Project '{name}' not found.[/bold red]")


# ---------------------------------------------------------------------------
# Scanning & Extraction
# ---------------------------------------------------------------------------

@main.command("scan")
@click.option("--project", "-p", help="Scan a specific project by name")
@click.option("--since", "-s", default="14 days ago", help="Time range (e.g. '7 days ago', '2026-11-01')")
@click.option("--all", "scan_all", is_flag=True, help="Scan all registered projects")
def cmd_scan(project: Optional[str], since: str, scan_all: bool):
    """Scan git repositories for recent commits and extract Content Atoms."""
    db = Database()
    cfg = load_config()

    if scan_all and project:
        raise click.UsageError("Use either --all or --project, not both.")

    if scan_all:
        projects = db.list_projects()
        if not projects:
            console.print("[yellow]No projects to scan. Register one with `lore project add <path>`.[/yellow]")
            return
    elif project:
        selected_project = _resolve_project_scope(db, project)
        if not selected_project:
            return
        projects = [selected_project]
    else:
        current_project = _resolve_project_scope(db)
        if current_project:
            projects = [current_project]
        elif find_git_root() is None:
            projects = db.list_projects()
            if not projects:
                console.print("[yellow]No projects to scan. Register one with `lore project add <path>`.[/yellow]")
                return
        else:
            return

    total_atoms_created = 0

    for proj in projects:
        proj_path = Path(proj.path)
        scan_root = find_git_root(proj_path)
        if scan_root is None:
            console.print(f"[yellow]Skipping {proj.name}: not a git repository.[/yellow]")
            continue

        with console.status(f"[cyan]Scanning git history in {proj.name}...[/cyan]"):
            scanner = GitScanner(scan_root)
            commits = scanner.scan_commits(since=since, exclude_patterns=cfg.exclude_patterns)
            tags = scanner.get_tags()
            atoms = AtomExtractor.extract_atoms(
                project_id=proj.id,
                commits=commits,
                tags=tags,
                tech_stack=proj.tech_stack,
            )

            for atom in atoms:
                db.save_atom(atom)
                total_atoms_created += 1

            db.update_project_scan_time(proj.id, datetime.now(timezone.utc))

        console.print(
            f"[bold green]✓ {proj.name}:[/bold green] Scanned {len(commits)} commits → Extracted {len(atoms)} Content Atoms"
        )

    console.print(f"\n[bold]Total Content Atoms indexed: [cyan]{total_atoms_created}[/cyan][/bold]")
    console.print("[dim]Run `lore atoms` to view extracted topics or `lore generate` to draft posts.[/dim]")


@main.command("atoms")
@click.option("--project", "-p", help="Filter by project name")
@click.option("--status", type=click.Choice(["unprocessed", "drafted", "archived", "all"]), default="all")
def cmd_atoms(project: Optional[str], status: str):
    """View extracted Content Atoms."""
    db = Database()
    selected_project = _resolve_project_scope(db, project)
    proj_id = selected_project.id if selected_project else None

    filter_status = None if status == "all" else status
    atoms = db.list_atoms(project_id=proj_id, status=filter_status)

    if not atoms:
        console.print("[dim]No atoms found. Run `lore scan` to extract atoms from your projects.[/dim]")
        return

    table = _styled_table("Content Atoms · Engineering Accomplishments", header_style="bold blue")
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", style="magenta")
    table.add_column("Title", style="bold")
    table.add_column("Diff", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for a in atoms:
        score_color = "green" if a.potential_score >= 0.8 else "yellow" if a.potential_score >= 0.6 else "dim"
        diff_str = f"+{a.evidence.insertions}/-{a.evidence.deletions}"
        table.add_row(
            a.id[:10],
            a.atom_type.value,
            a.title,
            diff_str,
            f"[{score_color}]{a.potential_score:.2f}[/{score_color}]",
            a.status,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Generation & Drafting
# ---------------------------------------------------------------------------

@main.command("generate")
@click.option("--project", "-p", help="Target project name")
@click.option("--atom", "-a", "atom_id", help="Target specific Content Atom ID")
@click.option(
    "--platform",
    type=click.Choice(["twitter", "thread", "linkedin", "blog", "changelog"]),
    default="twitter",
    help="Platform format",
)
@click.option("--model", "-m", help="Override LLM model (e.g. gemma4:e2b, gpt-4o)")
@click.option("--provider", help="Override LLM provider (ollama, openai, anthropic, etc.)")
def cmd_generate(
    project: Optional[str],
    atom_id: Optional[str],
    platform: str,
    model: Optional[str],
    provider: Optional[str],
):
    """Generate humanized social media posts or articles from Content Atoms."""
    db = Database()
    cfg = load_config()

    target_atom = None
    target_project = None

    if atom_id:
        target_atom = db.get_atom(atom_id)
        if not target_atom:
            raise click.ClickException(f"Atom '{atom_id}' was not found.")
        target_project = db.get_project(target_atom.project_id)

        if project:
            selected_project = _resolve_project_scope(db, project)
            if target_project is None or target_project.id != selected_project.id:
                raise click.ClickException(
                    f"Atom '{atom_id}' does not belong to project '{project}'. Choose an atom from that project."
                )
    else:
        target_project = _resolve_project_scope(db, project)

    if target_project:
        atoms = db.list_atoms(project_id=target_project.id, status="unprocessed")
        if not atoms:
            atoms = db.list_atoms(project_id=target_project.id)
        if not atoms:
            raise click.ClickException(
                f"No atoms found for '{target_project.name}'. Run `lore scan --project {target_project.name}` first."
            )
        if target_atom is None:
            target_atom = atoms[0]
    else:
        if target_atom is None:
            all_atoms = db.list_atoms()
            project_ids = {atom.project_id for atom in all_atoms}
            if len(project_ids) > 1:
                raise click.ClickException(
                    "Atoms belong to multiple projects. Run `lore generate --project <name>` or pass `--atom <id>`."
                )
            atoms = db.list_atoms(status="unprocessed")
            if not atoms:
                atoms = all_atoms
            if not atoms:
                console.print("[yellow]No atoms found in database. Run `lore scan` first.[/yellow]")
                return
            target_atom = atoms[0]
        target_project = db.get_project(target_atom.project_id)

    if target_project is None:
        raise click.ClickException(f"Could not find a project for atom '{target_atom.id}'.")

    plat = Platform(platform)
    angles = AngleFinder.find_angles(target_atom)
    chosen_angle = next((ang for ang in angles if plat in ang.best_platforms), angles[0])

    # Voice context
    voice_samples = db.list_voice_samples()
    voice_context = VoiceCalibrator.build_voice_context(voice_samples)

    router = LLMRouter(cfg)
    prompt = router.render_prompt(
        platform=plat,
        project_name=target_project.name if target_project else "Project",
        atom=target_atom,
        angle=chosen_angle,
        voice_context=voice_context,
    )

    p_name = provider or cfg.llm_provider
    m_name = model or cfg.llm_model

    console.print(f"[cyan]Generating {plat.value.upper()} draft via [bold]{p_name}/{m_name}[/bold]...[/cyan]")

    try:
        raw_output = router.generate(
            prompt=prompt,
            provider=p_name,
            model=m_name,
        )
    except Exception as e:
        raise click.ClickException(f"LLM generation failed: {e}") from e

    # 3-Pass Anti-Slop Humanization
    humanized_output, audit = Humanizer.humanize(raw_output, voice_context=voice_context)

    draft_id = f"draft_{uuid.uuid4().hex[:8]}"
    draft = Draft(
        id=draft_id,
        atom_id=target_atom.id,
        project_id=target_project.id if target_project else "unknown",
        platform=plat,
        title=f"{plat.value.capitalize()}: {target_atom.title}",
        raw_content=raw_output,
        humanized_content=humanized_output,
        humanizer_audit=audit,
        status=DraftStatus.DRAFTED,
    )
    db.save_draft(draft)
    db.update_atom_status(target_atom.id, "drafted")

    # Display results
    console.print(
        Panel(
            Markdown(humanized_output),
            title=f"[bold green]{plat.value.upper()} draft[/bold green]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    if audit.get("patterns_cleansed"):
        cleansed_str = ", ".join(audit["patterns_cleansed"][:5])
        console.print(f"[dim]Anti-slop patterns removed: {cleansed_str}[/dim]")

    console.print(f"[bold]Draft ID:[/bold] [cyan]{draft_id}[/cyan]")
    console.print(
        f"[bold cyan]Next:[/bold cyan] review with `lore draft show {draft_id}` "
        f"or approve with `lore draft approve {draft_id}`.\n"
    )


# ---------------------------------------------------------------------------
# Draft Review & Workflow
# ---------------------------------------------------------------------------

@main.command("drafts")
@click.option("--project", "-p", help="Filter by project")
@click.option("--platform", type=click.Choice(["twitter", "thread", "linkedin", "blog", "changelog"]))
@click.option("--status", type=click.Choice(["drafted", "approved", "rejected", "published"]))
def cmd_drafts(project: Optional[str], platform: Optional[str], status: Optional[str]):
    """List generated drafts."""
    db = Database()
    selected_project = _resolve_project_scope(db, project)
    proj_id = selected_project.id if selected_project else None

    plat = Platform(platform) if platform else None
    stat = DraftStatus(status) if status else None

    drafts = db.list_drafts(project_id=proj_id, platform=plat, status=stat)
    if not drafts:
        console.print("[dim]No drafts found. Generate one with `lore generate`.[/dim]")
        return

    table = _styled_table("Content Drafts", header_style="bold green")
    table.add_column("Draft ID", style="dim")
    table.add_column("Platform", style="magenta")
    table.add_column("Title", style="bold")
    table.add_column("Status")
    table.add_column("Updated", style="dim")

    for d in drafts:
        stat_color = "green" if d.status == DraftStatus.APPROVED else "yellow" if d.status == DraftStatus.DRAFTED else "red"
        table.add_row(
            d.id,
            d.platform.value,
            d.title or "Untitled",
            f"[{stat_color}]{d.status.value}[/{stat_color}]",
            d.updated_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)


@main.group("draft")
def group_draft():
    """Inspect, edit, approve, or reject drafts."""
    pass


@group_draft.command("show")
@click.argument("draft_id")
def cmd_draft_show(draft_id: str):
    """Inspect full draft content, evidence, and audit logs."""
    db = Database()
    draft = db.get_draft(draft_id)
    if not draft:
        console.print(f"[bold red]Draft '{draft_id}' not found.[/bold red]")
        return

    console.print(f"\n[bold cyan]Draft {draft.id}[/bold cyan] ({draft.platform.value.upper()}) - Status: {draft.status.value}")
    console.print(Panel(draft.humanized_content, title="Content"))

    if draft.atom_id:
        atom = db.get_atom(draft.atom_id)
        if atom:
            ev = atom.evidence
            console.print(
                f"[dim]Evidence: {ev.files_changed} files touched (+{ev.insertions}/-{ev.deletions}) "
                f"across {len(ev.commits)} commits. Key files: {', '.join(ev.key_files[:3])}[/dim]"
            )

    if draft.humanizer_audit:
        cleansed = draft.humanizer_audit.get("patterns_cleansed", [])
        if cleansed:
            console.print(f"[dim]Anti-slop filters triggered: {', '.join(cleansed)}[/dim]\n")


@group_draft.command("edit")
@click.argument("draft_id")
def cmd_draft_edit(draft_id: str):
    """Open draft in your $EDITOR for manual refinement."""
    db = Database()
    draft = db.get_draft(draft_id)
    if not draft:
        console.print(f"[bold red]Draft '{draft_id}' not found.[/bold red]")
        return

    editor = os.environ.get("EDITOR", "nano")
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as tf:
        tf.write(draft.humanized_content)
        tf_path = tf.name

    try:
        subprocess.run([editor, tf_path], check=True)
        with open(tf_path, "r", encoding="utf-8") as f:
            updated_content = f.read().strip()

        if updated_content and updated_content != draft.humanized_content:
            db.update_draft_content(draft.id, updated_content)
            console.print(f"[bold green]✓ Updated draft {draft.id}[/bold green]")
        else:
            console.print("[dim]No changes made.[/dim]")
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)


@group_draft.command("approve")
@click.argument("draft_id")
def cmd_draft_approve(draft_id: str):
    """Mark a draft as approved for publication."""
    db = Database()
    db.update_draft_status(draft_id, DraftStatus.APPROVED)
    console.print(f"[bold green]✓ Draft '{draft_id}' marked as APPROVED.[/bold green]")


@group_draft.command("reject")
@click.argument("draft_id")
def cmd_draft_reject(draft_id: str):
    """Mark a draft as rejected."""
    db = Database()
    db.update_draft_status(draft_id, DraftStatus.REJECTED)
    console.print(f"[yellow]Draft '{draft_id}' marked as REJECTED.[/yellow]")


# ---------------------------------------------------------------------------
# Voice Profile Calibration
# ---------------------------------------------------------------------------

@main.group("voice")
def group_voice():
    """Calibrate your unique developer writing voice."""
    pass


@group_voice.command("add")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option("--title", "-t", help="Sample title")
def cmd_voice_add(file_path: str, title: Optional[str]):
    """Ingest a writing sample (markdown or text) to train your voice profile."""
    p = Path(file_path)
    content = p.read_text(encoding="utf-8")
    sample_title = title or p.stem

    analysis = VoiceCalibrator.analyze_sample(content)
    sample_id = f"voice_{uuid.uuid4().hex[:8]}"

    sample = VoiceSample(
        id=sample_id,
        title=sample_title,
        content=content,
        analysis=analysis,
    )

    db = Database()
    db.save_voice_sample(sample)

    console.print(f"[bold green]✓ Ingested voice sample '{sample_title}'[/bold green]")
    console.print(f"  Avg sentence length: [cyan]{analysis['avg_sentence_len']} words[/cyan]")
    console.print(f"  Contraction rate: [cyan]{analysis['contraction_rate'] * 100:.1f}%[/cyan]")
    console.print(f"  First-person rate: [cyan]{analysis['first_person_rate'] * 100:.1f}%[/cyan]")


@group_voice.command("list")
def cmd_voice_list():
    """List ingested voice samples."""
    db = Database()
    samples = db.list_voice_samples()
    if not samples:
        console.print("[dim]No voice samples added. Ingest some with `lore voice add <file.md>`.[/dim]")
        return

    table = Table(title="Voice Profile Samples", show_header=True, header_style="bold cyan")
    table.add_column("Title", style="bold")
    table.add_column("Sentences", justify="right")
    table.add_column("Avg Words/Sentence", justify="right")
    table.add_column("First-Person")

    for s in samples:
        a = s.analysis
        table.add_row(
            s.title,
            str(a.get("sentence_count", "—")),
            str(a.get("avg_sentence_len", "—")),
            f"{a.get('first_person_rate', 0)*100:.1f}%",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Calendar & Export
# ---------------------------------------------------------------------------

@main.command("calendar")
@click.option("--project", "-p", help="Filter calendar by project")
def cmd_calendar(project: Optional[str]):
    """View 5-day Content Calendar recommendations."""
    db = Database()
    selected_project = _resolve_project_scope(db, project)
    proj_id = selected_project.id if selected_project else None

    atoms = db.list_atoms(project_id=proj_id)
    if not atoms:
        console.print("[yellow]No atoms found to plan calendar. Run `lore scan` first.[/yellow]")
        return

    schedule = ContentCalendar.plan_week(atoms)
    table = _styled_table("Suggested Content Calendar", header_style="bold yellow")
    table.add_column("Day", style="bold")
    table.add_column("Platform", style="magenta")
    table.add_column("Atom Topic", style="cyan")
    table.add_column("Hook Preview")

    for slot in schedule:
        table.add_row(
            slot.day_of_week,
            slot.platform.value.upper(),
            slot.atom.title,
            slot.suggested_hook[:60] + "...",
        )

    console.print(table)


@main.command("export")
@click.option("--project", "-p", help="Export drafts for a specific project")
@click.option("--status", type=click.Choice(["approved", "drafted", "all"]), default="approved")
@click.option("--format", "format_type", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--output-dir", "-o", default="./exports", help="Destination directory")
def cmd_export(project: Optional[str], status: str, format_type: str, output_dir: str):
    """Export approved drafts to Markdown or JSON."""
    db = Database()
    selected_project = _resolve_project_scope(db, project)
    filter_status = None if status == "all" else DraftStatus(status)
    drafts = db.list_drafts(
        project_id=selected_project.id if selected_project else None,
        status=filter_status,
    )

    if not drafts:
        console.print(f"[yellow]No drafts found matching status '{status}'.[/yellow]")
        return

    out_path = Path(output_dir)
    files = DraftExporter.export(drafts, out_path, format_type=format_type)

    console.print(f"[bold green]✓ Exported {len(files)} draft(s) to {out_path}[/bold green]")
    for f in files:
        console.print(f"  [dim]• {f.name}[/dim]")


# ---------------------------------------------------------------------------
# Visual Card Generator Command
# ---------------------------------------------------------------------------

@main.command("card")
@click.option("--diff", "-d", "diff_file", type=click.Path(exists=True), help="Read diff from file instead of git.")
@click.option("--output", "-o", help="Output PNG/SVG destination path.")
@click.option("--theme", default="tokyo_night", type=click.Choice(["tokyo_night", "catppuccin_mocha", "one_dark"]))
@click.option("--aspect-ratio", default="16:9", type=click.Choice(["16:9", "1:1"]))
def cmd_card(diff_file: Optional[str], output: Optional[str], theme: str, aspect_ratio: str):
    """Generate high-contrast visual diff card from git diff or file."""
    from lore.visual.card_generator import generate_diff_card
    if diff_file:
        diff_text = Path(diff_file).read_text(encoding="utf-8")
    else:
        res = subprocess.run(["git", "diff", "HEAD~1"], capture_output=True, text=True)
        diff_text = res.stdout or ""

    card_path = generate_diff_card(
        diff_text=diff_text,
        output_path=Path(output) if output else None,
        theme_name=theme,
        aspect_ratio=aspect_ratio,
    )
    console.print(f"[bold green]✓ Visual diff card created:[/bold green] {card_path}")


# ---------------------------------------------------------------------------
# Review Gateway Command (Interactive TUI + Web Dashboard)
# ---------------------------------------------------------------------------

@main.command("review")
@click.option("--project", "-p", help="Review pending drafts for one project")
@click.option("--web", is_flag=True, help="Launch zero-dependency web review dashboard (port 4748).")
@click.option("--port", default=4748, help="Port for web review dashboard.")
def cmd_review(project: Optional[str], web: bool, port: int):
    """Interactive review gateway for inspecting, editing, and approving drafts."""
    if web:
        if project:
            raise click.UsageError("The web dashboard currently shows all projects; remove --project or omit --web.")
        from lore.approval.local_web import run_local_web_server
        run_local_web_server(port=port)
        return

    # Terminal Interactive TUI
    db = Database()
    selected_project = _resolve_project_scope(db, project)
    pending = db.list_drafts(
        project_id=selected_project.id if selected_project else None,
        status=DraftStatus.DRAFTED,
    )
    if not pending:
        console.print("[dim]No pending drafts to review. Generate some with `lore generate`.[/dim]")
        return

    current_idx = 0
    while True:
        draft = pending[current_idx]
        console.clear()
        console.print(
            Panel(
                Markdown(draft.humanized_content),
                title=f"[bold cyan]{draft.title or 'Draft'}[/bold cyan]",
                subtitle=(
                    f"{draft.platform.value.upper()} · {draft.status.value} · "
                    f"{current_idx + 1} of {len(pending)} · {draft.id}"
                ),
                border_style="cyan",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print(
            "[bold]Review[/bold]  [green]a[/green] approve  [red]r[/red] reject  "
            "[yellow]e[/yellow] edit  [dim]n/p[/dim] navigate  [dim]w[/dim] web  [dim]q[/dim] quit"
        )

        choice = click.getchar().lower()
        if choice == "a":
            db.update_draft_status(draft.id, DraftStatus.APPROVED)
            console.print(f"[bold green]✓ Approved {draft.id}[/bold green]")
            pending.pop(current_idx)
            if not pending:
                console.print("[bold green]All drafts reviewed![/bold green]")
                break
            if current_idx >= len(pending):
                current_idx = max(0, len(pending) - 1)
        elif choice == "r":
            db.update_draft_status(draft.id, DraftStatus.REJECTED)
            console.print(f"[bold red]✗ Rejected {draft.id}[/bold red]")
            pending.pop(current_idx)
            if not pending:
                console.print("[yellow]All drafts reviewed.[/yellow]")
                break
            if current_idx >= len(pending):
                current_idx = max(0, len(pending) - 1)
        elif choice == "e":
            editor = os.environ.get("EDITOR", "nano")
            with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as tf:
                tf.write(draft.humanized_content)
                tf_path = tf.name
            try:
                subprocess.run([editor, tf_path], check=True)
                with open(tf_path, "r", encoding="utf-8") as f:
                    new_text = f.read().strip()
                if new_text and new_text != draft.humanized_content:
                    db.update_draft_content(draft.id, new_text)
                    draft.humanized_content = new_text
            finally:
                if os.path.exists(tf_path):
                    os.remove(tf_path)
        elif choice in ("n", "\x1b[b"):
            if current_idx < len(pending) - 1:
                current_idx += 1
        elif choice in ("p", "\x1b[a"):
            if current_idx > 0:
                current_idx -= 1
        elif choice == "w":
            from lore.approval.local_web import run_local_web_server
            run_local_web_server(port=port)
            break
        elif choice in ("q", "\x03"):
            break


# ---------------------------------------------------------------------------
# MCP Server Command
# ---------------------------------------------------------------------------

@main.command("mcp")
def cmd_mcp():
    """Launch Lore stdio Model Context Protocol (MCP) server for Cursor and Claude Code."""
    from lore.mcp.server import run_stdio_server
    run_stdio_server()


if __name__ == "__main__":
    main()
