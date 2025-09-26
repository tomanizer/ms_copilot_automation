import asyncio
from pathlib import Path
from typing import Optional

import click

from ..automation.copilot_controller import CopilotController
from ..utils.config import get_settings
from ..utils.logger import get_logger


logger = get_logger(__name__)


def run(coro):
    return asyncio.run(coro)


@click.group()
def cli() -> None:
    """MS365 Copilot automation CLI."""


@cli.command()
@click.option("--interactive", is_flag=True, help="Prompt for secrets instead of env/keyring")
@click.option("--manual", is_flag=True, help="Open headed browser and let you log in manually (non-interactive, keeps running)")
def auth(interactive: bool, manual: bool) -> None:
    """Authenticate and persist session."""
    settings = get_settings()
    if manual:
        async def _manual():
            async with CopilotController() as ctl:
                assert ctl.page and ctl.context
                await ctl.page.goto(settings.copilot_url)
                click.echo("Headed browser opened. Manually complete Microsoft login in the browser.")
                click.echo("This process will keep running and periodically save authentication state.")
                # Periodically persist storage state until interrupted
                try:
                    while True:
                        await asyncio.sleep(5)
                        await ctl.context.storage_state(path=str(settings.storage_state_path))
                except asyncio.CancelledError:
                    pass
        run(_manual())
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
    click.echo("Authenticated.")


@cli.command()
@click.argument("prompt", type=str)
@click.option("--out", type=click.Path(dir_okay=False, writable=True), default=None, help="Write response to file")
def chat(prompt: str, out: Optional[str]) -> None:
    """Send a prompt and print/write the response."""
    async def _run():
        async with CopilotController() as ctl:
            text = await ctl.chat(prompt)
            return text

    text = run(_run())
    if out:
        Path(out).write_text(text)
        click.echo(f"Wrote {out}")
    else:
        click.echo(text)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
def upload(file_path: str) -> None:
    """Upload a file (smoke)."""
    async def _run():
        async with CopilotController() as ctl:
            await ctl.ask_with_file(Path(file_path), "")

    run(_run())
    click.echo("Uploaded.")


@cli.command(name="ask-with-file")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("prompt", type=str)
@click.option("--out", type=click.Path(dir_okay=False, writable=True), default=None, help="Write response to file")
def ask_with_file_cmd(file_path: str, prompt: str, out: Optional[str]) -> None:
    """Upload file, ask prompt, return response."""
    async def _run():
        async with CopilotController() as ctl:
            text = await ctl.ask_with_file(Path(file_path), prompt)
            return text

    text = run(_run())
    if out:
        Path(out).write_text(text)
        click.echo(f"Wrote {out}")
    else:
        click.echo(text)


if __name__ == "__main__":
    cli()
