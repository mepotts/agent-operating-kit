"""Self-test for scripts/validate.py: every rule must fire on a planted defect and stay quiet on the clean tree.

    python -m unittest discover -s scripts -p "test_*.py" -v

This is the kit's own "break it, confirm red" proof. A validator that has never been seen to fail proves nothing:
generated or hand-written rules can pass vacuously, so each rule gets a mutation that must turn it red. A mutation
that changes nothing is itself an error (it would make the test pass for the wrong reason).
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import validate  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", "__pycache__", "results", "node_modules")
EMOJI = chr(0x1F600)


def fresh_copy(tmp: str) -> Path:
    dst = Path(tmp) / "kit"
    shutil.copytree(ROOT, dst, ignore=IGNORE)
    return dst


def edit(root: Path, rel: str, fn) -> None:
    p = root / rel
    old = p.read_text(encoding="utf-8")
    new = fn(old)
    assert new != old, f"mutation left {rel} unchanged, so it would prove nothing"
    p.write_text(new, encoding="utf-8", newline="\n")


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def drop_line(prefix: str):
    return lambda t: re.sub(r"^" + re.escape(prefix) + r".*\n", "", t, count=1, flags=re.M)


SKILL = "skills/sprint-spec/SKILL.md"
GATE = "examples/expired-coupon/gate.py"
NEW_COMMAND = "---\ndescription: A command that collides with a skill\ndisable-model-invocation: true\n---\nBody.\n"

# (rule id, what is planted, mutation)
MUTATIONS = [
    ("M01", "invalid JSON in plugin.json", lambda r: write(r, ".claude-plugin/plugin.json", "{ not json")),
    ("M02", "plugin name with a space and capitals", lambda r: edit(r, ".claude-plugin/plugin.json", lambda t: t.replace('"agent-operating-kit"', '"Bad Name"', 1))),
    ("M03", "displayName key (rejected by Claude Code 2.1.39)", lambda r: edit(r, ".claude-plugin/plugin.json", lambda t: t.replace('"version"', '"displayName": "X",\n  "version"', 1))),
    ("M04", "version without a CHANGELOG entry", lambda r: edit(r, ".claude-plugin/plugin.json", lambda t: t.replace('"0.1.0"', '"9.9.9"', 1))),
    ("M05", "license changed from MIT", lambda r: edit(r, ".claude-plugin/plugin.json", lambda t: t.replace('"MIT"', '"Apache-2.0"', 1))),
    ("M06", "invalid JSON in marketplace.json", lambda r: write(r, ".claude-plugin/marketplace.json", "[]")),
    ("M07", "reserved marketplace name", lambda r: edit(r, ".claude-plugin/marketplace.json", lambda t: t.replace('"name": "agent-operating-kit",\n  "description"', '"name": "claude-plugins-official",\n  "description"', 1))),
    ("M08", "marketplace entry name differs from the plugin", lambda r: edit(r, ".claude-plugin/marketplace.json", lambda t: t.replace('"name": "agent-operating-kit",\n      "source"', '"name": "other-plugin",\n      "source"', 1))),
    ("M09", "version duplicated in the marketplace entry", lambda r: edit(r, ".claude-plugin/marketplace.json", lambda t: t.replace('"source": "./",', '"source": "./",\n      "version": "0.1.0",', 1))),
    ("M10", "homepage that is not an https URL", lambda r: edit(r, ".claude-plugin/plugin.json", lambda t: t.replace("https://github.com/mepotts/agent-operating-kit", "not a url", 1))),
    ("C01", "YAML hazard (colon-space) in a skill description", lambda r: edit(r, SKILL, lambda t: t.replace("Write a sprint spec before", "Write a sprint spec: before", 1))),
    ("C01", "skill without a name", lambda r: edit(r, SKILL, drop_line("name:"))),
    ("C02", "misspelled skill field, silently ignored at runtime", lambda r: edit(r, "skills/handoff/SKILL.md", lambda t: t.replace("\n---\n\n#", "\ndisable_model_invocation: true\n---\n\n#", 1))),
    ("C03", "skill description with no trigger", lambda r: edit(r, SKILL, lambda t: re.sub(r"Use when[^\n]*", "", t, count=1))),
    ("C04", "skill far over the line budget", lambda r: edit(r, SKILL, lambda t: t + "\n- filler line" * 120)),
    ("C05", "command that the model may invoke", lambda r: edit(r, "commands/gate.md", drop_line("disable-model-invocation:"))),
    ("C06", "command with the same name as a skill", lambda r: write(r, "commands/handoff.md", NEW_COMMAND)),
    ("C07", "plugin agent with an ignored permissionMode", lambda r: edit(r, "agents/auditor.md", lambda t: t.replace("color: blue", "color: blue\npermissionMode: bypassPermissions", 1))),
    ("C08", "reviewer granted the Write tool", lambda r: edit(r, "agents/refuting-reviewer.md", lambda t: t.replace("tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob, Bash, Write", 1))),
    ("C09", "agent colored red", lambda r: edit(r, "agents/refuting-reviewer.md", lambda t: t.replace("color: orange", "color: red", 1))),
    ("C10", "a hooks directory shipped", lambda r: write(r, "hooks/hooks.json", '{"hooks": {}}')),
    ("C11", "CLAUDE.md at the plugin root", lambda r: write(r, "CLAUDE.md", "# not loaded\n")),
    ("L01", "broken relative link", lambda r: edit(r, "README.md", lambda t: t + "\n[gone](docs/gone.md)\n")),
    ("L02", "CLAUDE_PLUGIN_ROOT path that does not exist", lambda r: edit(r, SKILL, lambda t: t + "\nSee `${CLAUDE_PLUGIN_ROOT}/templates/NOPE.md`.\n")),
    ("L03", "backticked repo path that does not exist", lambda r: edit(r, "README.md", lambda t: t + "\nSee `templates/NOPE.md`.\n")),
    ("D01", "README without a Limitations section", lambda r: edit(r, "README.md", lambda t: re.sub(r"^## Limitations.*$", "## Notes", t, count=1, flags=re.M))),
    ("D02", "README over the word budget", lambda r: edit(r, "README.md", lambda t: t + "\n" + "word " * 1000)),
    ("D03", "mermaid diagram with a red fill", lambda r: edit(r, "README.md", lambda t: t.replace("flowchart LR", "flowchart LR\n  style S fill:#ff0000", 1))),
    ("D04", "README without the provenance statement", lambda r: edit(r, "README.md", lambda t: t.replace("wrote this kit's files under my direction", "helped", 1))),
    ("D05", "GATE template missing a section", lambda r: edit(r, "templates/GATE.md", lambda t: t.replace("## 9. Repair loop", "## 9. Notes", 1))),
    ("D06", "tier table drifted from the template", lambda r: edit(r, "skills/risk-tiers/SKILL.md", lambda t: t.replace("| 0 | Docs, copy, non-behavioral |", "| 0 | Docs only |", 1))),
    ("D07", "LICENSE that is not MIT", lambda r: write(r, "LICENSE", "Apache License\n")),
    ("D08", "CHANGELOG deleted", lambda r: (r / "CHANGELOG.md").unlink()),
    ("D09", "VERIFICATION.md deleted", lambda r: (r / "VERIFICATION.md").unlink()),
    ("H01", "absolute personal path in a doc", lambda r: edit(r, "README.md", lambda t: t + "\nsee C:\\Users\\someone\\notes\n")),
    ("H02", "secret-like string in a doc", lambda r: edit(r, "README.md", lambda t: t + "\nkey AKIA" + "ABCDEFGHIJKLMNOP\n")),
    ("H03", "emoji in a doc", lambda r: edit(r, "README.md", lambda t: t + "\nDone " + EMOJI + "\n")),
    ("H04", "a hit from the local denylist", lambda r: write(r, ".leak-denylist.local", "sprint-spec\n")),
    ("E01", "eval case without graders", lambda r: shutil.rmtree(r / "evals/handoff-fires/graders")),
    ("E02", "unknown key in an eval prompt", lambda r: edit(r, "evals/handoff-fires/prompt.md", lambda t: t.replace("max_turns: 12", "max_turns: 12\nmaxturns: 5", 1))),
    ("E03", "grader with an undocumented type", lambda r: edit(r, "evals/handoff-fires/graders/skill-fired.md", lambda t: t.replace("type: tool_used", "type: exact_match", 1))),
    ("E03", "grader with a regex that does not compile", lambda r: edit(r, "evals/handoff-fires/graders/next-action.md", lambda t: t.replace("pattern: 'next", "pattern: '(next", 1))),
    ("E04", "no eval case expects a skill to fire", lambda r: shutil.rmtree(r / "evals/handoff-fires")),
    ("E04", "no negative case", lambda r: shutil.rmtree(r / "evals/unrelated-request-quiet")),
    ("E05", "planted-defect case without a control", lambda r: shutil.rmtree(r / "evals/reviewer-accepts-true-claim")),
    ("E06", "evals/results not ignored", lambda r: edit(r, ".gitignore", lambda t: t.replace("evals/results/", "evals/other/", 1))),
    ("E07", "eval fixture drifted from the example candidate", lambda r: edit(r, "examples/expired-coupon/candidate-a/pricing.py", lambda t: t.replace("coupon expired", "coupon has expired", 1))),
    ("X01", "gate that never blocks", lambda r: edit(r, GATE, lambda t: t.replace('state = "blocked" if problems else "checks-passed"', 'state = "checks-passed"').replace("return 1 if problems else 0", "return 0"))),
    ("X02", "gate that declares ready", lambda r: edit(r, GATE, lambda t: t.replace('"STATE: checks-passed (not ready: independent evidence review still required)"', '"STATE: ready"'))),
    ("X03", "gate that ignores skipped tests", lambda r: edit(r, GATE, lambda t: t.replace('if status != "ok":\n            problems.append(f"test {name}: {status}, not passed")', "pass").replace('elif status != "ok":\n                problems.append(f"{crit[\'id\']} ({crit[\'intent\']}): test {name} is {status}")', "pass"))),
    ("X04", "example README with a stale hash", lambda r: edit(r, "examples/expired-coupon/README.md", lambda t: re.sub(r"(content hash\s+)[0-9a-f]{64}", lambda m: m.group(1) + "0" * 64, t, count=1))),
    ("X05", "example without the Illustrative label", lambda r: edit(r, "examples/expired-coupon/README.md", lambda t: t.replace("Illustrative.", "Sample.", 1))),
]


def failed_ids(root: Path) -> set[str]:
    return {r.id for r in validate.run(root, run_example=True) if not r.ok}


class ValidatorSelfTest(unittest.TestCase):
    def test_clean_tree_passes_every_rule(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(failed_ids(fresh_copy(tmp)), set())

    def test_every_rule_fires_on_its_planted_defect(self):
        for rid, what, mutate in MUTATIONS:
            with self.subTest(rule=rid, planted=what), tempfile.TemporaryDirectory() as tmp:
                root = fresh_copy(tmp)
                mutate(root)
                self.assertIn(rid, failed_ids(root), f"{rid} stayed green with a planted defect: {what}")

    def test_every_rule_has_at_least_one_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            all_ids = {r.id for r in validate.run(fresh_copy(tmp), run_example=True)}
        self.assertEqual(all_ids - {rid for rid, _, _ in MUTATIONS}, set(), "rules with no failing fixture")

    def test_cli_exits_nonzero_on_failure_and_zero_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = fresh_copy(tmp)
            clean = subprocess.run([sys.executable, str(HERE / "validate.py"), "--root", str(root)], capture_output=True, text=True)
            self.assertEqual(clean.returncode, 0, clean.stdout[-400:])
            write(root, "CLAUDE.md", "# x\n")
            broken = subprocess.run([sys.executable, str(HERE / "validate.py"), "--root", str(root)], capture_output=True, text=True)
            self.assertEqual(broken.returncode, 1)
            self.assertIn("FAIL C11", broken.stdout)

    def test_gate_blocks_a_skip_added_to_the_fixed_candidate(self):
        """The example's own break-it proof, run directly rather than through the validator."""
        with tempfile.TemporaryDirectory() as tmp:
            root = fresh_copy(tmp)
            ex = root / "examples" / "expired-coupon"
            edit(root, "examples/expired-coupon/candidate-b/test_pricing.py", lambda t: t.replace(
                "    def test_checkout_accepts_coupon_on_its_last_day", '    @unittest.skip("planted")\n    def test_checkout_accepts_coupon_on_its_last_day', 1))
            r = subprocess.run([sys.executable, str(ex / "gate.py"), str(ex / "candidate-b"), "--acceptance", str(ex / "acceptance.json")], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("STATE: blocked", r.stdout)


if __name__ == "__main__":
    unittest.main()
