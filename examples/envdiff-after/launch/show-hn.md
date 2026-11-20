# Show HN: notes for envdiff

These are notes to write from. There is no draft post in this file, on purpose.

## 1. Read this first

Hacker News asks for text the author wrote. From
news.ycombinator.com/newsguidelines.html:

> Please don't put generated text in HN posts. Write your text
> yourself—HN is for sharing between humans.

The same page says of comments: "Don't post generated text or AI-edited text."

So the post, the title and your replies are yours to write. Everything below
is material: the rules, the facts checked in this repository, and an outline.
None of it is text to paste, and it should not be run through an assistant for
polish afterwards either.

Before you post:

- Replace `OWNER` (see `launch/checklist.md`, step 2). The repository URL below
  was built from the package name in `pyproject.toml`, not from a git remote,
  so check it.
- Run the install command on a clean machine once the repository is public.
  It cannot work before that.
- A license must be in the repository. Without one, the first comment will be
  about that.
- Decide what to do about the traceback on a missing file (checklist, step 3).
- Do not ask anyone to upvote or comment. The Show HN rules say: "Please don't
  ask friends to upvote or comment."

## 2. Does it qualify?

From news.ycombinator.com/showhn.html: "Show HN is for something you've made
that other people can play with." A public repository with a working install
command qualifies. Today it does not, because nothing is public yet.

The harder rule: "The project should be non-trivial. Don't post
quickly-generated one-offs; anybody can do that now."

Honest reading: envdiff is at the small end. One file of about 70 lines, two
tests, one commit, version 0.1.0. It does one useful thing and the output is
clear, but some readers will say it is a ten-line script, and others will name
an existing tool and ask what is different. Show HN may be a hard room for it.
A specific subreddit (r/commandline, see `launch/reddit.md`) is likely a kinder
first stop, and what you learn there makes a later Show HN stronger. The
decision is yours.

Also from that page: "If your work isn't ready for users to try out, please
don't do a Show HN." A typo in a file name currently produces a Python
traceback. Fix that first if you post here.

## 3. Title format

`Show HN: Name – what it does`

- The submission form limits titles to 80 characters.
- No uppercase for emphasis, no exclamation points, no saying how good it is.
- Facts a title for this project should carry: the name (envdiff), the verb
  (compare), the object (two .env files). Optional fourth fact if it fits:
  values are not printed.

You word it.

## 4. URL

`https://github.com/OWNER/envdiff`

Handle unknown: this folder has no git remote. Repository name assumed to be
`envdiff`, taken from `pyproject.toml`. Check both after pushing.

## 5. Facts to draw on

Checked on 2026-11-20 with Python 3.14.4 on Linux, by running the code in this
repository.

What it does:

- compares two .env files by key, not by line
- three groups in the output: keys missing in the second file (`-`), keys
  missing in the first (`+`), keys in both with different values (`~`)
- last line counts the keys that match
- values hidden by default; `--values` prints them for the differing keys
- `--json` prints the three lists of key names
- exit status 0 when identical, 1 when anything differs, 2 on wrong arguments

How it works (this audience reads the code):

- single file, `envdiff.py`, about 70 lines
- standard library only: argparse, json, os, sys
- parser, in order: strip the line; skip blanks and lines starting with `#`;
  drop a leading `export `; skip lines with no `=`; split on the first `=`;
  trim whitespace on both sides; strip surrounding `"` and `'` from the value
- comparison: set difference and intersection on the keys of two dicts,
  output sorted by key
- trade-off: a deliberately small parser, not a full dotenv implementation

Verified by running it:

- `examples/dev.env` against `examples/prod.env` gives the output shown in the
  README (2 missing in prod.env, 1 missing in dev.env, 2 different, 2 match)
- reordered keys, comments, `export` prefix and quotes produce no differences
- `pip install` from a git URL builds a wheel and installs an `envdiff`
  command; its output is byte-identical to `python3 envdiff.py`
- both tests pass
- source parses as Python 3.8 syntax; it was not run on 3.8 itself

What does not work yet:

- a path that does not exist, or a directory: Python traceback, exit status 1,
  which is the same status as "the files differ"
- inline comments stay in the value: `PORT=8000 # web` differs from `PORT=8000`
- no multi-line values, no `${VAR}` expansion
- duplicate key in one file: last one wins, nothing reported
- UTF-8 byte order mark: becomes part of the first key, reported as missing on
  both sides
- headings use the base file name: `a/.env` against `b/.env` prints
  "Missing in .env" twice
- `--json` never includes values, with or without `--values`
- "1 key match." when exactly one key matches (grammar)
- not on PyPI; whether the name is free there was not checked

Similar tools:

- the repository names none; the README compares only with plain `diff`
- commenters will name others and ask what is different. One that exists:
  dotenv-linter has a `diff` command (`dotenv-linter diff .env .env.example`;
  its README, read on 2026-11-20, says it "can compare `.env` files with each
  other and output the difference between them"). It was not run here, so
  nothing above says how the two differ. Try it, and whatever a search for
  "compare .env files" turns up, before posting, so the answer is yours and
  accurate

## 6. Outline for the first comment

Questions to answer in your own words. A few sentences each is enough.

1. Who are you, in one line?
2. What made you build it? What were you doing when two env files disagreeing
   cost you time?
3. What does it do? (One or two sentences. The README pitch is the fact; say
   it your way.)
4. How does it work? (The parser rules and the set comparison above. Why
   values are hidden by default.)
5. What is rough? (Pick from "What does not work yet". Saying it first is
   better than having it pointed out.)
6. What feedback do you want? (For example: which .env syntax people expect
   it to handle.)

## 7. Formatting

Hacker News is plain text, not Markdown.

- Blank line between paragraphs.
- Code and terminal output: indent by two or more spaces, with a blank line
  before and after. Backticks and fenced blocks show up literally.
- No bullet syntax.
- `*text*` gives italics.
- URLs link themselves.

## 8. On the day

- Post when you can stay for the next few hours and answer.
- Reply in your own words.
- Do not ask anyone to upvote.
- Thank people who find problems, and fix what they report.
