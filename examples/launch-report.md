> This is the message the agent sent at the end of the run, unedited. It was written with an earlier
> version of the audit, which scored the starting point 28. The audit has since been made stricter
> (nothing is earned for things that are merely absent) and now scores the same starting point 15.

## Launch report: envdiff

**Launch score: 28 → 85** (a checklist of how the repo presents itself, not a prediction of stars, and it does not test whether the code works. It covers 85 of the 100 points: the 15 for the GitHub description, topics and social preview cannot be checked until the repo is pushed.)

The points still open are ones only you can earn: a license (8), your GitHub handle in place of `OWNER` (4) and a first tag (1). Nothing has been committed, pushed or posted.

### What changed

- `README.md`: rewritten. It now opens with one sentence, "Compare two `.env` files and see which keys are missing or different, without printing the values.", then the demo, an install command, real output for each flag, a "Why not `diff`?" section, how the parser reads a file, and a Limitations list. Your TODO list is at the end under the heading "Roadmap". Every output block is copied from a real run against `examples/`.
- `assets/demo.svg`: an animated terminal recording of the real tool comparing `examples/dev.env` with `examples/prod.env`, embedded under the pitch. `assets/demo.json` is the recipe for recording it again.
- `assets/social-preview.png`: the 1280x640 card shown when the repo link is shared.
- `pyproject.toml`: added description, readme, keywords and project URLs. I built and installed the package in a throwaway environment to check it; the `envdiff` command prints the same output as `python3 envdiff.py`.
- `CONTRIBUTING.md`: new and short. How to run it, run the tests and send a change.
- `.gitignore`: added `launch/` so the drafts stay out of the repo, plus `build/` and `dist/`, which a `pip install .` leaves behind.
- `launch/show-hn.md`: notes for Show HN, not a draft. Hacker News says "Please don't put generated text in HN posts. Write your text yourself", so this file has the rules, the facts I checked and an outline for you to write from.
- `launch/reddit.md`: drafts for r/commandline and r/Python. They are starting points to rewrite in your own words, with three gaps marked `[[author: ...]]` for things only you know, such as why you built it.
- `launch/checklist.md`: every manual step, in order, with the exact commands.
- `launch/handle-unreadable-files.patch`: a suggested fix for the bug below. It is not applied.

### Found by running it

- **A file that does not exist ends in a Python traceback.** `python3 envdiff.py examples/dev.env nope.env` prints a traceback and exits with status 1, the same status as "the files differ". This is the first thing someone trying the tool will hit. You asked for launch prep, so I did not change `envdiff.py`. I would fix it before posting, and the patch does that: it prints a one-line error, exits with status 2 and adds a test.
- **The parser is small, and it shows on awkward files.** `PORT=8000 # web` and `PORT=8000` are reported as different. A UTF-8 byte order mark breaks the first key. A duplicate key is silently resolved to the last one. Comparing `a/.env` with `b/.env` prints "Missing in .env" twice. `--json` never includes values. These are all in the README under Limitations now, so a commenter does not find them first.
- Small one: the last line reads "1 key match." when exactly one key matches.
- Both tests pass. I ran everything on Python 3.14 only. The source parses as 3.8 syntax, but it was not run on 3.8.

### Needs you

1. **Choose a license.** Without one nobody may legally use the code. Add the text as `LICENSE` (on GitHub: Add file > Create new file > name it `LICENSE` > Choose a license template), then add a `## License` section at the end of the README. The snippet is in `launch/checklist.md`, step 1.
2. **Replace `OWNER` with your GitHub handle.** There is no git remote, so I did not guess it. It is in 4 places in `README.md` and `pyproject.toml`, plus the launch files:
   ```sh
   grep -rl OWNER README.md pyproject.toml launch/ | xargs sed -i 's/OWNER/your-handle/g'
   ```
   I assumed the repo will be called `envdiff`. If not, change the URLs too.
3. **Decide about the traceback.** To apply the fix: `git apply launch/handle-unreadable-files.patch && python3 -m pytest`. Then delete the first bullet under Limitations in the README and the traceback sentence in both Reddit drafts.
4. **Check the name on PyPI:** `pip index versions envdiff`. I did not look it up, because that sends the name of an unannounced project to a public service. If the name is taken, people who type `pip install envdiff` out of habit get someone else's package, so say so next to the install command.
5. **Commit, then push to a private repo first** so you can see the page before anyone else:
   ```sh
   git add -A && git commit -m "Prepare for launch: README, demo, package metadata, CONTRIBUTING"
   gh repo create envdiff --private --source=. --remote=origin --push
   ```
6. **Set the description and topics.** The two `gh repo edit` commands are in the checklist, step 7. The description is the README pitch. The topics are cli, command-line-tool, python, dotenv, env, environment-variables, diff, configuration and devops.
7. **Upload the social preview.** GitHub has no API for it: Settings > General > Social preview > Edit > Upload an image > `assets/social-preview.png`.
8. **Make it public, then test the install on a clean machine before posting.** I could verify the install only from a local git URL, and pipx is not installed here. After that, tag `v0.1.0`. Commands are in the checklist, steps 10 to 12.
9. **Write the Show HN post yourself** from `launch/show-hn.md`, and rewrite the Reddit drafts in your own words. Read each subreddit's rules on self-promotion and AI-written posts first. Post on different days, and stay to answer for a few hours each time.

One thing to weigh before choosing Hacker News: Show HN asks that "the project should be non-trivial", and envdiff is about 70 lines with one commit. It may be a hard room. r/commandline is likely a kinder first stop. Expect "how is this different from X" either way: dotenv-linter has a `diff` command for .env files, so try it and have your own answer ready.

### Left alone

- `envdiff.py` and the tests: unchanged. The fix is offered as a patch.
- `LICENSE`: the choice is yours, so I did not add one or mention one in the README.
- X and other channels: you named Hacker News and Reddit, so I wrote only those.
- A GIF or MP4 of the demo: not needed for a README or a Reddit text post, and VHS is not installed here. Say if you want one.
- A tag, release or changelog: tagging is public and hard to take back, so it is a checklist step.
- Publishing to PyPI: still on your roadmap. One trap for later is in the checklist, section E: PyPI will not show the demo image from a relative path.

Three kinds of request left this machine, none with your project's name: repository counts for each topic via `gh`, the public pages for the Hacker News rules and dotenv-linter, and pip downloading setuptools for the test builds. Once the repo is pushed, ask me to run the audit again and it will score the GitHub metadata as well.
