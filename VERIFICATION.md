# Verification record

This is a record of what was run, on what, and what came out. All runs were on 2026-09-30 on one Windows 11 machine (Git Bash, Python 3.12, Node 24, git 2.45).

I used two Claude Code builds. Version 2.1.39 is the CLI installed on this machine. Version 2.1.275 ships inside the desktop app and is the only one here with `claude plugin eval`. Failed first attempts are kept in the record.

## 1. The format, from the docs

I read these pages of code.claude.com/docs before writing anything: plugins, marketplaces, skills, subagents, `plugin validate`, `plugin eval` and memory.

**Plugin:** A plugin is a directory. The manifest is `.claude-plugin/plugin.json` and only `name` is required. Components sit at the plugin root, outside `.claude-plugin/`. They are `skills/<name>/SKILL.md`, `agents/*.md`, `commands/*.md` and `hooks/hooks.json`. Components are namespaced `/plugin:name`.

**Commands:** Commands are the older format ("skills supersede them for new work"). A skill and a command with the same name collide, and the skill wins. This kit uses both, with distinct names.

**Agents:** Plugin agents honor `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, `isolation` and `color`. They ignore `permissionMode`, `hooks` and `mcpServers`.

**Isolation:** `isolation: worktree` branches from the default branch and ignores the commit under review, so the reviewer does not use it.

**Marketplace:** A marketplace is `.claude-plugin/marketplace.json` with `name`, `owner` and `plugins[]`. A repo can be both marketplace and plugin with `"source": "./"`.

**Validation:** `claude plugin validate` is the documented authority for manifests and component frontmatter. `--strict` fails on warnings. `claude plugin eval` needs Claude Code 2.1.269 or later.

## 2. `claude plugin validate`

| Command | 2.1.39 | 2.1.275 |
|---|---|---|
| `validate .` (marketplace) | passes | passes with `--strict` |
| `validate .claude-plugin/plugin.json` | passes | passes with `--strict` |
| `validate skills`, `agents`, `commands` | not supported (manifests only) | pass with `--strict` |

It also passes with an empty config directory and no login, so a CI job can run it.

Testing it showed three things.

**Manifest fixes:** 2.1.39 rejected `displayName` ("Unrecognized key") and warned without `metadata.description`. Both were fixed in the manifests.

**Planted defects:** A planted YAML error failed the validator, and a missing command description raised a warning. This shows the validator can fail.

**Gaps:** It silently accepts a misspelled skill field (`disable_model_invocation`) and the ignored `permissionMode` on a plugin agent. Those would do nothing at runtime, so `scripts/validate.py` checks them (C02, C07).

## 3. Install and load

I ran these in isolated `CLAUDE_CONFIG_DIR` directories, so the real `~/.claude` was never touched.

**Install:** `claude plugin marketplace add` then `install agent-operating-kit@agent-operating-kit` succeeded on 2.1.275. It also succeeded on 2.1.39 with the relative form `./agent-operating-kit`. 2.1.39 rejects an absolute Windows path. `plugin list` shows version 0.1.0, enabled. The plugin cache contains `templates/`, so `${CLAUDE_PLUGIN_ROOT}` paths resolve.

**Load:** `claude --plugin-dir . plugin details` lists 12 skill-type entries (6 skills and 6 commands) and 2 agents. It lists 0 hooks and 0 MCP servers. It adds about 1,174 tokens to every session. That is an estimate.

## 4. `scripts/validate.py` and its self-test

**Rules:** `scripts/validate.py` has 49 rules across manifests, components, links, README and templates, hygiene, the eval suite and the example. It passes on the tree.

**Self-test:** `scripts/test_validate.py` plants one defect per rule and requires that rule to fail. It also requires the clean tree to pass and every rule to have a planted defect. A mutation that changes nothing is an error. All 5 tests pass in about 30 s.

**Bugs found:** The validator and its self-test found three bugs in my own work. 1) The emoji rule flagged its own source, because the writing tool had decoded `\u` escapes into real characters. 2) The eval-coverage rule ignored skill names without a hyphen. 3) The color rule flagged the words "red-green" in a diagram label. All three are fixed.

## 5. `claude plugin eval`

The command, on 2.1.275, run from the plugin root:

```
claude plugin eval . --trust-plugin --no-publish --ablation none --model sonnet --judge-model sonnet -j 3
```

**Cases:** Nine cases, three runs each, one arm (no no-plugin baseline). Six check that a skill fires on natural phrasing. One is a negative control, where an ordinary rename must fire nothing. Two cover the reviewer. One is a planted false "done" (the fixture is the example's candidate A). The other is a true-claim control (candidate B, with its diff). The pair makes sure the graders can go both ways.

**Models:** The agent under test was Sonnet and the judge was Sonnet. Run 1 used the default small judge.

**Upload:** `--no-publish` was set on every run, so nothing was uploaded.

**Run 1 failed.** 2 of 9 cases scored 1.00 and the mean was 0.73. However, the skill fired in 17 of 18 trigger runs. I read the transcripts to find the causes, and there were four.

1. The skills were written as procedures to execute. Asked a general question in an empty workspace, the model went looking for a repository. It reported "nothing to gate" or "no incident to reconstruct" and skipped the answer. Two `handoff` runs spawned sub-agents and timed out. The fix was a one-line advice-mode rule in four skills.
2. `sprint-spec` was right to refuse to invent file paths, and my rubric demanded them. The case now describes the service.
3. The reviewer failed the true-claim control in 3 of 3 runs. The brief had no diff or candidate identity, so claims about the change could not be checked. The agent also treated "could not reproduce" like "contradicted". The fix was an explicit text-only mode and four defined statuses in the agent. The fixture also got a real diff and identity.
4. The small judge misgraded one correct reviewer answer, which named both planted defects. The fix was `--judge-model sonnet`.

Run 2 (full suite, candidate `d6af4b7`) scored 6 of 9 at 1.00, with a mean of 0.94. It also showed the reviewer catching a real flaw in my own work. The example and the control described the red-green as "delete the expiry check". That check already existed in the earlier candidate, and the fix is the routing. I corrected the example and the fixture (with a real revert, `FAILED (failures=1)`). I also added the red-proof and the log entry to the `failure-to-rule` advice mode. Then I re-ran only the two affected cases on candidate `d025a26`. Only those three files differ between the two candidates, so the table below is an exact record of `d025a26`.

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

**Final:** 8 of 9 cases at 1.00, with a mean of 0.98. The skill fired in 18 of 18 trigger runs and in 0 of 3 on the unrelated request. The reviewer returned `VERDICT: FAIL` on the planted defect in 3 of 3 runs. It named the dead-code fix, the skipped test and the missing boundary test. It returned `PASS WITH FOLLOW-UPS` on the true claim in 3 of 3 runs. The one imperfect case is `refute-review-fires`. In one run the model answered well but asked for specifics first and left out "skipped tests are failures".

Later commits change documentation, with one exception. The commit that rewrote the docs in plain voice also changed punctuation in the skills, agents, commands, templates and eval files. It changed no wording. I did not re-run the evals after it. `git diff d025a26 HEAD -- skills agents commands .claude-plugin evals` shows the new `evals/README.md` and those punctuation changes.

**Cost:** About $13.6 in all at list price. That is $0.62 for a smoke run, $5.54 for run 1, $5.21 for run 2 and $2.21 for the re-run.

This is a real reviewer verdict from run 2 on the planted-defect case. It is verbatim and abridged, with paths removed.

```
VERDICT: FAIL
Candidate: candidate-a (content hash 5d4e6dcc679c...c3747), no branch/revision given, dirty: unknown; risk tier reviewed against: 1

