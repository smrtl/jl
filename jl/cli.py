import json
import logging
import re
from typing import IO, Any

import click
from dateutil.parser import ParserError, parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jl")

LOG_LEVELS = {
    "TRACE": ("TRACE", "cyan"),
    "DEBUG": ("DEBUG", "blue"),
    "INFO": ("INFO", "green"),
    "WARN": ("WARN", "yellow"),
    "WARNING": ("WARN", "yellow"),
    "ERROR": ("ERROR", "red"),
    "CRITICAL": ("CRIT", "red"),
    "FATAL": ("FATAL", "red"),
}
K8S_PREFIXED_LINE = re.compile(r"(\[pod/[^][]+\]\s?)(.*)")
COLORS = ["magenta", "green", "blue", "yellow", "cyan", "red"]


def parse_json(line: str) -> tuple[str | None, dict[str, Any] | None]:
    json_start = line.find("{")
    try:
        if json_start > -1:
            data = json.loads(line[json_start:])
            return line[0:json_start], data
    except json.JSONDecodeError as e:
        logger.debug("%s", e)
    return None, None


def get_value(data: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return str(value)
    return None


def get_timestamp(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    if value := get_value(data, keys):
        try:
            timestamp = parse(value)
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except ParserError as e:
            logger.debug("%s", e)
            return value[0:19]
    return ""


def get_level(data: dict[str, Any], keys: tuple[str, ...]) -> str:
    if value := get_value(data, keys):
        return value.upper()
    return "INFO"


@click.command()
@click.argument(
    "file",
    default="-",
    type=click.File("r"),
)
@click.option(
    "--timestamp",
    "-t",
    default=("asctime", "@timestamp", "timestamp"),
    multiple=True,
    help="Adds a key to detect the log time.",
)
@click.option(
    "--level",
    "-l",
    default=("levelname", "level"),
    multiple=True,
    help="Adds a key to detect the log level.",
)
@click.option(
    "--message",
    "-m",
    default=("message", "msg"),
    multiple=True,
    help="Adds a key to detect the log message.",
)
@click.option(
    "--add",
    "-a",
    multiple=True,
    help="Additional value to display if present.",
)
@click.option(
    "--ignore",
    "-i",
    is_flag=True,
    help="Ignore non JSON logs",
)
@click.option(
    "--color/--no-color",
    default=None,
    help="Force the use of colors, by default colors are disabled if not in a tty.",
)
@click.option(
    "--k8s-prefix/--no-k8s-prefix",
    default=True,
    help="Try to parse k8s multi-pods prefix. True by default",
)
@click.option(
    "--fail-on-abort/--no-fail-on-abort",
    default=True,
    help="Exits with code 0 instead of 1 when the input stream is aborted",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Turns on debug logs",
)
def main(
    file: IO[str],
    timestamp: tuple[str, ...],
    level: tuple[str, ...],
    message: tuple[str, ...],
    add: tuple[str, ...],
    ignore: bool,
    color: bool | None,
    k8s_prefix: bool,
    fail_on_abort: bool,
    debug: bool,
) -> None:
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    pod_colors: dict[str, str] = {}

    try:
        # read in put line by line
        for raw_line in file:
            # parse k8s prefix
            if k8s_prefix and (match := K8S_PREFIXED_LINE.match(raw_line)):
                pod_prefix = match.group(1)
                if pod_prefix not in pod_colors:
                    pod_colors[pod_prefix] = COLORS[len(pod_colors) % len(COLORS)]
                pod_prefix = click.style(pod_prefix, fg=pod_colors[pod_prefix], dim=True)
                line = match.group(2)
            else:
                pod_prefix = ""
                line = raw_line.strip()

            # try to guess if the line might contain json
            prefix, data = parse_json(line)

            if data:
                # extract log data
                ts = get_timestamp(data, timestamp)
                lvl = get_level(data, level)
                msg = get_value(data, message) or ""

                # format and output
                prefix = pod_prefix + click.style(prefix, fg="bright_black")
                ts = click.style(ts.ljust(20), bold=True)
                lvl_info = LOG_LEVELS.get(lvl, (lvl[0:5], "bright_magenta"))
                lvl = click.style(lvl_info[0].rjust(5), fg=lvl_info[1], bold=True)
                click.echo(f"{prefix}{ts}{lvl}: {msg}", color=color)

                for key in add:
                    if value := data.get(key):
                        name = click.style(key.rjust(25), fg="bright_black", bold=True)
                        click.echo(f"{prefix}{name}: {value}", color=color)
            elif not ignore:
                click.echo(pod_prefix + line, color=color)
    except KeyboardInterrupt:
        if fail_on_abort:
            raise
        click.echo("\nAborted!")
