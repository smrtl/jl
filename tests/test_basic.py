from click.testing import CliRunner

from jl.cli import main


def test_additional() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["tests/fixtures/logs.txt", "-aimportant"])

    lines = result.output.split("\n")
    assert len(lines) == 16
    assert lines[6] == "[pod/svc-bd54fc89c-5s477/svc]                 important: yeah this is"
    assert lines[12].startswith("[pod/svc-bd54fc89c-5s477/svc] 2024-09-26 13:43:24  CRIT: ")


def test_ignore() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["tests/fixtures/logs.txt", "-i"])

    lines = result.output.split("\n")
    assert len(lines) == 10
