#!/usr/bin/env python3
"""Validate the agent-operating-kit repository. Standard library only.

    python scripts/validate.py [--root PATH] [--no-example]

Prints one line per rule and exits 1 if any rule fails. Every rule has an id, so a failure
names the rule that fired. scripts/test_validate.py proves each rule fires on a planted defect
and stays quiet on the clean tree.

This complements `claude plugin validate`, which is the authority on manifest and frontmatter
syntax. The official validator silently accepts a misspelled skill field (ignored at runtime)
and the agent fields that plugin agents ignore, and it does not look at links, README shape,
template drift, hygiene or the eval suite. This script does.
"""
from __future__ import annotations

import difflib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# ---- documented facts this script enforces (source: code.claude.com/docs, plugins and skills) ----
SKILL_FIELDS = {
    "name", "description", "when_to_use", "argument-hint", "arguments", "disable-model-invocation",
    "user-invocable", "allowed-tools", "disallowed-tools", "model", "effort", "context", "agent",
    "background", "hooks", "paths", "shell", "metadata", "license", "compatibility",
}
COMMAND_FIELDS = SKILL_FIELDS - {"name", "paths"}
AGENT_HONORED = {
    "name", "description", "model", "effort", "maxTurns", "tools", "disallowedTools", "skills",
    "memory", "background", "omitClaudeMd", "isolation", "color", "experimental",
}
AGENT_IGNORED = {"permissionMode", "hooks", "mcpServers", "initialPrompt"}
AGENT_COLORS = {"red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"}
# Keys accepted by old Claude Code releases too (2.1.39 rejects, for example, displayName).
COMPAT_PLUGIN_KEYS = {"name", "version", "description", "author", "homepage", "repository", "license", "keywords"}
RESERVED_MARKETPLACE = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills", "life-sciences", "knowledge-work-plugins",
    "claude-for-legal", "claude-for-financial-services", "financial-services-plugins", "first-party-plugins",
    "claude-tag-plugins", "claude-community", "claude-plugins-community", "healthcare",
    "anthropic-plugin-directory", "claude-plugin-directory", "inline", "builtin", "skills-dir", "synced",
    "claude-plugin-test", "npm", "pip", "uv", "cargo", "github", "gh",
}
PROMPT_KEYS = {
    "schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
    "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env",
}
GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists", "llm", "baseline"}
GRADER_KEYS = {
    "type", "weight", "arm", "pattern", "flags", "match", "target", "tool", "input_match", "min", "max",
    "before", "after", "path", "exists", "criteria", "focus", "baseline_file",
}

README_SECTIONS = ["what it is", "who it is for", "quickstart", "inside", "loop", "limitations", "provenance"]
README_MAX_WORDS = 900
SKILL_MAX_LINES = 60
TEMPLATE_SECTIONS = {
    "AGENTS.md": ["Commands", "Guardrails", "Work loop", "Release", "Handoff", "Failures become rules", "What stays human"],
    "SPRINT.md": ["Outcome", "Files", "Acceptance", "Isolation", "Stop and report if", "Irreversible actions",
                  "Done means", "Implementer report", "Reviewer verdict"],
    "GATE.md": ["Candidate", "Acceptance declaration", "Steps", "What blocks", "Evidence", "Independent evidence review",
                "Finalize", "Shared resource lease", "Repair loop", "Limits"],
    "HANDOFF.md": ["Objective and acceptance", "State", "Verified so far", "Failed approaches", "Next action",
                   "Blockers and pending approvals", "Resume checklist"],
    "FAILURE-LOG.md": ["Entry template"],
    "CLAUDE.starter.md": ["Quick start", "Module boundaries", "Verify, build, test"],
}
GATE_STATES = ["blocked", "checks-passed", "review-pending", "partial", "ready"]

sys.dont_write_bytecode = True  # importing the example gate must not litter the repo with __pycache__

SKIP_DIRS = {".git", "__pycache__", "node_modules", "results"}
TEXT_EXT = {".md", ".json", ".py", ".yml", ".yaml", ".txt"}


@dataclass
class Result:
    id: str
    ok: bool
    title: str
    detail: str = ""


class Ctx:
    def __init__(self, root: Path):
        self.root = root
        self.results: list[Result] = []

    def rule(self, rid: str, title: str, problems: list[str]) -> None:
        detail = "; ".join(problems[:8]) + (f" (+{len(problems) - 8} more)" if len(problems) > 8 else "")
        self.results.append(Result(rid, not problems, title, detail))

    def rel(self, p: Path) -> str:
        try:
            return p.relative_to(self.root).as_posix()
        except ValueError:
            return p.as_posix()


