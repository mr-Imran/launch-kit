# Contributing

Thanks for looking. The skill is small on purpose: one `SKILL.md`, four
reference files and three Python scripts that use only the standard library.

## Layout

```
skills/launch-kit/
  SKILL.md        the workflow the agent follows
  references/     guides loaded only when a step needs them
  scripts/        audit.py, term_demo.py, social_preview.py
  assets/         demo.tape (VHS template)
  evals/          test cases: a prompt, input files and graders for each
```

## Try a change

The scripts run on their own, so most changes can be checked without an agent:

```sh
python3 skills/launch-kit/scripts/audit.py examples/envdiff-before
python3 skills/launch-kit/scripts/audit.py examples/envdiff-after
python3 skills/launch-kit/scripts/term_demo.py --cmd "echo hello" -o /tmp/demo.svg
```

Keep them free of third-party imports and working on Python 3.8.

## Changing the audit

Every check has an id, a point value and a fix hint in `scripts/audit.py`. If
you add or re-weight a check, keep the five categories adding up to 100 and
say in the pull request why the check matters to someone landing on a repo.
A check should be hard to satisfy by accident and impossible to satisfy by
lying.

## Running the evals

Each folder under `skills/launch-kit/evals/` is one test case. With Claude Code
2.1.269 or later, from `skills/launch-kit/`:

```sh
claude plugin eval . --scaffold --allow-tools Write,Edit,Bash
```

These are real, billed model runs. Results land in `evals/results/`, which is
ignored by git.

## Reporting a problem

Open an issue with the repository you ran it on (or a small copy that shows the
problem), the audit output, and what you expected instead.
