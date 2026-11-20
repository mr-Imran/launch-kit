# Reddit drafts for envdiff

## Before you post

- **These drafts are a starting point, not posts.** Many subreddits have a rule
  about AI-written posts, and moderators remove what reads like one. Check each
  subreddit's rule on it, then rewrite the post in your own words.
- **Read each subreddit's rules on self-promotion before posting** (sidebar and
  wiki). Some forbid it, some allow it only on certain days or in a showcase
  thread, some require a flair. I have not checked them, and neither subreddit
  below should be treated as safe to post in until you have.
- **Gaps to fill.** They are marked `[[author: ...]]`. There is one in the
  r/commandline draft and two in the r/Python draft. They are things that are
  not in the repository, so I did not make them up.
- **Verify on the day:**
  - `pipx install git+https://github.com/OWNER/envdiff` works on a clean
    machine. It cannot work until the repository is public.
  - The repository URL. `OWNER` is a placeholder, and the name `envdiff` came
    from `pyproject.toml`, not from a git remote.
- **If you apply `launch/handle-unreadable-files.patch` first**, delete the
  sentence about the traceback from both drafts.
- One subreddit per day, not both at once. Stay and answer comments for a few
  hours after each post.
- Never ask for upvotes or stars, and do not ask friends to vote.
- Code and output below are indented by four spaces on purpose. Fenced code
  blocks do not render on old Reddit and some apps.

## Where to post

1. **r/commandline**: people who use and build terminal tools. A small
   single-purpose CLI is the kind of thing that gets read there. Lead with the
   workflow.
2. **r/Python**: the tool is one standard-library Python file, and that
   community cares about how something is built. From memory, and to be
   checked against their current rules: project posts there go under a
   "Showcase" flair and are expected to have three sections (What My Project
   Does, Target Audience, Comparison). The draft is laid out that way.

Not drafted, on purpose: r/devops is where the people with dev/staging/prod env
files are, but it is strict about self-promotion and a tool this small is
likely to be removed. r/opensource and r/SideProject accept showcases but few
readers there have this problem. If the first two posts go well and you want a
third, write it for that community rather than reusing one of these.

## Draft 1: r/commandline

Title:

```text
envdiff: compare two .env files by key, without printing the values
```

Body:

```text
[[author: one or two sentences on what made you write this. What were you doing when two env files disagreeing cost you time?]]

envdiff takes two .env files and tells you which keys are missing on each side and which have different values:

    $ envdiff examples/dev.env examples/prod.env
    Missing in prod.env (2):
      - DEBUG
      - SENTRY_DSN
    Missing in dev.env (1):
      + REDIS_URL
    Different values (2):
      ~ DATABASE_URL
      ~ LOG_LEVEL
    2 keys match.

Plain diff compares lines, so a reordered file, a comment or an "export" prefix shows up as a change, and every changed line is printed with its value. envdiff compares keys and prints only the names. --values adds the differing values, and --json gives the same lists to a script.

It exits 0 when the files match and 1 when they don't, so it can be a CI step.

It's one Python file with no dependencies (Python 3.8+). It isn't on PyPI yet, so for now:

    pipx install git+https://github.com/OWNER/envdiff

or clone the repo and run python3 envdiff.py a.env b.env.

What it doesn't do: it's a small parser, not a full dotenv implementation. Inline comments are kept as part of the value, there are no multi-line values and no ${VAR} expansion. A path that doesn't exist currently gives you a Python traceback instead of a clean error.

Repo: https://github.com/OWNER/envdiff

Tell me what's wrong or missing, especially .env syntax you'd expect it to handle.
```

## Draft 2: r/Python

Title:

```text
envdiff: a single-file, standard-library CLI that compares two .env files
```

Body:

```text
**What My Project Does**

envdiff compares two .env files by key. It lists the keys missing from each file and the keys whose values differ, and it does not print the values unless you pass --values.

    $ envdiff examples/dev.env examples/prod.env
    Missing in prod.env (2):
      - DEBUG
      - SENTRY_DSN
    Missing in dev.env (1):
      + REDIS_URL
    Different values (2):
      ~ DATABASE_URL
      ~ LOG_LEVEL
    2 keys match.

There is a --json flag, and the exit status is 0 when the files match and 1 when they don't.

It is one file of about 70 lines that imports only argparse, json, os and sys. The parser skips blank lines and comments, drops a leading "export ", splits on the first "=" with str.partition, and strips surrounding quotes. The comparison is set arithmetic on the keys of two dicts.

**Target Audience**

Anyone who keeps more than one .env file for the same app (dev and prod, or .env and .env.example) and wants to check that they have the same keys. It is version 0.1.0 with two tests, so treat it as a small utility.

[[author: one or two sentences on why you built it and how you use it yourself]]

**Comparison**

Plain diff compares lines: reordering, comments, "export" prefixes and quoting all show up as changes, and the values are printed. envdiff compares keys and hides values by default.

[[author: how it compares with any dotenv tools you have tried, for example the diff command in dotenv-linter. If you have not tried any, say so. People will ask.]]

It is not a full dotenv parser: inline comments are kept as part of the value, there are no multi-line values and no ${VAR} expansion. A path that doesn't exist currently ends in a traceback instead of a clean error.

Install (not on PyPI yet):

    pipx install git+https://github.com/OWNER/envdiff

Repo: https://github.com/OWNER/envdiff

I'd like to know what's wrong or missing.
```