# ------------------------------------------------------------------ small parsers
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP_DIRS):
            yield p


def split_frontmatter(text: str):
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, text)


def parse_scalar(v: str):
    v = v.strip()
    if v == "":
        return ""
    if v[0] == "'":
        out, i = [], 1
        while i < len(v):
            if v[i] == "'":
                if i + 1 < len(v) and v[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                if v[i + 1:].strip():
                    raise ValueError("text after closing quote")
                return "".join(out)
            out.append(v[i])
            i += 1
        raise ValueError("unterminated single-quoted string")
    if v[0] == '"':
        return json.loads(v)
    if v[0] == "[":
        if not v.endswith("]"):
            raise ValueError("unterminated flow list")
        items, buf, quote = [], "", ""
        for ch in v[1:-1]:
            if quote:
                buf += ch
                if ch == quote:
                    quote = ""
            elif ch in "'\"":
                quote = ch
                buf += ch
            elif ch == ",":
                items.append(buf)
                buf = ""
            else:
                buf += ch
        if buf.strip():
            items.append(buf)
        return [parse_scalar(x) for x in items]
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_block(block: str):
    """Parse the YAML subset this kit uses: flat `key: value` lines. Returns (data, hazards)."""
    data: dict = {}
    hazards: list[str] = []
    for i, line in enumerate(block.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            hazards.append(f"line {i}: indented YAML is outside the subset this kit uses")
            continue
        m = re.match(r"^([A-Za-z_$][\w$-]*):(?:\s+(.*))?$", line)
        if not m:
            hazards.append(f"line {i}: not a 'key: value' line")
            continue
        key, raw = m.group(1), (m.group(2) or "").strip()
        if raw and raw[0] not in "'\"[{|>&*!%@`" and (": " in raw or raw.endswith(":") or " #" in raw):
            hazards.append(f"line {i}: unquoted value of '{key}' contains ': ' or ' #' (YAML parse hazard)")
        try:
            data[key] = parse_scalar(raw)
        except ValueError as e:
            hazards.append(f"line {i}: {e}")
    try:  # cross-check with a real YAML parser when one is installed
        import yaml  # type: ignore

        yaml.safe_load(block)
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001 - any parse error is a finding
        hazards.append(f"PyYAML: {str(e).splitlines()[0]}")
    return data, hazards


def load_md(p: Path):
    """Return (frontmatter dict or None, hazards, body, raw text)."""
    text = read(p)
    block, body = split_frontmatter(text)
    if block is None:
        return None, ["no YAML frontmatter at the top of the file"], body, text
    data, hazards = parse_block(block)
    return data, hazards, body, text


FENCE_RE = re.compile(r"^(```+|~~~+)[^\n]*\n.*?^\1[ \t]*$", re.S | re.M)
INLINE_RE = re.compile(r"`[^`\n]+`")
LINK_RE = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.M)


def strip_code(text: str) -> str:
    return INLINE_RE.sub("", FENCE_RE.sub("", text))


def headings(text: str) -> list[str]:
    return [m.group(2).strip() for m in HEADING_RE.finditer(FENCE_RE.sub("", text))]


def slugify(h: str) -> str:
    h = re.sub(r"[`*_]", "", h.lower())
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", h)).strip("-")


# ------------------------------------------------------------------ rule groups
def check_manifests(c: Ctx) -> None:
    root = c.root
    pj, mj = root / ".claude-plugin" / "plugin.json", root / ".claude-plugin" / "marketplace.json"

    def load(rid: str, title: str, p: Path):
        try:
            data = json.loads(read(p))
            ok = isinstance(data, dict)
            c.rule(rid, title, [] if ok else [f"{c.rel(p)} is not a JSON object"])
            return data if ok else None
        except (OSError, ValueError) as e:
            c.rule(rid, title, [f"{c.rel(p)}: {e}"])
            return None

    plugin = load("M01", "plugin.json parses as a JSON object", pj)
    market = load("M06", "marketplace.json parses as a JSON object", mj)
    changelog = read(root / "CHANGELOG.md") if (root / "CHANGELOG.md").exists() else ""
    if plugin is not None:
        name = str(plugin.get("name", ""))
        c.rule("M02", "plugin name is kebab-case", [] if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) else [f"name {name!r}"])
        extra = sorted(set(plugin) - COMPAT_PLUGIN_KEYS)
        c.rule("M03", "plugin.json uses only keys that older Claude Code accepts", [f"unexpected keys {extra}"] if extra else [])
        ver = str(plugin.get("version", ""))
        p = []
        if not re.fullmatch(r"\d+\.\d+\.\d+", ver):
            p.append(f"version {ver!r} is not semver")
        elif f"## [{ver}]" not in changelog:
            p.append(f"CHANGELOG.md has no '## [{ver}]' entry")
        c.rule("M04", "version is semver and has a CHANGELOG entry", p)
        p = []
        if not (isinstance(plugin.get("author"), dict) and plugin["author"].get("name")):
            p.append("author.name missing")
        if plugin.get("license") != "MIT":
            p.append("license is not MIT")
        if not str(plugin.get("description", "")).strip():
            p.append("description missing")
        c.rule("M05", "author, license (MIT) and description are present", p)
        urls = [str(plugin[k]) for k in ("homepage", "repository") if k in plugin]
        c.rule("M10", "homepage and repository are https URLs", [u for u in urls if not re.fullmatch(r"https://[\w.-]+/\S+", u)])
    if market is not None:
        mname = str(market.get("name", ""))
        p = []
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", mname) or ".." in mname:
            p.append(f"marketplace name {mname!r} has characters Claude Code cannot install from")
        if mname.lower() in RESERVED_MARKETPLACE or mname.startswith("claudeai-"):
            p.append(f"marketplace name {mname!r} is reserved")
        if not (isinstance(market.get("owner"), dict) and market["owner"].get("name")):
            p.append("owner.name missing")
        if not (isinstance(market.get("plugins"), list) and market["plugins"]):
            p.append("plugins[] missing or empty")
        c.rule("M07", "marketplace has an allowed name, an owner and plugins", p)
        p, p2 = [], []
        for i, ent in enumerate(market.get("plugins", []) if isinstance(market.get("plugins"), list) else []):
            if not isinstance(ent, dict) or not ent.get("name") or "source" not in ent:
                p.append(f"plugins[{i}] needs name and source")
                continue
            if plugin is not None and ent["name"] != plugin.get("name"):
                p.append(f"plugins[{i}].name {ent['name']!r} differs from plugin.json name")
            src = ent["source"]
            if isinstance(src, str):
                if ".." in src or not (src == "." or src.startswith("./")):
                    p.append(f"plugins[{i}].source {src!r} must be '.' or start with './' and stay inside the repo")
                elif not (root / src).joinpath(".claude-plugin", "plugin.json").exists():
                    p.append(f"plugins[{i}].source {src!r} has no .claude-plugin/plugin.json")
            if "version" in ent:
                p2.append(f"plugins[{i}] sets version (plugin.json is the single source)")
        c.rule("M08", "marketplace entry names the plugin and its source resolves", p)
        c.rule("M09", "marketplace entry carries no version", p2)


