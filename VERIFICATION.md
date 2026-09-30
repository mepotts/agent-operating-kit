# Verification record

What was run, on what, and what came out. All runs were on 2026-09-30 on one Windows 11 machine (Git Bash, Python 3.12, Node 24, git 2.45). Two Claude Code builds were used: 2.1.39, which is the CLI installed on this machine, and 2.1.275, which ships inside the desktop app and is the only one here that has `claude plugin eval`. Failed first attempts are kept, not hidden.

## 1. The format, from the docs

Read from code.claude.com/docs (plugins, marketplaces, skills, subagents, `plugin validate`, `plugin eval`, memory) before writing anything:

- A plugin is a directory. The manifest is `.claude-plugin/plugin.json`; only `name` is required. Components sit at the plugin root, not inside `.claude-plugin/`: `skills/<name>/SKILL.md`, `agents/*.md`, `commands/*.md`, `hooks/hooks.json`. Components are namespaced `/plugin:name`.
- Commands are the older format ("skills supersede them for new work"); a skill and a command with the same name collide, and the skill wins. This kit uses both, with distinct names.
- Plugin agents honor `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation`, `color` and ignore `permissionMode`, `hooks`, `mcpServers`.
- `isolation: worktree` branches from the default branch, not the commit under review, so the reviewer does not use it.
- A marketplace is `.claude-plugin/marketplace.json` with `name`, `owner`, `plugins[]`. A repo can be both marketplace and plugin with `"source": "./"`.
- `claude plugin validate` is the documented authority for manifests and component frontmatter (`--strict` fails on warnings). `claude plugin eval` needs Claude Code 2.1.269 or later.

## 2. `claude plugin validate`

| Command | 2.1.39 | 2.1.275 |
|---|---|---|
| `validate .` (marketplace) | passes | passes with `--strict` |
| `validate .claude-plugin/plugin.json` | passes | passes with `--strict` |
| `validate skills`, `agents`, `commands` | not supported (manifests only) | pass with `--strict` |

It also passes with an empty config directory and no login, so a CI job can run it.

What testing it taught:
- 2.1.39 rejected `displayName` ("Unrecognized key") and warned without `metadata.description`. Both were fixed in the manifests.
- The validator is not hollow: a planted YAML error failed it, and a missing command description raised a warning.
- It silently accepts a misspelled skill field (`disable_model_invocation`) and the ignored `permissionMode` on a plugin agent. Those would do nothing at runtime, so `scripts/validate.py` checks them (C02, C07).

## 3. Install and load

In isolated `CLAUDE_CONFIG_DIR` directories, so the real `~/.claude` was never touched:

- `claude plugin marketplace add` then `install agent-operating-kit@agent-operating-kit` succeeded on 2.1.275, and on 2.1.39 with the relative form `./agent-operating-kit`. 2.1.39 rejects an absolute Windows path. `plugin list` shows version 0.1.0, enabled. The plugin cache contains `templates/`, so `${CLAUDE_PLUGIN_ROOT}` paths resolve.
- `claude --plugin-dir . plugin details`: 12 skill-type entries (6 skills and 6 commands), 2 agents, 0 hooks, 0 MCP servers, and about 1,174 tokens added to every session (an estimate).

## 4. `scripts/validate.py` and its self-test

- 49 rules across manifests, components, links, README and templates, hygiene, the eval suite and the example. It passes on the tree.
- `scripts/test_validate.py` plants one defect per rule and requires that rule to fail, requires the clean tree to pass, and requires every rule to have a planted defect. A mutation that changes nothing is an error. All 5 tests pass (about 30 s).
- Bugs the validator and its self-test found in my own work: the emoji rule flagged its own source (the writing tool had decoded `\u` escapes into real characters); the eval-coverage rule ignored skill names without a hyphen; the colour rule flagged the words "red-green" in a diagram label. All fixed.

## 5. `claude plugin eval`

Command, on 2.1.275, run from the plugin root:

```
claude plugin eval . --trust-plugin --no-publish --ablation none --model sonnet --judge-model sonnet -j 3
```

