# The top of the README

The README is the repository's landing page, and almost every visitor decides
from the part they can see without scrolling. Spend most of the effort there.

## Contents

1. The first screen
2. Writing the pitch
3. The install command
4. Below the fold
5. What to cut
6. Words that cost trust
7. What to keep
8. Skeleton
9. Before you finish

## 1. The first screen

In this order, within about the first 40 lines:

1. **Name.** One `#` title. Nothing else on the line.
2. **Pitch.** One sentence: what it does, for whom or when.
3. **Demo.** The thing working: a terminal recording, a screenshot, a short
   output sample. See `demo.md`.
4. **Install and first command.** Copy, paste, see something happen.

Badges, if any, go between the name and the pitch or after the pitch, and only
the few that carry information (build status, version, license). A wall of
badges pushes the pitch down and reads as decoration.

## 2. Writing the pitch

A good pitch is concrete enough that the right reader recognises their own
problem, and the wrong reader knows to leave. Two tests:

- **Could this sentence sit on a hundred other repositories?** Then it says
  nothing. "A fast, modern, lightweight tool" fits everything.
- **Does it name the thing acted on?** Verbs need objects: compares *what*,
  generates *what*, from *what*.

Shapes that work:

| Shape | Example |
|---|---|
| Verb + object + situation | "Rename photos by the date they were taken, read from their EXIF data." |
| X for Y | "A Postgres client for people who live in the terminal." |
| Like X, but Y | "Like `du`, but it shows the answer as a tree you can navigate." |
| Outcome first | "Find out what is holding port 3000, and stop it." |

Before and after:

| Before | Why it fails | After |
|---|---|---|
| "This is a script I wrote for my photos." | Opens with the author, not the reader. Says nothing about what happens. | "Rename photos by the date they were taken, read from their EXIF data." |
| "Welcome to DataFlow! DataFlow is a powerful platform that leverages modern technology to streamline your workflows." | Says nothing a reader can picture. | "Run SQL across CSV, Parquet and JSON files as if they were one database." |
| "A blazingly fast, lightweight, zero-config bundler." | Adjectives without evidence. | "Bundles a TypeScript library to ESM and CJS with one command and no config file." |

Keep it to one sentence of roughly 120 characters. A second sentence may add
the differentiator ("No dependencies. Works on macOS and Linux."), but only
facts.

If there is a number, it must exist: measured in this repository, reproducible
by the reader, with the method one click away. No number is better than an
invented one.

## 3. The install command

- Give the shortest command that works **today**. If the package is not
  published, say how to run it from the repository instead of printing a
  registry command that will fail:
  ```sh
  pipx install git+https://github.com/OWNER/REPO
  ```
- Run it, or verify every part of it, before writing it down. With no remote
  yet, the install-from-GitHub command cannot run, but its mechanics can:
  install from a temporary copy of the repository in a throwaway environment
  (`pip install git+file:///tmp/copy`, or `npm pack` and install the tarball)
  and check that the installed command behaves like the one in the checkout.
  Say in the report that the real URL is untested until the repository exists.
- State prerequisites in a few words next to it ("Needs Python 3.8+").
- Follow it at once with the first real command and its real output. Install
  alone does not show what the tool does.
- Owner and repository names come from `git remote get-url origin`. If there is
  no remote yet, write `OWNER` where the handle goes and list it under "Needs
  you" with one command that fills every occurrence. Do not guess a handle.
- If the tool has not been published and you could not confirm the registry
  name is free, say "not on <registry> yet" rather than promising a future
  `pip install name`.

## 4. Below the fold

A sensible order for what follows. Leave out any section with nothing real to say.

1. **Why / how it is different.** Three to five plain bullets, or a short
   paragraph naming the usual alternative and the difference.
2. **Usage.** Real commands with real output. Cover the two or three things
   people will do, not every flag.
3. **Options or reference.** A table, or a link to docs when it is long.
4. **Limitations.** What it does not do yet. This section earns more trust
   than any feature list, and it saves the author from the same issue filed
   ten times.
5. **Contributing.** How to run it locally and the tests, in three lines, or a
   link to CONTRIBUTING.md.
6. **License.** One line.

## 5. What to cut

Move down, move to `docs/`, or delete:

- A table of contents on a README that fits on two screens.
- The project's history, the author's biography, a long changelog.
- "TODO" and "Coming soon" lists at the top. Open items belong in issues or a
  short Roadmap near the end.
- Requests for stars. People star what was useful to them.
- Screens of configuration reference before the reader has seen it work.

## 6. Words that cost trust

Readers of developer tools have learned to skip marketing language, and they
have learned what machine-written copy looks like. Avoid:

- Unproven adjectives: blazingly fast, powerful, robust, seamless, modern,
  cutting-edge, next-generation, revolutionary, enterprise-grade.
- Empty verbs: leverage, streamline, supercharge, unlock, empower, elevate.
- "Welcome to", "Introducing", "Say goodbye to".
- An emoji in front of every heading and bullet.
- Feature bullets that are all adjectives ("Fast", "Simple", "Flexible").

Say what happens instead. "Parses a 1 GB log in 4 seconds on a 2021 laptop
(script in `bench/`)" beats "blazingly fast", and if you cannot write the first
sentence truthfully, the second one was not true either.

## 7. What to keep

- Everything accurate that the author wrote, even if you move it.
- Credits, acknowledgements, citations, sponsor notes.
- Section headings other pages may link to. If a heading must be renamed,
  mention it in the report.
- The author's voice. A plain, slightly informal README written by a person is
  more convincing than polished copy.

## 8. Skeleton

```markdown
# name

One sentence: what it does, for whom or when.

<p align="center">
  <img src="assets/demo.svg" alt="name renaming a folder of photos by the date each was taken" width="720">
</p>

## Install

    <command that works today>

Needs <runtime and version>.

## Usage

    <first real command>

    <its real output>

## Why

<the usual alternative, and what is different here>

## Limitations

## Contributing

## License
```

Adapt it. A library needs a code sample where a CLI has a terminal recording;
a web app needs a screenshot and a link to a running instance.

## 9. Before you finish

- Every command in the README was run, or each part of it verified.
- Every relative link and image path resolves (the audit checks this).
- Every number has a source in the repository.
- Images have alt text that says what they show.
- Nothing from a template is left: no "Project Title", no "your-username".
