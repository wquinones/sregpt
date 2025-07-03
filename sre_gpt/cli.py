"""
SRE-GPT Typer CLI – first-run key prompt & secure storage.

First time you run and no key is found, it will:
  • Prompt for the OpenAI API key (input hidden)
  • Save it in ~/.config/sre_gpt/config.yaml with chmod 600

Output modes
------------
Default: plain key/value lines
  --cmd-only   → only the command
  --json       → raw JSON
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from openai import OpenAI
from rich.console import Console
from rich.prompt import Prompt
from rich.theme import Theme

APP_NAME = "sre_gpt"
CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.yaml"
DEFAULT_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "You are SRE-GPT, an elite site-reliability engineer. "
    "When the user asks a question, respond with JSON only, using keys: "
    "cmd, explanation, dangerous."
)

custom_theme = Theme({"danger": "bold red"})
console = Console(theme=custom_theme)
app = typer.Typer(add_completion=False)

# ─────────────────────────── helpers ─────────────────────────── #

def _load_api_key() -> str:
    """Return OpenAI key from env / file or prompt to create one."""
    if (key := os.environ.get("OPENAI_API_KEY")):
        return key

    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as f:
            if (key := (yaml.safe_load(f) or {}).get("api_key")):
                return key

    # First-run interactive setup
    console.print("[bold yellow]⚙️  OpenAI API key not found. Let's configure it now.[/bold yellow]")
    key = Prompt.ask("🔑 Enter your OpenAI API key", password=True).strip()
    if not key:
        console.print("[danger]No key entered; aborting.[/danger]")
        raise typer.Exit(1)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as f:
        yaml.safe_dump({"api_key": key}, f)
    os.chmod(CONFIG_PATH, 0o600)
    console.print(f"[green]✓ API key stored in {CONFIG_PATH} with 0600 perms.[/green]")
    return key


def _openai() -> OpenAI:
    return OpenAI(api_key=_load_api_key())


def _build_messages(prompt: str, stdin_blob: Optional[str] = None):
    msgs = [{"role": "system", "content": _SYSTEM_PROMPT}]
    content = f"STDIN:\n{stdin_blob}\n\n{prompt}" if stdin_blob else prompt
    msgs.append({"role": "user", "content": content})
    return msgs


def _ask_llm(messages, model):
    resp = _openai().chat.completions.create(
        model=model, messages=messages, temperature=0.2
    )
    return resp.choices[0].message.content

_fence_re = re.compile(r"^```(?:json)?\s*\n|\n```$", re.MULTILINE)

def _parse_llm(raw: str):
    for candidate in (raw, _fence_re.sub("", raw.strip())):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None

# ─────────────────────────── CLI ─────────────────────────── #

@app.command()
def cli(
    shell: str = typer.Option(..., "-s", "--shell", help="Prompt / question"),
    model: str = typer.Option(DEFAULT_MODEL, help="OpenAI model name"),
    json_out: bool = typer.Option(False, "--json", help="Print raw JSON output"),
    cmd_only: bool = typer.Option(False, "--cmd-only", help="Print only the generated command"),
):
    """Ask SRE-GPT and print the result in the requested format."""
    if json_out and cmd_only:
        console.print("[danger]--json and --cmd-only are mutually exclusive.[/danger]")
        raise typer.Exit(1)

    stdin_blob = None if sys.stdin.isatty() else sys.stdin.read()
    payload = _parse_llm(_ask_llm(_build_messages(shell, stdin_blob), model))

    if payload is None:
        console.print("[danger]✖  Could not parse JSON response.[/danger]")
        raise typer.Exit(1)

    cmd = payload.get("cmd", "")
    dangerous = payload.get("dangerous", False) is True

    if json_out:
        if dangerous:
            payload["dangerous"] = "***true***"
            out = json.dumps(payload, indent=2)
            out = out.replace('"***true***"', '[danger]***true***[/danger]')
            console.print(out)
        else:
            console.print(json.dumps(payload, indent=2))
        return

    if cmd_only:
        console.print(cmd)
        if dangerous:
            console.print("[danger]⚠️  Marked dangerous[/danger]")
        return

    console.print(f"cmd: {cmd}")
    console.print(f"explanation: {payload.get('explanation', '')}")
    if dangerous:
        console.print("dangerous: [danger]***true***[/danger]")
    else:
        console.print("dangerous: false")

if __name__ == "__main__":
    app()

