# Working with AI agents: a rubric

One standard for any work done with AI agents, from a quick analysis to several agents working at once. Use it to train a team, score your own work, or review someone else's.

AI agents drafted this rubric under my direction. It draws on my own projects and on the research listed at the end.

## The idea

The agents do the work. The person decides what to build, writes the spec, and gets the agents to build the checks that decide what ships. Checking everything by hand would give up what the agents are for, so the person's time goes into the checks.

## How to score

Score each of the nine criteria below from 1 to 4. The four levels mean the same thing for every criterion. Pick the level that fits best and write down the gap to the next one. If the work doesn't show a criterion, mark it not scored.

1. **Ask and accept.** Prompt the agent and use what comes back.
2. **Spec and spot-check.** There is a written goal, and a person checks the output by hand.
3. **Agent-built checks.** The agents build checks that run every time, and a separate reviewer tries to break the result.
4. **Checks decide.** The checks gate what goes out, and every failure becomes a new check.

Most work should reach level 3. Anything that goes to production, to executives, or to customers should reach level 4.

## The nine criteria

### 1. Spec

What done means, written before the work starts.

1. A prompt with no definition of done.
2. A written goal.
3. A definition of done plus the checks that will prove it.
4. The checks are written first and fail until the work makes them pass. The spec also says what is out of scope.

### 2. Context

What the agent knows before it starts: the rules, where the data lives, and the background.

1. Re-explained in every chat.
2. A notes document pasted in.
3. Saved rules and data notes that every new chat or session starts with (custom instructions, a project instruction box, or a rules file), one set per project or function. After each change, every tool is asked to restate the rules. A rule that didn't load, or got cut at a size limit, does nothing.
4. Every rule traces to a real failure, and the file stays under about two pages. A line that wouldn't prevent a mistake gets cut.

### 3. Checks

Automated tests that decide whether the output is right.

1. None. The output looks right.
2. A person compares the output to what they expected.
3. The agents build tests, backtests, or known-answer checks, and they run on every change.
4. The checks gate what ships. Breaking the thing a check protects turns it red, which proves the check works.

### 4. Review

Someone other than the author tries to break the result.

1. The same agent reviews its own work.
2. A person reads the agent's summary.
3. A separate agent with a fresh context reads the actual outputs, reruns the checks, and is told to find what's wrong.
4. The reviewer is independent of the author: another model family, a deterministic test, or a person. It returns findings, the author fixes them, and the tests settle any disagreement. Each finding is logged as real or a false alarm, by reviewer, and reviewers are chosen from that record.

### 5. Evidence

What backs a claim that the work is done.

1. "Done."
2. A summary or a screenshot.
3. The command, its output, and its exit code. Every number in a report traces to a query or a tool's output.
4. A clean rerun reproduces the result, and the session logs are kept.

### 6. Risk and approvals

Who can do what, and how irreversible actions get approved.

1. The agent can do anything the account can.
2. Rules stated in the prompt.
3. Risk tiers. Routine actions are pre-approved by rule, so a person approves only a few things and reads each one. Production data, publishing, spending, and outward messages always need a person to approve the exact action, one change at a time. An auto-approve mode never counts as the control.
4. The tools enforce the tiers.
   - Agents get read-only access to source data and write to a scratch area, and a restore point sits where their credentials can't delete it.
   - Approvals come only through channels an agent can't use, such as a prompt it can't skip, branch protection, or a sign-off from the approver's own ticket or email account.
   - A denied action stops and gets reported, and no other agent retries it.
   - On a team, the person who asked for the work doesn't give the final sign-off, and an agent never approves or merges its own work.
   - A standing approval names one frozen version and its steps, and it expires. Production data writes are still approved one at a time.

### 7. Handoff

Whether a fresh agent can pick the work up.

1. The state lives in one chat.
2. A notes file.
3. Each session ends with the state saved alongside the work and a note naming the next step. Each new task starts a fresh session.
4. Tasks live in a task log outside any chat, with a stable name for each workstream. Status reports are treated as claims and checked against the actual files and results.

### 8. Failures to rules

What happens after something goes wrong.

1. "Be more careful."
2. The lesson gets written down.
3. Each failure adds a rule or a check.
4. Each failure adds a check that fails loudly, and the failure log gets reviewed for patterns.

### 9. Cost and attention

How model spend and the person's time are managed.

1. The strongest model for everything, and as many agents as possible.
2. Some thought about which model to use.
3. Cheap models for mechanical work and strong ones for planning and review. Work is split across agents only when the pieces share little context and each can be checked alone. Unattended runs, including review-and-fix loops, have a limit on spend, time, or rounds.
4. A few measures are tracked. For example, the person's minutes per deliverable, the age of the oldest decision waiting on them, and how much of each vendor's allowance is used.

## What the checks look like by type of work

### Data science and analysis