Nine cases, three runs each, one arm (no no-plugin baseline). The agent under test was Sonnet and the judge Sonnet, except run 1, which used the default small judge. `--no-publish` was set on every run, so nothing was uploaded. The cases: six where a skill should fire on natural phrasing, one negative control (an ordinary rename must fire nothing), and a pair for the reviewer: a planted false "done" (the fixture is the example's candidate A) and a true-claim control (candidate B, with its diff). The pair exists so the graders must be able to go both ways.

**Run 1 failed.** 2 of 9 cases scored 1.00 (mean 0.73; the skill fired in 17 of 18 trigger runs). I read the transcripts instead of tuning to the score. Four causes:

1. The skills were written as procedures to execute. Asked a general question in an empty workspace, the model went looking for a repository, reported "nothing to gate" or "no incident to reconstruct", and skipped the answer; two `handoff` runs spawned sub-agents and timed out. Fix: a one-line advice-mode rule in four skills.
2. `sprint-spec` was right to refuse to invent file paths, and my rubric demanded them. Fix: the case now describes the service.
3. The reviewer failed the true-claim control in 3 of 3 runs. The brief had no diff or candidate identity, so claims about the change could not be checked, and the agent treated "could not reproduce" like "contradicted". Fix: an explicit text-only mode and four defined statuses in the agent, plus a real diff and identity in the fixture.
4. The small judge misgraded one correct reviewer answer (it named both planted defects). Fix: `--judge-model sonnet`.

Run 2 (full suite, candidate `d6af4b7`) then scored 6 of 9 at 1.00 (mean 0.94). It also showed the reviewer catching a real flaw in my own work: the example and the control described the red-green as "delete the expiry check", but that check already existed in the earlier candidate; the fix is the routing. I corrected the example and the fixture (with a real revert, `FAILED (failures=1)`), added the red-proof and the log entry to the `failure-to-rule` advice mode, and re-ran only the two affected cases on candidate `d025a26`. Only those three files differ between the two candidates, so the table below is an exact record of `d025a26`.

| Case | Run 1 | Final |
|---|---|---|
| `sprint-spec-fires` | 0.50 | 1.00 |
| `risk-tiers-fires` | 1.00 | 1.00 |
| `refute-review-fires` | 0.83 | 0.83 |
| `release-gate-fires` | 0.67 | 1.00 |
| `handoff-fires` | 0.56 | 1.00 |
| `failure-to-rule-fires` | 0.83 | 1.00 |
| `unrelated-request-quiet` | 1.00 | 1.00 |
| `reviewer-refutes-false-done` | 0.89 | 1.00 |
| `reviewer-accepts-true-claim` | 0.25 | 1.00 |

Final: 8 of 9 at 1.00 (mean 0.98). The skill fired in 18 of 18 trigger runs and in 0 of 3 on the unrelated request. The reviewer returned `VERDICT: FAIL` on the planted defect in 3 of 3 runs, naming the dead-code fix, the skipped test and the missing boundary test, and `PASS WITH FOLLOW-UPS` on the true claim in 3 of 3. The one imperfect case: in one `refute-review-fires` run the model answered well but asked for specifics first and omitted "skipped tests are failures".

Later commits change documentation only: `git diff d025a26 HEAD -- skills agents commands .claude-plugin evals` shows just the new `evals/README.md`.

Cost, at list price: about $13.6 in all (a $0.62 smoke run, $5.54 for run 1, $5.21 for run 2, $2.21 for the re-run).

A real reviewer verdict from run 2 (planted-defect case; verbatim, abridged, paths removed):

```
VERDICT: FAIL
Candidate: candidate-a (content hash 5d4e6dcc679c...c3747), no branch/revision given, dirty: unknown; risk tier reviewed against: 1

| 1 | Spec outcome: at checkout an expired coupon is rejected | A path from checkout() that raises | checkout() calls apply_promo(), whose docstring says "Never checks the expiry date"; apply_coupon() has the check but has no caller | refuted |
| 2 | c1 test_checkout_rejects_expired_coupon satisfied | Test present and executing | decorated @unittest.skip("flaky date handling, revisit"); would fail if enabled | refuted |
| 6 | "Ran python -m unittest: all tests pass" | Counts covering the acceptance tests | the report's own output says OK (skipped=1); the skipped one is the sole expiry test | refuted |

1. The fix is not wired into the entry point; the spec outcome is not delivered. Blocks merge: yes.
2. The acceptance test for c1 is disabled ... The test is not flaky: TODAY, VALID and EXPIRED are fixed constants ...
```

What this evidence does not show:
- I changed skills, fixtures and rubrics after seeing failures, so the final scores are partly fitted to this suite. A held-out set of prompts would be a fairer test.
- Three runs per case, one agent model, LLM judges, and text fixtures. Three runs cannot estimate a rate; the residual `refute-review-fires` miss is within that noise.
- There is no no-plugin comparison, so it says nothing about whether the kit beats plain Claude.
- On Windows the eval warned that it "could NOT seal what the plugin under test wrote (directory modes do not restrict access on Windows)". This plugin ships no code that writes, but the isolation is weaker than on Linux.

## 6. Other checks

- The README's Mermaid diagram parses with the real Mermaid 12.0.0 parser, and a deliberately broken diagram is rejected, so the check is not vacuous.
- The reviewer's red-green recipe (`git archive <rev> | tar -x -C <tmpdir>`, revert the fix, run the tests) works on this machine and leaves the repository untouched.
- The example gate: `candidate-a` exits 1 (`STATE: blocked`); `candidate-b` exits 0 (`STATE: checks-passed`, never ready). A skip planted in `candidate-b` makes it block.
- A leak scan against a private list of the source project's internal terms found nothing. The list lives outside this repository.
- Everything is ASCII, contains no emoji, and uses no red/green colour coding.

## 7. Not checked

- Use by anyone other than the author, on any project other than the author's.
- Installing from a GitHub source (`owner/repo`). Only the local-directory marketplace source was tested, because no remote exists yet.
- macOS and Linux. The GitHub Actions workflow has never run: there is no remote yet, and its `npm install -g @anthropic-ai/claude-code` step is untested on a runner (the same commands were run locally).
- Whether the kit improves outcomes over working without it. The eval has no no-plugin comparison and tests text fixtures on one model.
- The slash commands were validated but never executed in a live session.
- Codex, Cursor and other tools reading the templates.
- Whether reading `${CLAUDE_PLUGIN_ROOT}` template files prompts for permission in a default-mode session.