def skill_dirs(root: Path):
    return sorted(d for d in (root / "skills").glob("*") if d.is_dir()) if (root / "skills").is_dir() else []


def check_components(c: Ctx) -> None:
    root = c.root
    p_c01, p_c02, p_c03, p_c04 = [], [], [], []
    skill_names: set[str] = set()
    for d in skill_dirs(root):
        f = d / "SKILL.md"
        if not f.exists():
            p_c01.append(f"{c.rel(d)} has no SKILL.md")
            continue
        fm, hazards, body, raw = load_md(f)
        skill_names.add(d.name)
        if fm is None or hazards:
            p_c01.extend(f"{c.rel(f)}: {h}" for h in hazards)
            continue
        if fm.get("name") != d.name:
            p_c01.append(f"{c.rel(f)}: name {fm.get('name')!r} must equal the directory name {d.name!r}")
        unknown = sorted(set(fm) - SKILL_FIELDS)
        if unknown:
            p_c02.append(f"{c.rel(f)}: unrecognized fields {unknown} (silently ignored at runtime)")
        desc = str(fm.get("description", ""))
        if not re.search(r"\bUse (when|after|before)\b", desc):
            p_c03.append(f"{c.rel(f)}: description has no 'Use when/after/before' trigger")
        if len(desc) + len(str(fm.get("when_to_use", ""))) > 1536:
            p_c03.append(f"{c.rel(f)}: description plus when_to_use exceeds 1,536 characters")
        if len(raw.splitlines()) > SKILL_MAX_LINES:
            p_c04.append(f"{c.rel(f)}: {len(raw.splitlines())} lines (limit {SKILL_MAX_LINES})")
    if not skill_names:
        p_c01.append("no skills found")
    c.rule("C01", "every skill has parseable frontmatter and a name equal to its directory", p_c01)
    c.rule("C02", "skill frontmatter uses documented fields only", p_c02)
    c.rule("C03", "every skill description states when to use it and fits the listing budget", p_c03)
    c.rule("C04", f"skills stay under {SKILL_MAX_LINES} lines", p_c04)

    p5, p6 = [], []
    cmd_dir = root / "commands"
    for f in sorted(cmd_dir.glob("*.md")) if cmd_dir.is_dir() else []:
        fm, hazards, _, _ = load_md(f)
        if fm is None or hazards:
            p5.extend(f"{c.rel(f)}: {h}" for h in hazards)
            continue
        if not fm.get("description"):
            p5.append(f"{c.rel(f)}: description missing")
        unknown = sorted(set(fm) - COMMAND_FIELDS)
        if unknown:
            p5.append(f"{c.rel(f)}: unrecognized fields {unknown}")
        if fm.get("disable-model-invocation") is not True:
            p5.append(f"{c.rel(f)}: must set disable-model-invocation: true (user-invoked entry point)")
        if f.stem in skill_names:
            p6.append(f"command {f.stem!r} collides with the skill of the same name")
    c.rule("C05", "commands have a description, documented fields, and are user-invoked only", p5)
    c.rule("C06", "no command shares a name with a skill", p6)

    p7, p8, p9 = [], [], []
    agent_dir = root / "agents"
    for f in sorted(agent_dir.glob("*.md")) if agent_dir.is_dir() else []:
        fm, hazards, _, _ = load_md(f)
        if fm is None or hazards:
            p7.extend(f"{c.rel(f)}: {h}" for h in hazards)
            continue
        for k in ("name", "description"):
            if not fm.get(k):
                p7.append(f"{c.rel(f)}: {k} missing")
        ignored = sorted(set(fm) & AGENT_IGNORED)
        if ignored:
            p7.append(f"{c.rel(f)}: {ignored} are ignored for plugin agents")
        unknown = sorted(set(fm) - AGENT_HONORED - AGENT_IGNORED)
        if unknown:
            p7.append(f"{c.rel(f)}: unrecognized fields {unknown}")

        def tools(key):
            v = fm.get(key, "")
            return {t.strip() for t in (v if isinstance(v, list) else str(v).split(",")) if str(t).strip()}

        allowed, denied = tools("tools"), tools("disallowedTools")
        writers = {"Write", "Edit", "NotebookEdit"}
        if not allowed:
            p8.append(f"{c.rel(f)}: declare an explicit tools list (an omitted list inherits every tool)")
        if allowed & writers or not writers <= denied:
            p8.append(f"{c.rel(f)}: must not grant {sorted(writers)} and must list them in disallowedTools")
        if fm.get("color") in {"red", "green"}:
            p9.append(f"{c.rel(f)}: color {fm['color']!r} is not colorblind-safe")
        elif "color" in fm and fm["color"] not in AGENT_COLORS:
            p9.append(f"{c.rel(f)}: color {fm['color']!r} is not a documented color")
    c.rule("C07", "agents have name and description and use only honored fields", p7)
    c.rule("C08", "agents are read-only by tool grant (no Write, Edit, NotebookEdit)", p8)
    c.rule("C09", "agent colors are documented and colorblind-safe", p9)

    shipped = [n for n in ("hooks", ".mcp.json", ".lsp.json", "bin", "monitors", "settings.json", "output-styles", "workflows")
               if (root / n).exists()]
    c.rule("C10", "the kit ships prompt content only (no hooks, MCP or LSP servers, executables, settings)", [f"found {shipped}"] if shipped else [])
    c.rule("C11", "no CLAUDE.md at the plugin root (it is not loaded and the official validator warns)",
           ["CLAUDE.md at the repo root"] if (root / "CLAUDE.md").exists() else [])


