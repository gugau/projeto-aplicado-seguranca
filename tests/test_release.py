"""Exercita o script real de publicação com serviços simulados, sem tocar em uma VM."""
import io
import os
from pathlib import Path
import subprocess
import stat
import sys
import tarfile

import pytest


pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="Exige filesystem/symlinks e comandos GNU Linux; executado no CI Ubuntu.")


@pytest.mark.parametrize("fail_new", [False, True])
def test_release_activation_and_automatic_rollback(tmp_path, fail_new):
    root = tmp_path / "application"
    previous = root / "releases" / "previous"
    previous.mkdir(parents=True)
    (root / "incoming").mkdir()
    (root / "current").symlink_to(previous)
    sha = "a" * 40
    with tarfile.open(root / "incoming" / f"{sha}.tar.gz", "w:gz") as archive:
        payload = b"Flask==3.1.3\n"
        entry = tarfile.TarInfo("requirements.txt")
        entry.size = len(payload)
        archive.addfile(entry, io.BytesIO(payload))
    commands = tmp_path / "commands"
    commands.mkdir()
    fake = {
        "sudo": "#!/bin/sh\nexit 0\n",
        "sleep": "#!/bin/sh\nexit 0\n",
        "curl": '#!/bin/sh\nif [ "$FAIL_NEW" = 1 ] && [ "$(readlink -f "$APP_ROOT/current")" != "$PREVIOUS" ]; then exit 22; fi\nexit 0\n',
        "python3": '#!/bin/sh\nmkdir -p "$3/bin"\nprintf "#!/bin/sh\\nexit 0\\n" > "$3/bin/python"\nchmod +x "$3/bin/python"\n',
    }
    for name, body in fake.items():
        command = commands / name
        command.write_text(body)
        command.chmod(0o755)
    env = {**os.environ, "PATH": f"{commands}:{os.environ['PATH']}", "APP_ROOT": str(root), "APP_GROUP": str(os.getgid()), "PREVIOUS": str(previous), "FAIL_NEW": "1" if fail_new else "0"}
    result = subprocess.run(["bash", str(Path(__file__).resolve().parents[1] / "deploy/release.sh"), sha], env=env, capture_output=True, text=True, timeout=15)
    release = next((root / "releases").glob(sha + ".*"))
    mode = stat.S_IMODE(release.stat().st_mode)
    # Regressão real: mktemp 0700 impedia o usuário do serviço de entrar.
    assert mode & 0o050 == 0o050
    assert mode & 0o027 == 0
    if fail_new:
        assert result.returncode != 0
        assert (root / "current").resolve() == previous
        assert "versão anterior restaurada" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        assert (root / "current").resolve().name.startswith(sha + ".")
    assert previous.is_dir()
