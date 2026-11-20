"""Lore Command Line Interface."""

import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from lore import __version__
from lore.config import load_config, save_config, update_config
from lore.core.database import Database
from lore.core.exceptions import LoreError
from lore.core.models import AtomType, Draft, DraftStatus, Platform, Project, VoiceSample
from lore.extraction.atom_extractor import AtomExtractor
from lore.generation.humanizer import Humanizer
from lore.generation.router import LLMRouter
from lore.generation.voice import VoiceCalibrator
from lore.intelligence.angle_finder import AngleFinder
from lore.intelligence.calendar import ContentCalendar
from lore.publishing.exporter import DraftExporter
from lore.scanner.git_scanner import GitScanner
from lore.scanner.project_walker import ProjectWalker

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="lore")
def main():
    """Lore: CLI-first developer content engine. Turn git commits into humanized posts."""
    pass


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

    default_model = cfg.llm_model
    if provider == "ollama":
        default_model = click.prompt("Ollama Model (e.g. gemma4:e2b, qwen3:4b, llama3.2:3b)", default="gemma4:e2b")

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
        table.add_row(k, str(v))
    console.print(table)


@group_config.command("set")
@click.argument("key")
@click.argument("value")
def cmd_config_set(key: str, value: str):
    """Update a specific configuration setting."""
    try:
        update_config({key: value})
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
    proj_name = name or repo_path.name
    proj_id = f"proj_{proj_name.lower().replace(' ', '_')}"

    db = Database()
    existing = db.get_project(proj_name)
    if existing:
        console.print(f"[yellow]Project '{proj_name}' is already registered at {existing.path}[/yellow]")
        return

    # Inspect project structure
    inspection = ProjectWalker.inspect(repo_path)
    desc = description or inspection.get("readme_description") or "Developer project"

    project = Project(
        id=proj_id,
        name=proj_name,
        path=str(repo_path),
        description=desc,
        tech_stack=inspection.get("tech_stack", []),
    )
    db.add_project(project)

    console.print(f"[bold green]✓ Registered project '{proj_name}'[/bold green]")
    console.print(f"  Path: [dim]{repo_path}[/dim]")
    console.print(f"  Stack: [cyan]{', '.join(project.tech_stack) or 'Generic'}[/cyan]")


@group_project.command("list")
def cmd_project_list():
    """List all registered projects."""
    db = Database()
    projects = db.list_projects()

    if not projects:
        console.print("[dim]No projects registered yet. Run `lore project add <path>` to get started.[/dim]")
        return

    table = Table(title="Watched Projects", show_header=True, header_style="bold cyan")
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

    if scan_all or not project:
        projects = db.list_projects()
        if not projects:
            console.print("[yellow]No projects to scan. Register one with `lore project add <path>`.[/yellow]")
            return
    else:
        p = db.get_project(project)
        if not p:
            console.print(f"[bold red]Project '{project}' not found.[/bold red]")
            return
        projects = [p]

    total_atoms_created = 0

    for proj in projects:
        proj_path = Path(proj.path)
        if not (proj_path / ".git").is_dir():
            console.print(f"[yellow]Skipping {proj.name}: not a git repository.[/yellow]")
            continue

        with console.status(f"[cyan]Scanning git history in {proj.name}...[/cyan]"):
            scanner = GitScanner(proj_path)
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
    proj_id = None
    if project:
        p = db.get_project(project)
        if not p:
            console.print(f"[bold red]Project '{project}' not found.[/bold red]")
            return
        proj_id = p.id

    filter_status = None if status == "all" else status
    atoms = db.list_atoms(project_id=proj_id, status=filter_status)

    if not atoms:
        console.print("[dim]No atoms found. Run `lore scan` to extract atoms from your projects.[/dim]")
        return

    table = Table(title="Content Atoms (Engineering Accomplishments)", show_header=True, header_style="bold blue")
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
            console.print(f"[bold red]Atom '{atom_id}' not found.[/bold red]")
            return
        target_project = db.get_project(target_atom.project_id)
    elif project:
        target_project = db.get_project(project)
        if not target_project:
            console.print(f"[bold red]Project '{project}' not found.[/bold red]")
            return
        atoms = db.list_atoms(project_id=target_project.id, status="unprocessed")
        if not atoms:
            atoms = db.list_atoms(project_id=target_project.id)
        if not atoms:
            console.print(f"[yellow]No atoms found for '{project}'. Run `lore scan -p {project}` first.[/yellow]")
            return
        target_atom = atoms[0]
    else:
        atoms = db.list_atoms(status="unprocessed")
        if not atoms:
            atoms = db.list_atoms()
        if not atoms:
            console.print("[yellow]No atoms found in database. Run `lore scan` first.[/yellow]")
            return
        target_atom = atoms[0]
        target_project = db.get_project(target_atom.project_id)

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
        console.print(f"[bold red]LLM Generation failed:[/bold red] {e}")
        console.print("[dim]Falling back to mock offline preview mode...[/dim]")
        raw_output = router.generate(prompt=prompt, force_mock=True)

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
    console.print("\n" + "=" * 60)
    console.print(Panel(humanized_output, title=f"[bold green]Humanized Draft ({plat.value.upper()})[/bold green]"))

    if audit.get("patterns_cleansed"):
        cleansed_str = ", ".join(audit["patterns_cleansed"][:5])
        console.print(f"[dim]🛡️  Anti-Slop Cleansed: {cleansed_str}[/dim]")

    console.print(f"[bold]Draft ID:[/bold] [cyan]{draft_id}[/cyan]")
    console.print("[dim]Run `lore draft approve <id>` to approve or `lore draft edit <id>` to refine.[/dim]\n")


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
    proj_id = None
    if project:
        p = db.get_project(project)
        if p:
            proj_id = p.id

    plat = Platform(platform) if platform else None
    stat = DraftStatus(status) if status else None

    drafts = db.list_drafts(project_id=proj_id, platform=plat, status=stat)
    if not drafts:
        console.print("[dim]No drafts found. Generate one with `lore generate`.[/dim]")
        return

    table = Table(title="Content Drafts", show_header=True, header_style="bold green")
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
    proj_id = None
    if project:
        p = db.get_project(project)
        if p:
            proj_id = p.id

    atoms = db.list_atoms(project_id=proj_id)
    if not atoms:
        console.print("[yellow]No atoms found to plan calendar. Run `lore scan` first.[/yellow]")
        return

    schedule = ContentCalendar.plan_week(atoms)
    table = Table(title="Suggested Content Calendar", show_header=True, header_style="bold yellow")
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
@click.option("--status", type=click.Choice(["approved", "drafted", "all"]), default="approved")
@click.option("--format", "format_type", type=click.Choice(["markdown", "json"]), default="markdown")
@click.option("--output-dir", "-o", default="./exports", help="Destination directory")
def cmd_export(status: str, format_type: str, output_dir: str):
    """Export approved drafts to Markdown or JSON."""
    db = Database()
    filter_status = None if status == "all" else DraftStatus(status)
    drafts = db.list_drafts(status=filter_status)

    if not drafts:
        console.print(f"[yellow]No drafts found matching status '{status}'.[/yellow]")
        return

    out_path = Path(output_dir)
    files = DraftExporter.export(drafts, out_path, format_type=format_type)

    console.print(f"[bold green]✓ Exported {len(files)} draft(s) to {out_path}[/bold green]")
    for f in files:
        console.print(f"  [dim]• {f.name}[/dim]")


if __name__ == "__main__":
    main()
