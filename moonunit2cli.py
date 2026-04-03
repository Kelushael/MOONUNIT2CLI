#!/usr/bin/env python3
"""
moonunit2cli.py
MOONUNIT2 — Sovereign AI Agent
Type the alias. It boots. You're in. That's it.
"""

import sys
import os
import time
import threading
from pathlib import Path

AGENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(AGENT_DIR))

import chat
import serve
import config
from agent import Agent


MODELS_DIR   = Path.home() / "models"
DEFAULT_MODEL = MODELS_DIR / "current.gguf"
CODER_MODEL  = MODELS_DIR / "coder.gguf"

ORANGE = chat.NEON_ORANGE
RESET  = chat.RESET
DIM    = chat.DIM
BOLD   = chat.BOLD


# ============================================================
# ASCII launch sequence
# ============================================================

FRAMES = [
    r"""
     ___  ___                   _   _       _ _   ___
    |   \/   |                 | | | |     (_) | |_  |
    | |\  /| | ___   ___  _ __ | | | |_ __  _| |_  | |
    | | \/ | |/ _ \ / _ \| '_ \| | | | '_ \| | __| | |
    | |    | | (_) | (_) | | | | |_| | | | | | |_ _| |
    |_|    |_|\___/ \___/|_| |_|\___/|_| |_|_|\__|___|
    """,
    r"""
    ╔╦╗╔═╗╔═╗╔╗╔╦ ╦╔╗╔╦╔╦╗╔═╗
    ║║║║ ║║ ║║║║║ ║║║║║ ║ ╠╣
    ╩ ╩╚═╝╚═╝╝╚╝╚═╝╝╚╝╩ ╩ ╚═╝
         SOVEREIGN AGENT
    """,
    r"""
    +-+-+-+-+-+-+-+-+-+
    |M|O|O|N|U|N|I|T|2|
    +-+-+-+-+-+-+-+-+-+
     S O V E R E I G N
    """,
]

LOADING_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def _play_launch_sequence(server_ready_event):
    """Play ASCII art while model loads in background."""

    # Frame 1
    for line in FRAMES[0].split("\n"):
        print(f"{ORANGE}{line}{RESET}", flush=True)
        time.sleep(0.04)

    time.sleep(0.3)

    # Frame 2
    for line in FRAMES[1].split("\n"):
        print(f"{BOLD}{ORANGE}{line}{RESET}", flush=True)
        time.sleep(0.06)

    time.sleep(0.3)

    # Frame 3
    for line in FRAMES[2].split("\n"):
        print(f"{ORANGE}{line}{RESET}", flush=True)
        time.sleep(0.08)

    time.sleep(0.4)

    # Spin while waiting for model
    spin_i = 0
    while not server_ready_event.is_set():
        spinner = LOADING_FRAMES[spin_i % len(LOADING_FRAMES)]
        print(f"\r  {ORANGE}{spinner}{RESET}  {DIM}loading model...{RESET}", end="", flush=True)
        spin_i += 1
        time.sleep(0.1)

    # Clear spinner line
    print(f"\r  {chat.NEON_GREEN}✓{RESET}  model ready{' ' * 20}", flush=True)


# ============================================================
# Model check
# ============================================================

def _ensure_model():
    if CODER_MODEL.exists() and CODER_MODEL.stat().st_size > 1_000_000_000:
        if not DEFAULT_MODEL.exists() or DEFAULT_MODEL.resolve() != CODER_MODEL.resolve():
            if DEFAULT_MODEL.is_symlink():
                DEFAULT_MODEL.unlink()
            DEFAULT_MODEL.symlink_to(CODER_MODEL)
        return True
    if DEFAULT_MODEL.exists() and DEFAULT_MODEL.stat().st_size > 100_000_000:
        return True
    return False


# ============================================================
# Boot
# ============================================================

def boot():
    import requests

    # Check remote first — it's faster than local on this hardware
    remote_url = config.get("remote.url", "https://axismundi.fun/v1/chat/completions")
    try:
        r = requests.get(remote_url.replace("/v1/chat/completions", "/health"), timeout=5)
        remote_ok = r.status_code == 200
    except Exception:
        remote_ok = False

    model_ready = _ensure_model()

    # Remote preferred. Only start local server if remote is down.
    server_ready = threading.Event()
    existing = serve.find_existing_server(
        port=config.get("model.port", 8181),
        host=config.get("model.host", "127.0.0.1")
    )

    if remote_ok:
        config.set_value("agent.use_remote", True, source="boot")
        server_ready.set()
    elif existing:
        config.set_value("agent.use_remote", False, source="boot")
        server_ready.set()
    elif model_ready:
        config.set_value("agent.use_remote", False, source="boot")
        def _start_server():
            s = serve.ModelServer()
            s.start(quiet=True)
            server_ready.set()
        t = threading.Thread(target=_start_server, daemon=True)
        t.start()
    else:
        server_ready.set()

    # Play launch sequence while server loads (if needed)
    _play_launch_sequence(server_ready)

    chat.blank()
    chat.status_dot(f"Remote ({remote_url.split('/')[2]})", ok=remote_ok)
    chat.status_dot("Local model", ok=model_ready or existing)
    if remote_ok:
        chat.out(f"  {chat.DIM}using remote{chat.RESET}")
    elif existing or model_ready:
        chat.out(f"  {chat.DIM}using local (slow on CPU){chat.RESET}")
    else:
        chat.out(f"  {chat.BRIGHT_RED}no backend available{chat.RESET}")
    chat.blank()

    return remote_ok


