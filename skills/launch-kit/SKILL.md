---
name: launch-kit
description: >-
  Make a GitHub repository launch-ready and measure it with a 0-100 launch
  score. Audits the repo, rewrites the top of the README around a one-line
  pitch, records a real terminal demo as an animated SVG (no dependencies),
  generates the 1280x640 social preview image, picks the description and
  topics, and prepares the launch posts (Show HN notes, Reddit and X drafts)
  within each community's rules. Use this
  whenever someone is about to open-source, publish, release, announce or
  promote a repository; asks to improve or rewrite a README, add a demo GIF or
  screenshot, get more GitHub stars, reach or visibility, choose topics, make a
  social preview or OG image, or write a Show HN, Reddit or launch post; or
  asks whether a repo is ready to share, even if they never say "launch".
license: MIT
compatibility: >-
  Bundled scripts need Python 3.8+. Optional: gh CLI (GitHub metadata), VHS
  (GIF or MP4 demos), any SVG rasterizer or Chrome (social preview PNG).
metadata:
  version: "0.1.0"
---

# Launch Kit

A visitor gives a repository a few seconds. In that time they need to learn
what it does, see it working, and find the command to try it. Most repositories
fail at one of the three, and good code goes unnoticed.

This skill gets a repository ready for that visit and for the day it is
announced. It works in a loop: measure, fix the thing that costs the most,
measure again.

Two kinds of path appear below. `scripts/...` and `references/...` live in
this skill's folder (the one that contains this file), so call the scripts by
their full path. Everything else (`assets/demo.svg`, `launch/`, `README.md`)
is in the user's repository.

## Ground rules

These four shape every decision, so they come first.

**Only true claims.** What you write will be read by people deciding whether to
trust the author. An invented benchmark, a user count nobody measured, a
testimonial, a "used by" row, or an install command for a package that is not
published yet will be noticed, and then the launch thread is about that instead
of the project. If a fact would strengthen the pitch and you cannot confirm it
from the repository or by running the code, ask the author or leave it out.

**It is the author's project.** Sharpen and reorder; keep what is accurate,
keep credits and links, keep their way of talking where it works. A README that
is already good needs a small edit, not a rewrite.

**Local files freely, public things only when asked.** Editing the working tree
is the job. Committing, pushing, changing the repository's description or
topics, creating a release, and posting anywhere all reach other people, so do
them only if the author asked for that. Launch posts are material for the
author: they write the final words and post from their own account. Hacker
News asks for no generated text in posts at all, so for Show HN this skill
prepares notes and never the post itself.

**The score is a checklist, not a forecast.** It measures how well the
repository presents itself. It cannot tell whether people want the thing, and
it does not look at whether the code works. Say this when you report a score.

## Workflow

### 1. Understand the project

Read the README, the manifest and the entry points. Then run the thing: the
help text, the bundled example, the tests, and two or three inputs a new user
might plausibly try (a missing file, an empty argument, the second example in
the README). Do this for every request, including "just audit it" and "just
write the posts". What you learn here is what makes the rest true: the real
output goes in the README, and the rough edges you hit are the limitations the
README and the launch posts must admit before a commenter finds them.

Keep the working tree clean while you do it. Tests and builds drop caches and
build folders into the repository; run them from a temporary copy, or with
their cache options turned off, or remove what they left. Trying the install
from a copy, in a throwaway environment, is the only way to know the install
command works, so do that too when it is cheap. Clean up only what you
created.

Some tools act on the machine itself: they kill processes, delete files, send
requests, change settings. Exercise those against things you made for the
purpose (a throwaway server, a temporary folder), and never point a
destructive option at anything you did not start.

Then answer four questions, because everything later is built from them:

- What does it do? One sentence with a concrete verb and object.
- Who needs it, and at what moment?
- What would they use otherwise, and what is different here?
- What proof exists today? Real output, passing tests, a number someone measured.

