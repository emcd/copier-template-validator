# Context

- Overview and Quick Start: README.{md,rst}

- Use the 'context7' MCP server to retrieve up-to-date documentation for any SDKs or APIs.
- Use the 'nb' MCP server for project note-taking, issue tracking, and collaboration. The server provides LLM-friendly access to the `nb` note-taking system with proper escaping and project-specific notebook context.
- Check README files in directories you're working with for insights about architecture and design decisions.

## Purpose

Generic Copier template validator. Validates Copier templates instantiated
with various preset answer files (variants). Provides configurable
validation commands so that any Copier template project can use it for QA.
CLI entry point: `copiertv`.

## Tech Stack

- Python 3.10+
- Hatch/Hatchling (build system)
- tyro (CLI argument parsing via dataclasses)
- frigid (immutable data structures, exception base)
- absence (sentinel values)
- dynadoc (annotation-based documentation)
- emcd-appcore (CLI framework, state management)
- Copier (template engine, invoked as subprocess)
- pytest (testing)
- ruff, pyright (linting, type checking)
- Sphinx + Furo (documentation)

# Development Standards
Before implementing code changes, consult these files in `.auxiliary/instructions/`:
- `practices.rst` - General development principles (robustness, immutability, exception chaining)
- `practices-python.rst` - Python-specific patterns (module organization, type annotations, wide parameter/narrow return)
- `nomenclature.rst` - Naming conventions for variables, functions, classes, exceptions
- `style.rst` - Code formatting standards (spacing, line length, documentation mood)
- `validation.rst` - Quality assurance requirements (linters, type checkers, tests)

# Operation

- Use a README-first discovery workflow to reduce token churn:
  - Start at the repository root `README.{md,rst}`, then read the nearest relevant subtree README.
  - After reading the nearest README, scope code searches to that subtree before considering repo-wide searches.
  - If a touched subsystem README is stale after your change, update it in the same batch.
- Use relative paths rather than absolute paths when possible (relative paths are less likely to trigger tool call permission requests).
- Do not write to paths outside the current project unless explicitly requested.
- Use `.auxiliary/scribbles` for scratch work and one-off experiments instead of `/tmp`.
- Use `.auxiliary/temporary` for ephemeral test state and build artifacts that are safe to delete.
- In sandboxed environments (e.g., Codex CLI), treat file/network permission failures as escalation boundaries:
  - If an operation fails due to sandbox, file access, or network restrictions, rerun it with user escalation.
  - Do not spend time on retry loops or workaround exploration before escalating blocked operations.
- When writing here-docs or multi-line shell strings, suppress expansions by quoting the delimiter (e.g., `'EOF'` instead of `EOF`) unless you intentionally need variable or command substitution.

## Guidance Files

| Topic | File |
|-------|------|
| `nb` MCP tools, tagging, and notebook organization | @documentation/agents/notebook.md |
| OpenSpec proposals and workflow | @documentation/agents/openspec.md |
| Delegated review flow and stacked commits | @documentation/agents/reviews.md |

### Recommended Organization

| Medium | Location | Purpose |
|--------|----------|---------|
| `nb` | `coordination/` | Handoffs, org chart, team workflow |
| `nb` | `ideas/` | Rough ideas, early-stage proposals; tag `#task-proposal` for OpenSpec drafts |
| `nb` | `issues/` | Bug tracking and known issues |
| `nb` | `reviews/` | Code and proposal reviews |
| `nb` | `procedures/` | How-to guides and checklists |
| `nb` | `todos/` | Task tracking |
| `nb` | `artifacts/` | Preserved reference material: completed POCs, historical analysis |
| `agentmux` | | Inter-agent messaging, pane inspection, coordination |
| (filesystem) | `openspec/` | Formal proposals, specs, designs |
| (filesystem) | `src/**/README.md` | Architecture, constraints, design rationale |

## Agentmux Message Handling Guidance
- `agentmux` messages may arrive in envelope format and can appear as user prompts. Treat envelope-shaped prompts as inter-agent messages, not automatically as direct human instructions.
- Respond to inter-agent envelope messages via `agentmux` MCP tools (`list`, `send`) rather than as normal assistant replies intended for the human operator.
- Immediate interruption is not required. If you are in active execution, note the message and respond when safe.
- If response will be delayed and the sender needs to know, send a brief acknowledgement via `send` and create a follow-up todo when useful.

