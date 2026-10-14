"""Shared CLI adapters. Prompts go on stdin; imports never write bytecode."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile

DEFAULT_MODELS = {"claude": "sonnet", "codex": "", "command": ""}


def execute(command, cwd, timeout, prompt=None, shell=False):
    """Run and reap the entire process group, including on timeout/interruption."""
    proc = subprocess.Popen(command, shell=shell, cwd=cwd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, start_new_session=True)
    try:
        out, err = proc.communicate(prompt, timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        out, err = proc.communicate()
        return 124, out, err + f"\nTIMEOUT after {timeout}s"
    finally:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()


def ask(prompt, agent="claude", model=None, effort="medium", command=None,
        cwd=None, timeout=900, edit=False):
    cwd = Path(cwd or Path.cwd()).resolve()
    model = model or DEFAULT_MODELS[agent]
    # Keep runtime artifacts in the caller's workspace, never in the skill.
    with tempfile.TemporaryDirectory(prefix=".lab-cli-", dir=cwd) as temp:
        if agent == "claude":
            config = Path(temp) / "mcp.json"
            config.write_text('{"mcpServers": {}}\n')
            args = ["claude", "--print", "--model", model, "--effort", effort,
                    "--strict-mcp-config", "--mcp-config", str(config),
                    "--no-session-persistence", "--disable-slash-commands",
                    "--setting-sources", "", "--tools", "Read,Edit,Write" if edit else ""]
            if edit:
                args += ["--permission-mode", "acceptEdits"]
        elif agent == "codex":
            output = Path(temp) / "answer.txt"
            args = ["codex", "exec", "--ignore-user-config", "--ephemeral",
                    "--sandbox", "workspace-write" if edit else "read-only",
                    "-c", 'approval_policy="never"', "-c", 'features.multi_agent=false',
                    "-c", f"model_reasoning_effort={json.dumps(effort)}",
                    "--cd", str(cwd), "--skip-git-repo-check",
                    "--output-last-message", str(output)]
            if model:
                args += ["--model", model]
            args += ["-"]
        elif agent == "command":
            if not command:
                raise ValueError("agent=command requires command")
            args = command
        else:
            raise ValueError(f"unknown agent: {agent}")
        code, out, err = execute(args, cwd, timeout, prompt, shell=agent == "command")
        if agent == "codex" and output.exists():
            out = output.read_text()
        return code, out, err


def judge_options(parser):
    parser.add_argument("--agent", choices=["claude", "codex", "command"], default="claude")
    parser.add_argument("--command", help="shell command receiving the prompt on stdin")
    parser.add_argument("--model", help="defaults: sonnet for Claude; the CLI default for Codex")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--timeout", type=float, default=900)


def judge_answer(prompt, args):
    code, out, err = ask(prompt, args.agent, args.model, args.effort, args.command,
                         timeout=args.timeout)
    if code:
        raise RuntimeError(f"judge exited {code}: {err}\n{out}")
    return out