If running it turns up a bug, say so plainly in your report. Change the code
only when the request covers code changes. "Get it ready to launch" is about
how the project is presented, so leave the behaviour alone: list the bug under
"Needs you", name it as a limitation wherever you describe the tool, and if
the fix is small, offer it as a tested patch file next to the launch notes
(`launch/<what-it-fixes>.patch`) so the author can apply it with one command.

**Which install command works today?** A name in `package.json` or
`pyproject.toml` does not mean the package is published. Look for evidence in
the repository first: a note in the README, a publish workflow, version tags.
A registry lookup (`npm view <name>`, `pip index versions <name>`) can settle
it, with two cautions. It tells a public service the name of a project that
may not be announced yet, so skip it when the author has not gone public, and
hand them the command instead. And a hit only proves the name is taken:
compare the repository URL before concluding it is this project. When in
doubt, write the command that works from the repository and put "confirm the
registry name" under "Needs you".

**Whose repository is it?** Owner and name come from `git remote get-url
origin`. Failing that, a repository URL in the manifest will do, flagged for
the author to confirm. With neither, do not guess a handle: write `OWNER`
where it goes, keep a count of the places, and give the author one command
that fills them all. The audit keeps the placeholder check failing until they
do, which is correct.

### 2. Measure

```sh
python3 scripts/audit.py /path/to/repo          # readable report
python3 scripts/audit.py /path/to/repo --json   # for parsing
```

The audit scores five areas: first impression (40), README depth (20),
repository hygiene (15), GitHub metadata (15) and launch assets (10). GitHub
metadata needs the `gh` CLI and a pushed repository; when it cannot be checked
it is skipped and the score covers the rest. The line under the score says
how many points were in play, and the gains in the fix list are counted in
those points, not in the 0-100 score: say which scale you mean when you quote
them. Keep the first result: the final report compares against it.

If the audit reports secret files in the repository, stop and tell the author
before anything else. Nothing else matters until that is fixed.

**When the author only asked how ready the repository is**, change nothing and
report in this shape. No reference files are needed for this path; the audit's
own hints are enough.

```markdown
## Launch readiness: <repo>

**Launch score: <n>/100** (<earned> of <possible> points; <what was not
checked and why>. A checklist of how the repo presents itself, not a
prediction of stars.)

<Two or three sentences: what the project is, and the verdict in plain words.>

### What to fix, biggest gain first
1. <piece of work> (+<points> of the <possible> in play): <what is wrong now,
   what done looks like, and whether it needs a decision from you>

### Found by running it
- <bugs and rough edges the audit cannot see, with the command that shows each>

### Needs a decision from you
- <license, GitHub handle, registry name: things nobody else can choose>
```

### 3. Fix, largest gain first

The audit groups fixes by piece of work and orders them by points. The usual
order:

1. **Top of the README**: title, one-line pitch, demo, install command, first
   example. Read `references/readme-hook.md` before writing.
2. **Demo**: record the real tool doing its one most convincing thing. Read
   `references/demo.md`. For anything with a command line:
   ```sh
   python3 scripts/term_demo.py --spec assets/demo.json -o assets/demo.svg
   ```
   It runs the commands for real and writes an animated SVG that plays in a
   GitHub README. No recording tools are needed.
3. **Hygiene**: package metadata, a short CONTRIBUTING, and the license.
   Choosing a license is a legal decision that belongs to the author. If the
   manifest already names one, add the matching LICENSE file. Otherwise ask,
   and if nobody can answer, leave it and put it first under "Needs you".
4. **Metadata**: description, topics, homepage, and the social preview image.
   Read `references/metadata.md`.
   ```sh
   python3 scripts/social_preview.py --title NAME --tagline "the pitch" \
       --command "install command" --footer "github.com/owner/repo" \
       -o assets/social-preview.png
   ```
   GitHub has no API for the social preview, so uploading it is always a manual
   step for the author.
