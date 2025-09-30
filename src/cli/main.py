import asyncio
import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ..automation.copilot_controller import CopilotController
from ..automation.ui import prepare_chat_ui
from ..utils.config import get_settings
from ..utils.logger import get_logger


console = Console()
logger = get_logger(__name__)


def run(coro):
    return asyncio.run(coro)


class GlobalState:
    def __init__(self) -> None:
        self.headless: Optional[bool] = None
        self.output_dir: Optional[Path] = None
        self.force_markdown: Optional[bool] = None
        self.normalize_markdown: Optional[bool] = None


gstate = GlobalState()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--headless/--headed", default=True, help="Run browser headless or headed")
@click.option("--output-dir", type=click.Path(file_okay=False), default=None, help="Output directory")
@click.option("--force-markdown/--no-force-markdown", default=None, help="Append instruction so Copilot responds in Markdown")
@click.option("--normalize-markdown/--raw-markdown", default=None, help="Control whether responses are post-processed into Markdown")
@click.option("--log-level", type=click.Choice(["DEBUG","INFO","WARNING","ERROR"], case_sensitive=False), default=None)
@click.pass_context
def cli(
    ctx: click.Context,
    headless: bool,
    output_dir: Optional[str],
    force_markdown: Optional[bool],
    normalize_markdown: Optional[bool],
    log_level: Optional[str],
) -> None:
    """MS365 Copilot automation CLI."""
    gstate.headless = headless
    gstate.output_dir = Path(output_dir) if output_dir else None
    gstate.force_markdown = force_markdown
    gstate.normalize_markdown = normalize_markdown
    if log_level:
        os.environ["LOG_LEVEL"] = log_level.upper()


def _apply_overrides():
    settings = get_settings()
    if gstate.headless is not None:
        os.environ["BROWSER_HEADLESS"] = "true" if gstate.headless else "false"
        settings.browser_headless = gstate.headless
    if gstate.output_dir:
        settings.output_directory = gstate.output_dir
        settings.output_directory.mkdir(parents=True, exist_ok=True)
    if gstate.force_markdown is not None:
        settings.force_markdown_responses = gstate.force_markdown
    if gstate.normalize_markdown is not None:
        settings.normalize_markdown = gstate.normalize_markdown
    return settings


@cli.command()
@click.option("--interactive", is_flag=True, help="Prompt for secrets instead of env/keyring")
@click.option("--manual", is_flag=True, help="Open headed browser and let you log in manually (keeps running)")
def auth(interactive: bool, manual: bool) -> None:
    """Authenticate and persist session."""
    settings = _apply_overrides()
    if manual:
        async def _manual():
            async with CopilotController() as ctl:
                assert ctl.page and ctl.context
                await ctl.page.goto(settings.copilot_url)
                console.print(Panel.fit("Headed browser opened. Complete login in the browser.\nThis process saves auth state periodically. Press Ctrl+C when done.", title="Manual Auth", style="cyan"))
                try:
                    while True:
                        await asyncio.sleep(5)
                        await ctl.context.storage_state(path=str(settings.storage_state_path))
                except asyncio.CancelledError:
                    pass
        try:
            run(_manual())
        except KeyboardInterrupt:
            console.print("[green]Stopped. Auth state saved to[/] [bold]playwright/auth/user.json[/].")
        return

    if interactive:
        settings.username = click.prompt("Username", type=str, default=settings.username or "")
        settings.password = click.prompt("Password", type=str, default=settings.password or "", hide_input=True)
        if click.confirm("Provide TOTP secret?", default=False):
            settings.mfa_secret = click.prompt("MFA TOTP secret", type=str, hide_input=True)

    async def _run():
        async with CopilotController() as ctl:
            await ctl.ensure_authenticated()

    run(_run())
    console.print("[green]Authenticated.[/]")


@cli.command()
@click.argument("prompt", type=str)
@click.option("--out", type=click.Path(dir_okay=False, writable=True), default=None, help="Write response to file")
def chat(prompt: str, out: Optional[str]) -> None:
    """Send a prompt and show/write the response."""
    _apply_overrides()

    async def _run():
        async with CopilotController() as ctl:
            text = await ctl.chat(prompt)
            return text

    with console.status("Contacting Copilot…", spinner="dots"):
        text = run(_run())
    if out:
        Path(out).write_text(text)
        console.print(f"[green]Wrote[/] {out}")
    else:
        console.print(Panel(Markdown(text), title="Copilot", border_style="green"))


@cli.command(name="ask-with-file")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("prompt", type=str)
@click.option("--out", type=click.Path(dir_okay=False, writable=True), default=None, help="Write response to file")
@click.option("--download", is_flag=True, help="Wait for Copilot to offer a downloadable artifact")
@click.option("--download-dir", type=click.Path(file_okay=False), default=None, help="Directory for downloaded files")
@click.option("--download-timeout", type=int, default=60, show_default=True, help="Seconds to wait for downloadable artifact")
def ask_with_file_cmd(
    file_path: str,
    prompt: str,
    out: Optional[str],
    download: bool,
    download_dir: Optional[str],
    download_timeout: int,
) -> None:
    """Upload file, ask prompt, return response."""
    settings = _apply_overrides()
    download_path = Path(download_dir) if download_dir else settings.output_directory
    if download:
        download_path.mkdir(parents=True, exist_ok=True)

    async def _run():
        async with CopilotController() as ctl:
            text = await ctl.ask_with_file(Path(file_path), prompt)
            artifact = None
            if download:
                try:
                    artifact = await ctl.download_response(
                        download_path, timeout_ms=download_timeout * 1000
                    )
                except RuntimeError as exc:
                    logger.warning("Download skipped: %s", exc)
                    artifact = None
            return text, artifact

    with console.status("Uploading file and waiting for Copilot…", spinner="dots"):
        text, artifact = run(_run())
    if out:
        Path(out).write_text(text)
        console.print(f"[green]Wrote[/] {out}")
    else:
        console.print(Panel(Markdown(text), title="Copilot", border_style="green"))
    if download:
        if artifact:
            console.print(f"[green]Downloaded[/] {artifact}")
        else:
            console.print("[yellow]Copilot did not provide a downloadable artifact within the timeout.[/]")


@cli.command()
@click.option("--out", type=click.Path(file_okay=False), default=None, help="Directory to save the download")
@click.option("--timeout", type=int, default=60, show_default=True, help="Seconds to wait for a downloadable artifact")
def download(out: Optional[str], timeout: int) -> None:
    """Download the next artifact offered in the current Copilot conversation."""
    settings = _apply_overrides()
    target_dir = Path(out) if out else settings.output_directory
    target_dir.mkdir(parents=True, exist_ok=True)

    async def _run():
        async with CopilotController() as ctl:
            await ctl.ensure_authenticated()
            assert ctl.page
            await ctl.page.goto(settings.copilot_url)
            await prepare_chat_ui(ctl.page)
            return await ctl.download_response(target_dir, timeout_ms=timeout * 1000)

    try:
        with console.status("Waiting for Copilot to provide a download…", spinner="dots"):
            path = run(_run())
    except RuntimeError as exc:
        console.print(f"[red]Download failed:[/] {exc}")
        raise SystemExit(1)
    console.print(f"[green]Downloaded[/] {path}")


if __name__ == "__main__":
    cli()
