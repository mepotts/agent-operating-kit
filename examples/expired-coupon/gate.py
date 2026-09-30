#!/usr/bin/env python3
"""Toy exact-candidate gate for the worked example. Illustrative, standard library only.

    python gate.py <candidate-dir> --acceptance acceptance.json [--out <evidence-dir>]

Steps, in order: freeze the candidate (content hash), check the acceptance declaration covers
every file, run the tests, check every named acceptance test passed, re-hash the source.
It ends as `blocked` or `checks-passed`. It never prints `ready`: that needs an independent
evidence review, and a script cannot review itself.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

TEST_LINE = re.compile(
    r"^(\w+) \([\w.]+\) \.\.\. (ok|FAIL|ERROR|skipped .*|expected failure|unexpected success)$", re.M
)


def content_hash(root: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(root.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        h.update(p.relative_to(root).as_posix().encode())
        h.update(p.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def run_tests(root: Path):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-v"],
        cwd=root, capture_output=True, text=True, timeout=120, env=env,
    )
    output = proc.stdout + proc.stderr
    return proc.returncode, output, {m.group(1): m.group(2) for m in TEST_LINE.finditer(output)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--acceptance", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    root = args.candidate.resolve()
    declaration = json.loads(args.acceptance.read_text(encoding="utf-8"))
    problems: list[str] = []

    # 1. Freeze: hash the source before anything runs.
    frozen = content_hash(root)
    print(f"candidate      {args.candidate}")
    print(f"content hash   {frozen}")

    # 2. The declaration must cover every source file.
    files = {p.relative_to(root).as_posix() for p in root.rglob("*.py") if "__pycache__" not in p.parts}
    for uncovered in sorted(files - set(declaration["files"])):
        problems.append(f"file not covered by the acceptance declaration: {uncovered}")

    # 3. Run the tests. Anything other than a plain pass blocks: skips, failures, errors, zero tests.
    code, output, results = run_tests(root)
    counts = {}
    for status in results.values():
        key = "skipped" if status.startswith("skipped") else status
        counts[key] = counts.get(key, 0) + 1
    print(f"tests          {len(results)} found, {counts}")
    if not results:
        problems.append("zero tests found")
    for name, status in results.items():
        if status != "ok":
            problems.append(f"test {name}: {status}, not passed")
    if code != 0 and not any("test " in p for p in problems):
        problems.append(f"test runner exited {code}")

    # 4. Acceptance evidence: every named test must appear in the results as passed.
    for crit in declaration["criteria"]:
        for name in crit["tests"]:
            status = results.get(name)
            if status is None:
                problems.append(f"{crit['id']} ({crit['intent']}): test {name} was never run")
            elif status != "ok":
                problems.append(f"{crit['id']} ({crit['intent']}): test {name} is {status}")

    # 5. Source stability: the candidate must be byte-for-byte what was frozen.
    if content_hash(root) != frozen:
        problems.append("source changed during the run; the run is void")

    state = "blocked" if problems else "checks-passed"
    for p in problems:
        print(f"  BLOCK  {p}")
    if state == "checks-passed":
        print("STATE: checks-passed (not ready: independent evidence review still required)")
    else:
        print("STATE: blocked")

    if args.out:
        evidence = args.out / frozen[:8]
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / "tests.txt").write_text(output, encoding="utf-8")
        report = {
            "candidate": args.candidate.name,
            "contentHash": frozen,
            "state": state,
            "problems": problems,
            "testsOutputSha256": hashlib.sha256(output.encode()).hexdigest(),
        }
        (evidence / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"evidence       {evidence}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