5. **Launch posts**: one file per channel in `launch/`. Read
   `references/launch-posts.md` first: the rules differ by community, and for
   Hacker News you write notes for the author instead of a post. Cover the
   channels the author named; if they named none, cover Show HN, Reddit and X.

Follow the repository's own conventions for where assets live (`docs/`,
`.github/`, `media/`); use `assets/` when it has none.

Some points can only be earned by the author: the license, the first tag, the
description and topics on GitHub, the social preview upload, the real handle
in place of `OWNER`. Do not chase them. A score in the high 80s with a clear
"Needs you" list is the right result for a repository that has not been pushed.

### 4. Measure again and report

Run the audit again and report in this shape:

```markdown
## Launch report: <repo>

**Launch score: <before> → <after>** (a checklist of how the repo presents
itself, not a prediction of stars<; what was not checked and why>)

### What changed
- <file>: <what and why, one line each>

### Needs you
1. <manual steps in order: license choice, handle, upload social preview,
   apply topics, review drafts, post>

### Left alone
- <anything you decided not to do, and the reason>
```

"Needs you" matters most: it is the part of the launch that only the author
can do, so make each step concrete enough to do without thinking (exact
setting, exact command).

## Partial requests

People often want one piece. Do that piece well and skip the rest.

| The request | Do | Read | Skip |
|---|---|---|---|
| "Is this ready?" / "audit my repo" | Steps 1-2, readiness report | nothing | All edits |
| "Fix / rewrite my README" | Steps 1-2, README, demo if missing, step 4 | readme-hook, demo | Launch drafts |
| "Add a demo GIF" | Step 1, demo, embed it | demo | Everything else |
| "Write my Show HN / Reddit / X post" | Step 1, those channels only (notes for Show HN, and say why) | launch-posts | The audit, README and code edits, other channels, the checklist |
| "Pick topics" / "social image" | Step 1, that item | metadata | Everything else |
| "Get it ready to launch" | Everything | all four | Nothing |

For a partial request there is no before and after, so drop the score line and
report in this shape:

```markdown
## <What you made>: <repo>

<One or two sentences: what is ready and where it is.>

<The deliverable itself, when it is text.>

### Found by running it
### Needs you
### Left alone
```

When the deliverable is text the author will paste somewhere (a Reddit draft,
a pitch, topics), put it in the reply in full as well as in a file: they want
to read it now. For notes they will write from (Show HN), give the core in
the reply and the path to the rest.

"Don't touch the code or the README" is a boundary for the whole task. New
files that you were asked for (drafts under `launch/`) are fine; edits to
existing files are not, including `.gitignore`. Mention what you would have
changed instead.

## Scripts

| Script | What it does |
|---|---|
| `scripts/audit.py [repo] [--summary] [--json] [--no-remote] [--min N]` | Launch score with fixes grouped by piece of work. `--summary` prints the score and area totals only; `--min N` exits 1 below N, for CI. |
| `scripts/term_demo.py --spec FILE -o demo.svg` | Runs commands and records them as an animated terminal SVG. `--cmd "..."` for quick one-offs, `--frame SECONDS` for a still. |
| `scripts/social_preview.py --title ... -o social-preview.png` | 1280x640 card, converted to PNG with whatever rasterizer is installed. |

All three use only the Python standard library. Run any of them with `--help`
for every option.

## References

- `references/readme-hook.md`: the top of the README, pitch formulas, before and after examples, what to cut.
- `references/demo.md`: what to show, the demo spec format, checking the result, GIF and MP4 with VHS, screenshots for apps with a UI.
- `references/metadata.md`: description, topics, social preview upload, releases, a repository that is not pushed yet.
- `references/launch-posts.md`: what each community allows (Hacker News wants self-written text), Show HN notes, Reddit and X drafts, text formatting, launch-day checklist.
- `assets/demo.tape`: VHS template for when a GIF or MP4 is needed.
