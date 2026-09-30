---
name: handoff
description: Make work resumable across sessions, agents and vendors - write a checkpoint before stopping and resume from one cold. Use when a usage or context limit is near, when switching to another agent or tool, when stopping mid-task, when picking up unfinished work, or when running parallel agent lanes.
---

# Handoff and resume

Goal: any agent, from any vendor, can resume from repository state alone. Sessions end mid-task through limits, restarts and tool switches, so persist as you go.

Template: `${CLAUDE_PLUGIN_ROOT}/templates/HANDOFF.md`. Commands: `/agent-operating-kit:checkpoint` and `/agent-operating-kit:resume`.

Asked what to write down (a general question)? Answer from the list below and inspect nothing. Read the repository only when you are actually writing or resuming a checkpoint.

## Before you stop: persist
- Objective, acceptance criteria, exact checkout path, branch and revision
- Commits done; uncommitted files and who owns them
- Commands run and their verified results, with evidence paths, hashes and platform limits
- Failed approaches and their diagnosed causes; label hypotheses as hypotheses
- The next concrete action, blockers, pending approvals, shared-resource ownership
- Obligations that outlive local completion (observing a release, recovery): who carries them and what triggers them
- If a usage limit caused the stop, when it resets

Take facts from git and files, not memory. Keep the checkpoint out of version control, and copy the previous one to a dated sibling before overwriting.

## Resume, in order
1. Read the checkpoint, copy it aside, then write your own identity into the live file.
2. Confirm the other session really stopped: processes, containers, lock files, run directories, its last transcript record. A stale timestamp is not proof. When unsure, treat the lease as live.
3. Reconstruct from the most durable source first: worktrees, the checkpoint's next action, the work record and evidence, the newest run directories. Transcripts last.
4. Do not rerun a finished expensive gate on an unchanged frozen candidate.
5. Keep one integration coordinator at a time. Approval boundaries do not change with the coordinator.
6. Before handing back, persist state and either release shared resources or lease them explicitly, with owner and ports recorded.

## Parallel lanes
- One worktree per lane, with its own data target and port range. A device or emulator belongs to one lane at a time.
- Write only in your worktree and lane file. Stage with explicit pathspecs. No bare stash. Never rebase a shared branch. Every git command names its worktree.
- One writer per file. Shared files belong to the coordinator.
- A lane reports branch, head, files changed, commands and results, reviewer and verdict, criteria moved, limitations. The coordinator merges with a merge commit, re-runs focused checks and announces the new head.
- Freeze: after the coordinator names a revision, only gate repairs it routes may land. A different lane reviews security-sensitive work.
- Steer a running subagent only through its spawn prompt, stating the working directory and first action. Messaging it can create a duplicate acting in the same worktree.

## Fresh-agent exercise
After a material change to workflow or docs layout, start an agent with only the checkout path and ask about a dozen questions, requiring citations: what is being built, what agents may do without approval, what was last verified and whether that proves HEAD, how to recover a failed run, what remains unproven. Score each answer on conclusion, citation and limitation. A pass shows retrieval works; it does not show long-term autonomous maintenance.