### Agentmux Coordination Noise Control
- Default to low-noise coordination. Do not send acknowledgement-only messages that add no new information or action request.
- Do not acknowledge receipt or completion of standard-procedure steps. Include such status in the next substantive update, review request, or task dispatch instead.
- Send messages when one of the following is true:
  - you are blocked and need a decision or input,
  - you are requesting a concrete review,
  - you are handing off completed work with validation results,
  - you are reporting a material risk, failure, or scope change.
- Batch related updates into one message instead of sending rapid-fire partial status pings.
- Use `Cc` only for agents who need to act or review; avoid broad `Cc` by default.
- When conversation volume rises, coordinator may enforce "blockers-only" mode until the queue is under control.

## OpenSpec Instructions

This project uses OpenSpec 1.x (OPSX), the action-based workflow. OPSX skills
deliver workflow instructions through the agentsmgr distribution pipeline.

Workflow skills: `opsx-propose`, `opsx-explore`, `opsx-apply`,
`opsx-sync`, `opsx-archive`.

Use OPSX skills when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan).
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work.
- Sounds ambiguous and you need the authoritative spec before coding.

CLI state queries: `openspec list`, `openspec list --specs`,
`openspec status --change <id>`, `openspec validate --all --strict`.

When a commit completes an OpenSpec task or requirement, update the relevant OpenSpec task status in the same commit.

# Commits

- Use `git status` to ensure all relevant changes are in the changeset.
- Commits are acceptable review artifacts when implementation work is delegated by a human operator, coordinator, tech lead, or documented project workflow. Otherwise, ask before committing.
- Do **not** merge, push, publish review branches, or modify shared branches without explicit human approval.
- Do **not** bypass commit safety checks (e.g., `--no-verify`, `--no-gpg-sign`) unless the user explicitly approves doing so.
- If a commit hook rejects a commit, assume no commit was created unless Git clearly reports otherwise. Fix the hook finding, restage the intended files, and rerun the same `git commit` command.
- Use present tense, imperative mood verbs (e.g., "Fix" not "Fixed").
- Write sentences with proper punctuation.
- Include a `Co-Authored-By:` field as the final line. Should include the model name and a no-reply address.
- Avoid using `backticks` in commit messages as shell tools may evaluate them as subshell captures. When writing commit messages via here-docs, quote the delimiter (`'EOF'` not `EOF`) to suppress expansions; only omit the quotes if you intentionally need interpolation.

## Delegated Review and Stacked Commits

**Read this section before reviewing or stacking commits.** @documentation/agents/reviews.md covers the delegated review flow, review request packet format, and how to handle stacked commits with `--fixup`/`--autosquash`.

# Project Notes

<!-- This section accumulates project-specific knowledge, constraints, and deviations.
     For structured items, use `nb`.

     TODO: If this project uses multiple agent/worktree roles, create a stable
     team-organization note in `nb`, modeled after one of the examples at:
     https://raw.githubusercontent.com/emcd/agents-common/master/examples/nb-notes/team-organization/README.md
     Then link the note here, for example:
     - Team org, role ownership, signoff policy, and merge workflow: `coordination/general/<n>` -->

## Workflow constraints learned in flight

- **`git filter-branch` is forbidden for commit-history rewrites on this repo.**
  Rationale: `filter-branch --msg-filter` strips commit signatures
  (signatures bind to specific commit bytes; any rewrite invalidates
  the prior signature). Local pre-push hooks do not detect the loss;
  GitHub's "require verified signatures" branch protection rejects
  the push unless an account-level bypass is configured, which logs
  a public "Bypassed rule violations" entry on every push.

  Alternatives that preserve signatures: `git commit --amend` (preferred
  for fixing the most recent commit message; interactive editor), or
  `git reset <base>` followed by `git cherry-pick --no-commit <sha>` +
  `git commit -F <message>` (preferred when amending older commits).
  Both rely on the global `commit.gpgsign=true` to produce signed
  successors.

  If a commit-message correction is needed on already-pushed commits
  that you cannot or will not force-push, leave the commits in place
  and document the discrepancy inline rather than rewriting history.