def md_files(root: Path):
    return [p for p in iter_files(root) if p.suffix == ".md"]


def check_links(c: Ctx) -> None:
    root = c.root
    p1, p2, p3 = [], [], []
    for f in md_files(root):
        text = read(f)
        for m in LINK_RE.finditer(strip_code(text)):
            target = m.group(1)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
                continue
            path_part, _, frag = target.partition("#")
            dest = f if not path_part else (f.parent / path_part).resolve()
            if not dest.exists():
                p1.append(f"{c.rel(f)}: broken link {target}")
            elif frag and dest.suffix == ".md" and slugify(frag) not in {slugify(h) for h in headings(read(dest))}:
                p1.append(f"{c.rel(f)}: no heading for anchor {target}")
        for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]*\w)", text):
            if not (root / m.group(1)).exists():
                p2.append(f"{c.rel(f)}: ${{CLAUDE_PLUGIN_ROOT}}/{m.group(1)} does not exist")
        for m in INLINE_RE.finditer(FENCE_RE.sub("", text)):
            span = m.group(0).strip("`")
            if re.fullmatch(r"(?:templates|examples|skills|agents|commands|evals|scripts)/[\w./-]*\w", span) and not (root / span).exists():
                p3.append(f"{c.rel(f)}: `{span}` does not exist")
    c.rule("L01", "relative markdown links and anchors resolve", p1)
    c.rule("L02", "${CLAUDE_PLUGIN_ROOT} paths resolve", p2)
    c.rule("L03", "backticked repo paths resolve", p3)