| 1 | Spec outcome: at checkout an expired coupon is rejected | A path from checkout() that raises | checkout() calls apply_promo(), whose docstring says "Never checks the expiry date"; apply_coupon() has the check but has no caller | refuted |
| 2 | c1 test_checkout_rejects_expired_coupon satisfied | Test present and executing | decorated @unittest.skip("flaky date handling, revisit"); would fail if enabled | refuted |
| 6 | "Ran python -m unittest: all tests pass" | Counts covering the acceptance tests | the report's own output says OK (skipped=1); the skipped one is the sole expiry test | refuted |

1. The fix is not wired into the entry point; the spec outcome is not delivered. Blocks merge: yes.
2. The acceptance test for c1 is disabled ... The test is not flaky: TODAY, VALID and EXPIRED are fixed constants ...
```

### What the evidence does not show

**Fitted suite:** I changed skills, fixtures and rubrics after seeing failures, so the final scores are partly fitted to this suite. A held-out set of prompts would be a fairer test.

**Sample size:** The suite has three runs per case, one agent model, LLM judges and text fixtures. Three runs cannot estimate a rate. The residual `refute-review-fires` miss is within that noise.

**No baseline:** There is no no-plugin comparison, so the results say nothing about whether the kit beats plain Claude.

**Windows isolation:** On Windows the eval warned that it "could NOT seal what the plugin under test wrote (directory modes do not restrict access on Windows)". This plugin ships no code that writes. The isolation is still weaker than on Linux.

## 6. Other checks

**Mermaid:** The README's diagram parses with the real Mermaid 12.0.0 parser. A deliberately broken diagram is rejected, so the check can fail.

**Red-green recipe:** The reviewer's recipe works on this machine and leaves the repository untouched. It runs `git archive <rev> | tar -x -C <tmpdir>`, reverts the fix and runs the tests.

**Example gate:** `candidate-a` exits 1 (`STATE: blocked`). `candidate-b` exits 0 (`STATE: checks-passed`, never ready). A skip planted in `candidate-b` makes it block.

**Leak scan:** A scan against a private list of the source project's internal terms found nothing. The list lives outside this repository.

**Characters:** Every file is ASCII with no emoji and no red/green color coding.

## 7. Not checked

- Use by anyone other than me, on any project other than mine.
- Installing from a GitHub source (`owner/repo`). Only the local-directory marketplace source was tested, because no remote existed yet.
- macOS and Linux. The GitHub Actions workflow had not run, because there was no remote yet. Its `npm install -g @anthropic-ai/claude-code` step was untested on a runner (the same commands were run locally).
- Whether the kit improves outcomes over working without it. The eval has no no-plugin comparison and tests text fixtures on one model.
- The slash commands were validated but never executed in a live session.
- Codex, Cursor and other tools reading the templates.
- Whether reading `${CLAUDE_PLUGIN_ROOT}` template files prompts for permission in a default-mode session.
- Whether the punctuation cleanup changed any eval result. The evals were not re-run after it.
