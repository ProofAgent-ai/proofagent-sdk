import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from proofagent.cli import STARTER_CONFIG, cmd_init, main

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"


def test_cmd_init_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "proofagent.yaml"
    assert cmd_init(target, force=False) == 0
    assert target.read_text(encoding="utf-8") == STARTER_CONFIG


def test_cmd_init_refuses_existing_without_force(tmp_path: Path) -> None:
    target = tmp_path / "proofagent.yaml"
    target.write_text("existing", encoding="utf-8")
    assert cmd_init(target, force=False) == 1
    assert target.read_text(encoding="utf-8") == "existing"


def test_cmd_init_overwrites_with_force(tmp_path: Path) -> None:
    target = tmp_path / "proofagent.yaml"
    target.write_text("existing", encoding="utf-8")
    assert cmd_init(target, force=True) == 0
    assert target.read_text(encoding="utf-8") == STARTER_CONFIG


def test_main_init_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["proofagent", "init", "-o", "custom.yaml"])
    assert main() == 0
    assert (tmp_path / "custom.yaml").read_text(encoding="utf-8") == STARTER_CONFIG


def test_cli_module_invocation_smoke() -> None:
    """`python -m proofagent.cli init` works when the package is on PYTHONPATH."""
    env = {**os.environ, "PYTHONPATH": str(_SRC)}
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        result = subprocess.run(
            [sys.executable, "-m", "proofagent.cli", "init", "-o", "out.yaml"],
            cwd=td_path,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0
        out = td_path / "out.yaml"
        assert out.read_text(encoding="utf-8") == STARTER_CONFIG
