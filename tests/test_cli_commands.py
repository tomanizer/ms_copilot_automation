from click.testing import CliRunner

from src.cli.main import cli


def test_cli_registers_expected_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    for command in ("chat", "ask-with-file", "download", "auth"):
        assert command in cli.commands