def check_docs(c: Ctx) -> None:
    root = c.root
    readme = root / "README.md"
    text = read(readme) if readme.exists() else ""
    hs = " | ".join(h.lower() for h in headings(text))
    c.rule("D01", "README has the required sections", [f"missing section matching {s!r}" for s in README_SECTIONS if s not in hs] if text else ["README.md missing"])
    words = len(re.findall(r"\S+", text))
    c.rule("D02", f"README is at most {README_MAX_WORDS} words", [f"{words} words"] if words > README_MAX_WORDS else [])
    mer = re.findall(r"^```mermaid\n(.*?)^```", text, re.S | re.M)
    p = [] if mer else ["no mermaid diagram"]
    for block in mer:
        # Only style declarations are colors. Label text such as "red-green proof" is a testing term.
        for line in block.splitlines():
            if not (re.match(r"\s*(style|classDef|linkStyle)\b", line) or re.search(r"\b(fill|stroke|color)\s*:", line)):
                continue
            if re.search(r"\b(red|green|lime|crimson|maroon)\b", line, re.I):
                p.append("mermaid diagram names a red or green color")
            for h in re.findall(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", line):
                h = h if len(h) == 6 else "".join(ch * 2 for ch in h)
                r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
                if (r > g + 50 and r > b + 50) or (g > r + 50 and g > b + 50):
                    p.append(f"mermaid color #{h} is red-ish or green-ish")
    c.rule("D03", "README has a mermaid diagram that avoids red and green", p)
    norm = text.replace(chr(0x2019), "'")
    c.rule("D04", "README carries the provenance statement", [] if "AI agents (Claude Code) wrote this kit's files under my direction" in norm else ["provenance sentence missing"])

    p = []
    for name, secs in TEMPLATE_SECTIONS.items():
        f = root / "templates" / name
        if not f.exists():
            p.append(f"templates/{name} missing")
            continue
        t = read(f)
        hs = " | ".join(h.lower() for h in headings(t))
        p.extend(f"templates/{name}: missing section {s!r}" for s in secs if s.lower() not in hs)
        if name in ("AGENTS.md", "CLAUDE.starter.md") and "<FILL" not in t:
            p.append(f"templates/{name}: no <FILL> placeholders")
    ag = root / "templates" / "AGENTS.md"
    if ag.exists() and len(re.findall(r"^\d+\. \*\*", read(ag), re.M)) < 12:
        p.append("templates/AGENTS.md: expected 12 numbered guardrails")
    cl = root / "templates" / "CLAUDE.starter.md"
    if cl.exists() and not read(cl).startswith("@AGENTS.md"):
        p.append("templates/CLAUDE.starter.md: first line must be the @AGENTS.md import")
    gt = root / "templates" / "GATE.md"
    if gt.exists():
        p.extend(f"templates/GATE.md: state `{s}` missing" for s in GATE_STATES if f"`{s}`" not in read(gt))
    c.rule("D05", "templates exist with their required sections and placeholders", p)

    def tier_rows(path: Path):
        return {m.group(1): [x.strip() for x in m.group(0).strip("|\n").split("|")[:4]]
                for m in re.finditer(r"^\| ([0-4]) \|.*$", read(path), re.M)} if path.exists() else {}

    a, b = tier_rows(root / "skills" / "risk-tiers" / "SKILL.md"), tier_rows(root / "templates" / "AGENTS.md")
    p = [] if len(a) == 5 and a == b else [f"risk-tiers skill rows {sorted(a)} differ from templates/AGENTS.md rows {sorted(b)}"]
    c.rule("D06", "the tier table in the risk-tiers skill matches templates/AGENTS.md", p)
    lic = read(root / "LICENSE") if (root / "LICENSE").exists() else ""
    c.rule("D07", "LICENSE is MIT, copyright Matthew Potts", [] if lic.startswith("MIT License") and "Copyright (c)" in lic and "Matthew Potts" in lic else ["LICENSE is not MIT / Matthew Potts"])
    c.rule("D08", "CHANGELOG.md exists and follows Keep a Changelog headings", [] if (root / "CHANGELOG.md").exists() and re.search(r"^## \[\d+\.\d+\.\d+\]", read(root / "CHANGELOG.md"), re.M) else ["CHANGELOG.md missing or has no version heading"])
    ver = root / "VERIFICATION.md"
    vt = read(ver).lower() if ver.exists() else ""
    c.rule("D09", "VERIFICATION.md records what was checked and what was not", [] if all(s in vt for s in ("claude plugin validate", "not checked")) else ["VERIFICATION.md missing or lacks the validate record / 'not checked' section"])


# Ranges are numeric so this source stays pure ASCII (and does not flag itself).
EMOJI_RANGES = [(0x1F000, 0x1FAFF), (0x2600, 0x27BF), (0x2B00, 0x2BFF), (0xFE0F, 0xFE0F)]


def has_emoji(text: str) -> bool:
    return any(lo <= ord(ch) <= hi for ch in text for lo, hi in EMOJI_RANGES)
SECRET_RES = [re.compile(x) for x in (r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"ghp_[A-Za-z0-9]{36}", r"sk-[A-Za-z0-9]{20,}", r"xox[baprs]-[A-Za-z0-9-]{10,}")]
ABS_PATH_RE = re.compile(r"[A-Za-z]:[\\/]Users[\\/]|/Users/[A-Za-z]|/home/[a-z][\w-]*/")


def check_hygiene(c: Ctx) -> None:
    root = c.root
    p1, p2, p3, p4 = [], [], [], []
    deny = []
    dl = root / ".leak-denylist.local"
    if dl.exists():
        deny = [re.compile(x.strip(), re.I) for x in read(dl).splitlines() if x.strip() and not x.startswith("#")]
    for f in iter_files(root):
        if f.suffix not in TEXT_EXT or f.name == ".leak-denylist.local":
            continue
        try:
            t = read(f)
        except UnicodeDecodeError:
            p3.append(f"{c.rel(f)}: not valid UTF-8")
            continue
        if f.name == "validate.py" or f.name == "test_validate.py":
            scan = "\n".join(l for l in t.splitlines() if "re.compile" not in l and "ABS_PATH_RE" not in l and "SECRET_RES" not in l)
        else:
            scan = t
        if ABS_PATH_RE.search(scan):
            p1.append(f"{c.rel(f)}: absolute personal path")
        if any(r.search(scan) for r in SECRET_RES):
            p2.append(f"{c.rel(f)}: secret-like string")
        if has_emoji(t):
            p3.append(f"{c.rel(f)}: emoji or pictograph")
        for r in deny:
            if r.search(t):
                p4.append(f"{c.rel(f)}: matches local denylist /{r.pattern}/")
    c.rule("H01", "no absolute personal paths", p1)
    c.rule("H02", "no secret-like strings", p2)
    c.rule("H03", "no emoji or pictographs (and files are valid UTF-8)", p3)
    c.rule("H04", "no hits from the optional local denylist (.leak-denylist.local)", p4)


def check_evals(c: Ctx) -> None:
    root = c.root
    ev = root / "evals"
    cases = sorted(p.parent for p in ev.glob("*/prompt.md")) if ev.is_dir() else []
    p1, p2, p3 = [], [], []
    fire_patterns: list[str] = []
    negative = False
    tagged: dict[str, int] = {}
    for d in cases:
        fm, hazards, body, _ = load_md(d / "prompt.md")
        if fm is None:
            fm, hazards = {}, hazards
        p2.extend(f"{c.rel(d)}/prompt.md: {h}" for h in hazards if "no YAML frontmatter" not in h)
        unknown = sorted(set(fm) - PROMPT_KEYS)
        if unknown:
            p2.append(f"{c.rel(d)}/prompt.md: unknown keys {unknown} (an unknown key is an error)")
        if not body.strip():
            p2.append(f"{c.rel(d)}/prompt.md: empty prompt")
        for t in (fm.get("tags") or []):
            tagged[t] = tagged.get(t, 0) + 1
        graders = sorted((d / "graders").glob("*.md")) if (d / "graders").is_dir() else []
        if not graders:
            p1.append(f"{c.rel(d)}: no graders (a case without one fails to load)")
        for g in graders:
            gm, gh, gbody, _ = load_md(g)
            if gm is None:
                p3.append(f"{c.rel(g)}: no frontmatter")
                continue
            p3.extend(f"{c.rel(g)}: {h}" for h in gh)
            typ = gm.get("type")
            if typ not in GRADER_TYPES:
                p3.append(f"{c.rel(g)}: type {typ!r} is not one of {sorted(GRADER_TYPES)}")
                continue
            unk = sorted(set(gm) - GRADER_KEYS)
            if unk:
                p3.append(f"{c.rel(g)}: unknown keys {unk}")
            if gm.get("arm") not in (None, "with-only", "both"):
                p3.append(f"{c.rel(g)}: arm must be with-only or both")
            if typ == "llm" and not gbody.strip() and not gm.get("criteria"):
                p3.append(f"{c.rel(g)}: llm grader has no rubric")
            if typ == "regex" and not gm.get("pattern"):
                p3.append(f"{c.rel(g)}: regex grader needs a pattern")
            if typ == "tool_used" and not gm.get("tool"):
                p3.append(f"{c.rel(g)}: tool_used grader needs a tool")
            for key in ("pattern", "input_match"):
                if key in gm:
                    try:
                        re.compile(str(gm[key]), re.I if "i" in str(gm.get("flags", "")) else 0)
                    except re.error as e:
                        p3.append(f"{c.rel(g)}: {key} does not compile: {e}")
            if typ == "tool_used" and gm.get("tool") == "Skill":
                if gm.get("max") == 0:
                    negative = True
                else:
                    fire_patterns.append(str(gm.get("input_match", "")))
    c.rule("E01", "every eval case has a prompt and at least one grader", p1 if cases else ["no eval cases found under evals/"])
    c.rule("E02", "eval prompt.md frontmatter uses documented keys only", p2)
    c.rule("E03", "eval graders use documented types and options, and their regexes compile", p3)
    names = {d.name for d in skill_dirs(root)}
    fires = {n for n in names if any(re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", ip) for ip in fire_patterns)}
    p = [f"no case expects skill {n!r} to fire" for n in sorted(names - fires)]
    if not negative:
        p.append("no negative case (tool_used Skill with max: 0)")
    c.rule("E04", "every skill has a case that expects it to fire, and a negative case exists", p)
    c.rule("E05", "a planted-defect case has a matching control case (graders must be able to go both ways)",
           [] if tagged.get("planted-defect") and tagged.get("control") else ["need cases tagged planted-defect and control"])
    gi = read(root / ".gitignore") if (root / ".gitignore").exists() else ""
    c.rule("E06", "evals/results/ is gitignored", [] if re.search(r"^/?evals/results/?$", gi, re.M) else ["evals/results/ not in .gitignore"])

    ex = root / "examples" / "expired-coupon"
    p7: list[str] = []
    gate_mod = None
    if (ex / "gate.py").exists():
        spec = importlib.util.spec_from_file_location("aok_example_gate", ex / "gate.py")
        gate_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gate_mod)
    for tag, cand in (("planted-defect", "candidate-a"), ("control", "candidate-b")):
        for d in cases:
            fm, _, body, _ = load_md(d / "prompt.md")
            if not (fm and tag in (fm.get("tags") or [])):
                continue
            for fname in ("pricing.py", "test_pricing.py"):
                src = ex / cand / fname
                if not src.exists() or read(src).strip() not in body:
                    p7.append(f"{c.rel(d)}: does not embed {cand}/{fname} verbatim")
            if gate_mod is not None and gate_mod.content_hash(ex / cand) not in body:
                p7.append(f"{c.rel(d)}: does not state the current content hash of {cand}")
            if tag == "control":  # the control must carry the real diff, or claims about the change cannot be checked
                for fname in ("pricing.py", "test_pricing.py"):
                    a, b = ex / "candidate-a" / fname, ex / cand / fname
                    if not (a.exists() and b.exists()):
                        continue
                    for line in difflib.unified_diff(read(a).splitlines(), read(b).splitlines(), lineterm="", n=0):
                        if line.startswith(("+++", "---", "@@")) or not line[1:].strip():
                            continue
                        if line[1:] not in body:
                            p7.append(f"{c.rel(d)}: diff line missing from the prompt: {line[:60]}")
                            break
    c.rule("E07", "eval fixtures embed the example candidates verbatim", p7)


def run_gate(root: Path, cand: Path, extra_cwd: Path | None = None):
    ex = root / "examples" / "expired-coupon"
    return subprocess.run(
        [sys.executable, str(ex / "gate.py"), str(cand), "--acceptance", str(ex / "acceptance.json")],
        capture_output=True, text=True, timeout=180, cwd=extra_cwd or ex,
    )


def check_example(c: Ctx) -> None:
    root = c.root
    ex = root / "examples" / "expired-coupon"
    if not (ex / "gate.py").exists():
        for rid in ("X01", "X02", "X03", "X04", "X05"):
            c.rule(rid, "worked example rule", ["examples/expired-coupon is missing"])
        return
    a = run_gate(root, ex / "candidate-a")
    c.rule("X01", "the example gate blocks candidate-a (exit 1, STATE: blocked)",
           [] if a.returncode == 1 and "STATE: blocked" in a.stdout else [f"exit {a.returncode}: {a.stdout[-200:]}"])
    b = run_gate(root, ex / "candidate-b")
    ok = b.returncode == 0 and "STATE: checks-passed" in b.stdout and not re.search(r"STATE: ready\b", b.stdout)
    c.rule("X02", "the example gate ends candidate-b at checks-passed, never ready", [] if ok else [f"exit {b.returncode}: {b.stdout[-200:]}"])
    with tempfile.TemporaryDirectory() as d:  # hollow-gate proof: break the thing the gate exists to catch
        mut = Path(d) / "candidate-b-with-skip"
        shutil.copytree(ex / "candidate-b", mut, ignore=shutil.ignore_patterns("__pycache__"))
        tf = mut / "test_pricing.py"
        tf.write_text(read(tf).replace("    def test_checkout_rejects_expired_coupon", '    @unittest.skip("planted")\n    def test_checkout_rejects_expired_coupon'), encoding="utf-8", newline="\n")
        m = run_gate(root, mut)
    c.rule("X03", "hollow-gate proof: a planted skip in candidate-b makes the gate block",
           [] if m.returncode == 1 and "STATE: blocked" in m.stdout else [f"gate did not block a skipped acceptance test (exit {m.returncode})"])
    rd = read(ex / "README.md") if (ex / "README.md").exists() else ""
    hashes = {k: re.search(r"content hash\s+(\w+)", r.stdout) for k, r in (("candidate-a", a), ("candidate-b", b))}
    p = [f"README does not show the current hash of {k}" for k, m_ in hashes.items() if not m_ or m_.group(1) not in rd]
    c.rule("X04", "the example README shows the gate's current content hashes", p)
    c.rule("X05", "the example is labeled illustrative", [] if "illustrative" in " ".join(rd.splitlines()[:6]).lower() else ["no 'Illustrative' label near the top"])


def run(root: Path, run_example: bool = True) -> list[Result]:
    c = Ctx(root)
    for fn in (check_manifests, check_components, check_links, check_docs, check_hygiene, check_evals):
        fn(c)
    if run_example:
        check_example(c)
    return c.results


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    run_example = True
    it = iter(argv)
    for a in it:
        if a == "--root":
            root = Path(next(it)).resolve()
        elif a == "--no-example":
            run_example = False
        else:
            print(__doc__)
            return 2
    results = run(root, run_example)
    for r in results:
        print(f"{'PASS' if r.ok else 'FAIL'} {r.id}  {r.title}" + (f"\n       -> {r.detail}" if not r.ok else ""))
    failed = [r for r in results if not r.ok]
    print(f"\n{len(results)} rules, {len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
