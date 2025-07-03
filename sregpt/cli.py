"""
sregpt – AI CLI Assistant for SRE / Sysadmin teams
(renamed package; web-UI version)
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
from typing import Optional
import typer, yaml
from openai import OpenAI
from rich.console import Console
from rich.prompt import Prompt
from rich.theme import Theme

APP_NAME = "sregpt"  # ← updated
CONFIG_PATH = Path.home() / ".config" / APP_NAME / "config.yaml"
DEFAULT_MODEL = "gpt-4o-mini"

_SYSTEM_PROMPT = (
    "You are SRE-GPT, an elite site-reliability engineer. "
    "When the user asks a question, respond with JSON only, with keys: "
    "cmd, explanation, dangerous."
)

console = Console(theme=Theme({"danger": "bold red"}))
app = typer.Typer(add_completion=False)

# ---------- key helper ----------
def _load_api_key() -> str:
    if (k := os.environ.get("OPENAI_API_KEY")):
        return k
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as f:
            if (k := (yaml.safe_load(f) or {}).get("api_key")):
                return k
    console.print("[yellow]⚙️  No OpenAI key, please enter it:[/yellow]")
    k = Prompt.ask("🔑  OpenAI API key", password=True).strip()
    if not k:
        raise typer.Exit("No key entered.")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w") as f:
        yaml.safe_dump({"api_key": k}, f)
    os.chmod(CONFIG_PATH, 0o600)
    console.print(f"[green]✓ Stored at {CONFIG_PATH}[/green]")
    return k

def _openai() -> OpenAI:
    return OpenAI(api_key=_load_api_key())

def _ask_llm(prompt: str, stdin: Optional[str], model: str):
    msgs = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": f"STDIN:\n{stdin}\n\n{prompt}" if stdin else prompt},
    ]
    rsp = _openai().chat.completions.create(model=model, messages=msgs, temperature=0.2)
    return rsp.choices[0].message.content

_fence = re.compile(r"^```(?:json)?\s*\n|\n```$", re.MULTILINE)
def _parse(raw: str):
    for c in (raw, _fence.sub("", raw.strip())):
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    return None

# ---------- CLI ----------
@app.command()
def cli(
    shell: str = typer.Option(..., "-s", "--shell", help="Prompt / question"),
    model: str = typer.Option(DEFAULT_MODEL, help="OpenAI model"),
    json_out: bool = typer.Option(False, "--json", help="Raw JSON output"),
    cmd_only: bool = typer.Option(False, "--cmd-only", help="Only the command"),
):
    if json_out and cmd_only:
        console.print("[danger]--json and --cmd-only conflict[/danger]"); raise typer.Exit()
    payload = _parse(_ask_llm(shell, None if sys.stdin.isatty() else sys.stdin.read(), model))
    if payload is None:
        console.print("[danger]✖ parse error[/danger]"); raise typer.Exit()
    cmd, dangerous = payload.get("cmd", ""), payload.get("dangerous", False)
    if json_out:
        console.print(json.dumps(payload, indent=2)); return
    if cmd_only:
        console.print(cmd); return
    console.print(f"cmd: {cmd}")
    console.print(f"explanation: {payload.get('explanation','')}")
    console.print("dangerous:", "[danger]***true***[/danger]" if dangerous else "false")

if __name__ == "__main__":
    app()