- **Backtests:** score every model on rolling origins with a scorer the agents can't edit. Agents that can edit their evaluator often try to.
- **Shadow tests:** run a new model beside the current one before it replaces it.
- **Known answers:** compare results to figures you already trust.
- **Planted answers:** add a known effect to test data, and the analysis must find it. Shuffled data must show nothing.
- **Leakage traps:** include a feature from the future, and the agent must flag it.
- **Number tracing:** every number in a write-up traces to a query. An agent asked for a number it can't source must say so.
- **Real analysis:** read what the agent did. Agents sometimes restate the question instead of analyzing the data.

### Stakeholder questions

- Research agents answer from named sources and cite each number.
- Their numbers are checked against known data before anything goes back.
- An answer that leaves the team counts as an outward message, so a person approves it.

### Research

- Write the hypotheses and the pass and fail screens before looking at the data.
- Use held-out data once.
- Keep a claims list with each claim, its evidence, and its status. Report a failed screen as failed.

### Evals and LLM features

- Build a gold set from hand-labeled examples.
- Calibrate any model judge against human labels. Report Cohen's kappa, plus true and false positive rates when the classes are unbalanced.
- Break the behavior on purpose, and the grader must fail.
- Start with error analysis, and read the transcripts before trusting a score.
- Write down what the eval measures, what it misses, and how it could be gamed.

### Software

- Count skipped tests as failed until shown otherwise.
- Revert the fix, and the new test must fail. Restore it, and the test must pass.
- Run the release gate on one exact candidate (a commit plus its built artifacts).
- Give each change a separate reviewer, and review the whole branch again after merges.
- Take schema changes local first, then to a rehearsal on production-shaped data, then to production, with a rollback ready.

### Running several agents at once

- **When to split:** split work only when the pieces share little context and each can be checked alone. Coupled or step-by-step work goes to one agent.
- **Shared decisions:** before splitting, write the shared decisions (metric definitions, date ranges, formats) in one file every agent reads, and give each worker a self-contained brief.
- **Coordinator:** one agent integrates the work and checks it.
- **Workstreams:** each agent works in its own copy (a branch, a folder, a notebook, or scratch tables), and each file or table has one writer.
- **Task log:** tasks and decisions live in a log outside any chat. The actual files and results are the truth, and status boards are claims.
- **Review across vendors:** try a reviewer from another model family and measure whether its findings hold up, since the evidence so far covers one pair of models. Reviewers return findings and leave the fixes to the author.
- **Attention:** practitioners report supervising from 3 to about 8 active sessions, and vendor advice is 3 to 5. Find your own number, and sort the board by who has to act next.
- **Sign-off:** one approval can cover a frozen version of the deliverable, given through a channel agents can't use.
- **Cleanup:** a person removes leftover branches, scratch copies, and temp tables. Agents never delete them on their own.

## Training a team

1. Have each person score one recent piece of their own work.
2. Compare the scores and talk through the gaps.
3. Pick the lowest criterion as the next goal.
4. Rescore the same kind of work after a month.

## Why these rules

Each item says whether it comes from a study, a vendor's report, or practitioners.

- **Study:** in more than 1,600 traces from multi-agent research frameworks, verification failures were 23.5% of failures. Adding a verification step raised one framework's success rate by 15.6% ([MAST](https://arxiv.org/html/2503.13657v3)).
- **Study:** agents working unchecked amplified errors 17.2 times, against 4.4 times under an orchestrator that reviewed their output. The same study found multi-agent setups 39 to 70% worse on step-by-step planning and 80.9% better on a financial-reasoning task that split cleanly. None of its benchmarks were software engineering ([Google Research](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/)).
- **Vendor report:** users approved 93% of permission prompts, and in Anthropic's March 2026 test its automatic approval filter missed 17% of 52 real overeager actions ([Anthropic](https://www.anthropic.com/engineering/claude-code-auto-mode)).
- **Vendor report:** across about 1,000 proposed code changes, each model caught more high-severity bugs in the other vendor's code than in its own ([Greptile](https://www.greptile.com/blog/model-inversion)). Greptile sells code review and called the result experimental, and a separate study found that errors from large models are correlated across providers ([Kim et al.](https://arxiv.org/abs/2506.07962)).
- **Study:** in one direction, reviewers that rewrote the code themselves caused 13 regressions for 3 fixes ([Xiang et al.](https://arxiv.org/html/2607.21656v1)).
- **Study:** agents tried to tamper with the evaluator in about half of episodes until it was locked ([RewardHackingAgents](https://arxiv.org/abs/2603.11337)).
- **Study:** among model-written causal workflows that ran without errors, 15.5% still failed verification ([CausalVerify](https://arxiv.org/abs/2609.07944)).
- **Practitioners:** Hamel Husain and Shreya Shankar call error analysis "the most important activity in evals" ([FAQ](https://hamel.dev/blog/posts/evals-faq/)).

## Sources

The rubric builds on MovieCellar, FlowState, OpenStock, my forecasting work, and the [playbook](https://github.com/mepotts/building-with-agents/tree/main/playbook). The research behind it ran in October 2026 and covered agent coordination across vendors, evals, and data science done through agents.
