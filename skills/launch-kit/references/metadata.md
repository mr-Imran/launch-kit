# Repository metadata

The description, topics and social preview are what people see **before** they
open the repository: in search results, on topic pages, and when a link is
pasted into a chat or a post.

Everything here changes the public repository. Prepare the values, show them to
the author, and apply them only after a yes. If nobody is there to say yes,
write the exact commands into `launch/checklist.md` instead.

## Contents

1. Description
2. Topics
3. Social preview image
4. Homepage
5. A first release
6. Package manifest
7. A repository that is not pushed yet
8. The license, when the author has to choose

## 1. Description

- GitHub allows up to 350 characters, but lists and link previews cut it far
  earlier. Aim for under 120.
- Reuse the README pitch. One message everywhere is easier to remember.
- Start with what it does. Do not repeat the repository name; it is already
  shown next to it.

```sh
gh repo edit OWNER/REPO --description "Rename photos by the date they were taken, read from their EXIF data"
```

## 2. Topics

Topics put the repository on browsable pages (`github.com/topics/<name>`) and
feed GitHub search.

Rules GitHub enforces: lowercase letters, digits and hyphens; at most 50
characters each; at most 20 topics.

Choose 5 to 10, mixing:

| Kind | Examples |
|---|---|
| What it is | `cli`, `linter`, `library`, `github-action` |
| Language or runtime | `python`, `nodejs`, `rust` |
| Domain | `photography`, `devops`, `postgres`, `markdown` |
| Ecosystem it plugs into | `claude-code`, `agent-skills`, `vscode-extension` |
| The job it does | `file-renaming`, `code-review`, `testing` |

Prefer topics people already browse. Check how many repositories use one:

```sh
gh api "search/repositories?q=topic:exif&per_page=1" --jq .total_count
```

This sends only the topic name, never the project's. A topic with a few
hundred to tens of thousands of repositories is a real page with a real
audience. A topic you invented has no visitors. A huge topic that does not
describe the project (`javascript` on a shell script) is spam, and visitors
arriving from it leave at once.

```sh
gh repo edit OWNER/REPO --add-topic cli --add-topic exif --add-topic python
```

## 3. Social preview image

This is the card shown when the repository link is shared. Without one, GitHub
generates a generic card.

```sh
python3 scripts/social_preview.py --title "mytool" \
    --tagline "Rename photos by the date they were taken, read from their EXIF data" \
    --command "pipx install mytool" \
    --footer "github.com/realhandle/mytool" --label "CLI" \
    -o assets/social-preview.png
```

GitHub's requirements: PNG, JPG or GIF, under 1 MB, at least 640x320, and
1280x640 for the best result. The script writes 1280x640.

The image is a picture, so nothing in it can be fixed later with search and
replace. Put only settled facts on it:

- No `OWNER` or other gap. If the handle is unknown, leave `--footer` out, or
  use a fact instead ("Python 3.8+ · no dependencies").
- A `--command` that works, or one that does not depend on the handle (the
  run command rather than an install-from-GitHub URL). Leave it out if no such
  command exists yet.

Look at the image after generating it. Text widths are estimated, so a very
long title or command can run close to the edge; shorten the text if it does.

There is no API for uploading it. The author does this by hand:

1. Open the repository on GitHub, then **Settings**.
2. Under **General**, find **Social preview** and choose **Edit**.
3. **Upload an image** and pick `assets/social-preview.png`.

Always list this under "Needs you" in the report.

## 4. Homepage

Set it when there is somewhere better than the repository to send people: the
docs site, a live demo, the package page.

```sh
gh repo edit OWNER/REPO --homepage "https://example.org/docs"
```

Leave it empty rather than pointing it back at the repository.

## 5. A first release

A tagged release lets people pin a version and gives the repository a
"Releases" entry in the sidebar. The audit gives a point for a tag or a
changelog.

```sh
git tag v0.1.0 && git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes "First public release."
```

Tagging and releasing are public and hard to take back cleanly, so they are
the author's step: put the commands in the checklist and leave the point
unearned. Do not invent a changelog to collect it.

## 6. Package manifest

Registries show these fields, and the audit checks them:

- `package.json`: `description`, `keywords`, `repository`.
- `pyproject.toml`: `description`, `keywords`, and `[project.urls]`.
- `Cargo.toml`: `description`, `keywords`, `repository`.

Use the same pitch and a subset of the same topics. A repository URL that
still says `OWNER` does not count, and the audit says so.

## 7. A repository that is not pushed yet

Common on launch week: the code exists only on the author's machine.

- GitHub metadata cannot be checked or set. Prepare the values and put the
  commands in `launch/checklist.md`, ready to paste.
- The handle is unknown unless the author gave it. Use `OWNER` in text files
  and give one command that replaces it everywhere, for example:
  ```sh
  grep -rl OWNER README.md CONTRIBUTING.md pyproject.toml launch/ | xargs sed -i 's/OWNER/their-handle/g'
  ```
  List the files that really contain it; do not paste this line unchanged.
  Name `launch/` explicitly when it is in `.gitignore`: many search tools skip
  ignored folders and would miss it. On macOS, `sed -i` needs an empty
  argument after it (`sed -i ''`).
- Suggest pushing to a **private** repository first. The author can then see
  how the README and demo render, set the description and topics, upload the
  social preview, and switch to public when everything looks right.
  ```sh
  gh repo create NAME --private --source=. --remote=origin --push
  ```
  Making it public is safest from the web page (Settings > General > Danger
  Zone > Change visibility): the `gh` flags for this differ between versions.

## 8. The license, when the author has to choose

You do not choose it, but you can make choosing take two minutes. Put this in
"Needs you" and in the checklist:

- Why it blocks the launch: without a license nobody may legally use, change
  or share the code, and it is the first thing commenters point out.
- Where to decide: https://choosealicense.com. MIT and Apache-2.0 are the
  common picks for small tools; say that it is a legal choice and theirs.
- How to add it: on GitHub, **Add file > Create new file**, name it `LICENSE`,
  and pick a template. Or copy the text into `LICENSE` locally.
- What follows from it, ready to paste once they have chosen: a `## License`
  section for the end of the README, and the license field for the manifest
  (`"license": "MIT"` in `package.json`; in `pyproject.toml` the form depends
  on the build backend's version, so check before writing it).

Leave the README without a License section until then. A heading that says
"License: to be decided" helps nobody and the audit does not count it.
