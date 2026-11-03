"""Verifica nomes de arquivos e padrões de credenciais; nunca imprime seus valores."""
import argparse
from pathlib import Path
import re
import subprocess


PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})"),
    "aws-access-id": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    prefix = ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root)]
    def git(*arguments):
        return subprocess.check_output([*prefix, *arguments])
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")
    failures = []
    for name in filter(None, names):
        path = Path(name)
        forbidden = (path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example") or path.suffix in (".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3") or any(p in path.parts for p in (".oci", ".aws", ".cache")))
        if forbidden:
            failures.append((name, "forbidden-path"))
        file = root / path
        if file.is_file():
            for detector, regex in PATTERNS.items():
                if regex.search(file.read_bytes()):
                    failures.append((name, detector))
    if args.history:
        for entry in git("rev-list", "--objects", "--all").decode().splitlines():
            parts = entry.split(" ", 1)
            if len(parts) != 2:
                continue
            obj, name = parts
            if git("cat-file", "-t", obj).strip() != b"blob":
                continue
            data = git("cat-file", "blob", obj)
            for detector, regex in PATTERNS.items():
                if regex.search(data):
                    failures.append((f"history:{obj[:12]}:{name}", detector))
    for name, detector in failures:
        print(f"FALHA {detector}: {name}")
    if failures:
        raise SystemExit(1)
    print("Nenhum padrão de credencial detectado no escopo examinado (verificação heurística).")


if __name__ == "__main__":
    main()
