# The demo

A demo answers "does it work, and what does that look like?" faster than any
paragraph. It goes directly under the pitch.

## Contents

1. What to show
2. Route A: animated SVG with `term_demo.py` (default)
3. Checking what you recorded
4. Route B: GIF or MP4 with VHS
5. Route C: projects with a UI
6. Projects with nothing to run
7. Embedding it
8. Keeping it honest

## 1. What to show

One moment where the value is obvious. Not a tour.

- Two to four commands. Under about 20 seconds.
- Start from a state the reader recognises (two config files, a failing test,
  a messy folder) and end on the result.
- Real output from the real tool, run just now.
- Use sample data that lives in the repository (`examples/`), so readers can
  repeat it. If there is none, create a small example folder and say so in the
  report: it is useful to users as well.

**Size.** Aim for 80 columns and about 20 rows, which is what fits a README at
full size. These are targets, not limits. If the line that carries the point
is 88 characters wide, set `"cols": 90` rather than letting it wrap in the
middle of a word: a wider recording is scaled down a little, and a wrapped
line is hard to read at any size. Past about 100 columns or 26 rows the text
gets too small; show less instead (`max_lines`, fewer commands). Leave
`"rows"` out of the spec and the window fits what was recorded; the script
warns when a recording is too tall and its first lines scroll away.

Run demo commands somewhere safe: inside the repository or a temporary
directory, with sample data, never against the author's real accounts, home
directory or production services.

## 2. Route A: animated SVG (default)

`scripts/term_demo.py` runs commands, captures what they print, and writes an
animated SVG. It needs only Python. The SVG plays in a GitHub README, loops,
stays sharp at any size, and is usually 10 to 40 KB.

Write a spec next to the output so the demo can be re-recorded after changes:

```json
{
  "//": "Re-record: python3 term_demo.py --spec assets/demo.json -o assets/demo.svg (term_demo.py is part of launch-kit)",
  "title": "mytool",
  "cols": 80,
  "cwd": "..",
  "steps": [
    {"comment": "Which images in this folder are over 1 MB?"},
    {"cmd": "mytool scan examples/photos",
     "exec": "node ./bin/cli.js scan examples/photos"},
    {"cmd": "mytool scan examples/photos --fix --dry-run",
     "exec": "node ./bin/cli.js scan examples/photos --fix --dry-run",
     "max_lines": 10},
    {"pause": 1}
  ]
}
```

```sh
python3 scripts/term_demo.py --spec assets/demo.json -o assets/demo.svg
```

Relative `cwd` values are resolved from the spec file's folder, so a spec in
`assets/` wants `"cwd": ".."` to run from the repository root.

The recorder is not part of the author's repository, so the spec alone does
not tell a contributor how to use it. The `"//"` line is for that (unknown
keys are ignored); say where `term_demo.py` comes from, in the spec or in
CONTRIBUTING.

Things worth knowing:

- **`cmd` is what the viewer sees; `exec` is what runs.** Use `exec` when the
  published spelling does not work yet in this checkout (`npx mytool` before
  the package is on npm, an entry point that is not installed). The two must
  do the same thing.
- **`output`** shows recorded text without running anything. Use it only for
  output genuinely captured elsewhere, when the command cannot run here (it
  needs a key, a network, a GPU). Tell the author which steps were pasted
  rather than recorded.
- **`max_lines`** caps long output (default 16) and adds an "… N more lines"
  marker. `"keep": "tail"` keeps the end instead, which is where test runners
  and build tools print their summary.
- **`comment`** types a `# ...` line. One at the start to set the scene is
  enough.
- **`clear`** starts a fresh screen when two scenes would not fit together.
- Each command runs in a new shell. `cd` does not carry over: set `cwd` on the
  step or chain with `&&`.
- Colours: the script asks tools for colour (`FORCE_COLOR=1`) and renders ANSI
  colours. Set `"color": false` on a step if a tool prints garbage instead.
- A non-zero exit status prints a warning. That is fine when failing is the
  point (a linter finding problems, a diff tool finding differences);
  otherwise fix the command.
- `"theme": "light"` exists. Dark reads well on both GitHub themes, so it is
  the default.
- Real output can contain things that should not be public: the local user
  name, home directory paths, hostnames, tokens. Read the transcript for them
  and choose commands or sample data that do not print them.