def teardown():
    pass


# ============================================================
# Interactive chat loop
# ============================================================

def chat_loop(agent):
    chat.out(chat.muted("  /help  /status  /ssh  /remote  /release  /exit"))
    chat.blank()

    while True:
        try:
            user_input = chat.prompt_input("you > ")
        except (EOFError, KeyboardInterrupt):
            chat.blank()
            chat.system_msg("Goodbye.")
            break

        if user_input is None:
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit", "exit", "quit"):
            chat.system_msg("Goodbye.")
            break

        elif user_input.lower() == "/help":
            chat.blank()
            chat.out(chat.orange("  Commands"))
            chat.bullet("/status     — agent + server status")
            chat.bullet("/ssh        — connect to remote server")
            chat.bullet("/remote     — switch to remote inference")
            chat.bullet("/local      — switch to local inference")
            chat.bullet("/release    — publish tested artifact to release hub")
            chat.bullet("/exit       — exit")
            chat.blank()
            chat.out(chat.muted("  Everything else goes straight to the agent."))
            chat.blank()
            continue

        elif user_input.lower() == "/status":
            _show_status(agent)
            continue

        elif user_input.lower().startswith("/ssh"):
            rest = user_input[4:].strip()
            user_input = f"SSH connect to {rest}" if rest else \
                         "Connect to the remote server via SSH. You know the domain and the user."

        elif user_input.lower() == "/remote":
            config.set_value("agent.use_remote", True, source="cli")
            chat.out(chat.success("  Switched to remote inference"))
            continue

        elif user_input.lower() == "/local":
            config.set_value("agent.use_remote", False, source="cli")
            chat.out(chat.success("  Switched to local inference"))
            continue

        elif user_input.lower().startswith("/release"):
            rest = user_input[8:].strip()
            user_input = f"Run tests on {rest if rest else 'the current project'}. If all tests pass, publish it to the release hub at markyninox.com. Do not publish if any test fails."

        chat.blank()
        response = agent.send(user_input)
        if response:
            chat.blank()
            chat.agent_msg(response)
        chat.blank()


# ============================================================
# Status display
# ============================================================

def _show_status(agent):
    chat.blank()
    chat.header("Status")

    server = serve.ModelServer()
    status = server.get_status()
    chat.label("Local server", "running" if status["healthy"] else "down",
               val_color=chat.NEON_GREEN if status["healthy"] else chat.BRIGHT_RED)
    chat.label("Port", str(status["port"]))

    remote_url = config.get("remote.url", "https://axismundi.fun/v1/chat/completions")
    use_remote = config.get("agent.use_remote", False)
    chat.label("Remote", remote_url.split("/")[2])
    chat.label("Using remote", str(use_remote))

    import memory as mem
    chat.label("Memories", str(mem.count()))

    import context_engine
    ctx = context_engine.get_active_context()
    chat.label("Active context", f"{ctx['count']} chunks ({ctx['pressure']:.0%} pressure)")

    import tool_registry
    chat.label("Dynamic tools", str(len(tool_registry.list_dynamic_tools())))

    chat.blank()


# ============================================================
# Self-install — script bends the system to its will
# ============================================================

ALIAS_NAME = "moonunit2"

def _self_install():
    """Ensure the script is executable and aliased system-wide."""
    script_path = Path(__file__).resolve()
    changed = False

    # Ensure executable
    if not os.access(script_path, os.X_OK):
        os.chmod(script_path, script_path.stat().st_mode | 0o755)
        changed = True

    # Determine best symlink location
    user_bin = Path.home() / ".local" / "bin"
    system_bin = Path("/usr/local/bin")

    # Try user-local first (no sudo needed), then system
    for bin_dir in [user_bin, system_bin]:
        link = bin_dir / ALIAS_NAME
        if link.is_symlink() or link.exists():
            if link.is_symlink() and link.resolve() == script_path:
                return  # Already correct
            # Wrong target — fix it
            try:
                link.unlink()
            except PermissionError:
                continue
        try:
            bin_dir.mkdir(parents=True, exist_ok=True)
            link.symlink_to(script_path)
            # Ensure ~/.local/bin is in PATH
            if bin_dir == user_bin:
                _ensure_path(user_bin)
            changed = True
            break
        except PermissionError:
            continue

    if changed:
        chat.system_msg(f"Installed: {ALIAS_NAME}")


def _ensure_path(bin_dir):
    """Ensure bin_dir is in PATH via shell rc file."""
    path_dirs = os.environ.get("PATH", "").split(":")
    if str(bin_dir) in path_dirs:
        return
    # Add to bashrc/zshrc
    for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
        if rc.exists():
            content = rc.read_text()
            export_line = f'export PATH="$HOME/.local/bin:$PATH"'
            if export_line not in content and str(bin_dir) not in content:
                with open(rc, "a") as f:
                    f.write(f"\n# Added by {ALIAS_NAME}\n{export_line}\n")


# ============================================================
# Entry point
# ============================================================

def main():
    _self_install()
    boot()
    agent = Agent()
    try:
        chat_loop(agent)
    finally:
        teardown()


if __name__ == "__main__":
    main()