Limits: it records output, not keystroke-by-keystroke interaction, so it cannot
show a full-screen TUI, a prompt that waits for input, or a progress bar
redrawing. Use Route B for those.

## 3. Checking what you recorded

The script prints the transcript it captured. That text is exactly what the
SVG shows, so reading it is the first check: right commands, right output,
nothing cut off that mattered, nothing private.

To see it rendered:

- **Final frame.** Any SVG rasterizer shows the last frame with the whole
  transcript on screen, which is what a viewer sees when the loop pauses:
  ```sh
  rsvg-convert assets/demo.svg -o /tmp/demo.png        # or
  ffmpeg -y -loglevel error -i assets/demo.svg -frames:v 1 -update 1 /tmp/demo.png
  ```
- **A moment in the middle.** `--frame SECONDS` writes a still with the
  animation frozen at that time. Open or screenshot it with a browser:
  ```sh
  python3 scripts/term_demo.py --spec assets/demo.json -o /tmp/frame.svg --frame 4 --quiet
  chrome --headless=new --screenshot=/tmp/frame.png --window-size=760,480 file:///tmp/frame.svg
  ```
  Do not use Chrome's `--virtual-time-budget` on the animated file: with a
  looping animation it hangs or captures the empty first frame.

Recording again re-runs the commands. To re-render without running anything
(a different theme, a still), pass `--dump recorded.json` once and use that
file as the spec afterwards.

## 4. Route B: GIF or MP4 with VHS

Use [VHS](https://github.com/charmbracelet/vhs) when the demo must be a GIF or
MP4: for interactive programs, and for places that do not accept SVG, such as
a post on X or Product Hunt. A Reddit text post links to the repository, where
the SVG plays, so Reddit alone is not a reason to make a GIF. Write a `.tape`
file only when a GIF or MP4 is really going to be used.

Copy `assets/demo.tape`, edit the commands, then:

```sh
vhs demo.tape        # writes the file named on the Output line
```

VHS needs `ttyd` and `ffmpeg`. If it is not installed, still write the `.tape`
file, embed the Route A SVG in the README for now, and list "run `vhs
demo.tape`" under the steps the author must do. Do not install system packages
without being asked.

asciinema with `agg` is an equivalent path when it is already installed.

Keep GIFs to a few megabytes. They load on every page view.

## 5. Route C: projects with a UI

A web app, desktop app or browser extension needs a picture of the real
interface.

- Start the app and take a real screenshot with whatever browser automation is
  available (Playwright, or `chrome --headless=new --screenshot=out.png
  --window-size=1280,800 URL`).
- Show a state with realistic data, not an empty page.
- For motion, ask the author for a short screen recording. They can drag it
  into the README editor on GitHub, which hosts it.
- Never draw a mock-up and present it as the product. If nothing can be
  captured, leave the slot empty and say what is needed.

## 6. Projects with nothing to run

Specifications, datasets, curated lists and documentation sites have no demo.
A diagram or a sample of the content can take the slot. If nothing fits, leave
it out and note that the audit's demo checks do not apply to this repository.

## 7. Embedding it

```markdown
<p align="center">
  <img src="assets/demo.svg" alt="mytool scanning a folder of photos and listing the three files over 1 MB" width="720">
</p>
```

- Use a relative path so the image works on forks and branches.
- Write alt text that says what happens in the recording.
- Set a width so it does not stretch across wide screens.
- Place it directly under the pitch, above the install section.

Package registry pages and some Markdown viewers show an animated SVG as a
still image. `term_demo.py` handles that: the still image is the final frame
with the whole transcript visible.

Registries that render the README from the package (PyPI, when the manifest
says `readme = "README.md"`) do not resolve relative image paths, so the demo
shows there as a broken image. If the project is going to be published that
way, tell the author: once the repository is public, the image can point at
its absolute `raw.githubusercontent.com` URL instead.

## 8. Keeping it honest

- Record; do not compose. Never type output by hand or tidy up numbers.
- Typing is animated, but output is whatever the command printed.
- If the demo depends on setup (sample files, a build step), keep that setup
  in the repository so anyone can reproduce the recording.
- If the tool printed a warning or an ugly line, either fix the tool or leave
  it in. Editing it out of the picture is how readers get surprised later.
