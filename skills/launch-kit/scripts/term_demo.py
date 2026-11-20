#!/usr/bin/env python3
"""term_demo.py: record real commands into an animated terminal SVG.

Standard library only: no VHS, asciinema, ffmpeg or browser needed. The SVG
plays in a GitHub README when embedded as an image, loops forever, and falls
back to a readable final frame wherever animation is off.

Quick use (each command is really run, and its real output is recorded):

    python3 term_demo.py --cmd "mytool --version" --cmd "mytool scan ." -o assets/demo.svg

Full control with a JSON spec:

    python3 term_demo.py --spec demo.json -o assets/demo.svg

    {
      "title": "mytool",
      "cols": 80, "theme": "dark", "prompt": "$ ", "cwd": ".",
      "steps": [
        {"comment": "Scan a project"},
        {"cmd": "mytool scan .", "max_lines": 12},
        {"cmd": "npx mytool fix", "exec": "node ./bin/cli.js fix"},
        {"pause": 1.5},
        {"clear": true},
        {"cmd": "mytool report", "keep": "tail"}
      ]
    }

Leave "rows" out and the window fits what was recorded (up to 26 rows). Set it
to force a height; anything taller scrolls, and the script says so.

Step fields:
  cmd        text typed at the prompt; it is executed unless "output" is given
  exec       run this instead of cmd (same behaviour, different spelling, e.g.
             a local path standing in for a package that is not published yet)
  output     recorded output to show instead of running anything
  max_lines  cap on output lines for this step (default 16)
  keep       "head" (default) or "tail": which end survives the cap
  cwd, env, timeout, color   per-step overrides
  comment    a "# ..." line typed at the prompt
  pause      extra seconds to wait
  clear      clear the screen

Every command runs in a fresh shell, so `cd` does not carry over: set "cwd"
or chain with `&&`.

To look at the result without a browser tab: any SVG rasterizer shows the final
frame (rsvg-convert, ffmpeg, a Chrome screenshot). To inspect a moment in the
middle, add --frame SECONDS and screenshot that file in a browser.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata

THEMES = {
    "dark": {
        "bg": "#0d1117", "bar": "#161b22", "border": "#30363d", "fg": "#e6edf3", "dim": "#8b949e",
        "prompt": "#3fb950", "title": "#8b949e",
        "ansi": ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#b1bac4",
                 "#6e7681", "#ffa198", "#56d364", "#e3b341", "#79c0ff", "#d2a8ff", "#56d4dd", "#ffffff"],
    },
    "light": {
        "bg": "#ffffff", "bar": "#f6f8fa", "border": "#d0d7de", "fg": "#1f2328", "dim": "#656d76",
        "prompt": "#1a7f37", "title": "#656d76",
        "ansi": ["#24292f", "#cf222e", "#116329", "#9a6700", "#0969da", "#8250df", "#1b7c83", "#6e7781",
                 "#57606a", "#a40e26", "#1a7f37", "#7d4e00", "#218bff", "#a475f9", "#3192aa", "#8c959f"],
    },
}
FONT = 'ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'
FONT_SIZE = 14
CW = 8.4            # width of one cell at 14px (0.6em); textLength pins it for every font
LH = 20             # line height
PAD = 16
BAR = 34

TYPE_SPEED = 0.05   # seconds per typed cell
TYPE_MAX = 2.4      # a long command never takes longer than this to type
ENTER_PAUSE = 0.35  # between the last keystroke and the first line of output
LINE_STAGGER = 0.05 # output lines arrive one after another
OUTPUT_MAX = 0.9    # ...but a long output never takes longer than this
AFTER_STEP = 0.9    # breathing room after each command
START = 0.6
HOLD = 3.0          # how long the final frame stays before the loop restarts
AUTO_ROWS_MAX = 26  # when "rows" is not given, the window grows to fit, up to this

SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")
OTHER_ESC_RE = re.compile(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b\[[0-9;?]*[ -/]*[@-ln-~]|\x1b[@-Z\\^_=>]")
BAD_XML_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff￾￿]")


def cell_width(ch):
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def text_width(s):
    return sum(cell_width(c) for c in s)


def xml(s):
    return BAD_XML_RE.sub("", s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def color_256(n, palette):
    if n < 16:
        return palette[n]
    if n < 232:
        n -= 16
        r, g, b = n // 36, (n // 6) % 6, n % 6
        conv = lambda v: 0 if v == 0 else 55 + 40 * v
        return "#%02x%02x%02x" % (conv(r), conv(g), conv(b))
    v = 8 + 10 * (n - 232)
    return "#%02x%02x%02x" % (v, v, v)


def parse_ansi(line, theme, state):
    """Split one line into (text, color, bold) runs. `state` carries colour across lines."""
    runs = []
    pos = 0
    line = OTHER_ESC_RE.sub("", line)
    for m in SGR_RE.finditer(line):
        if m.start() > pos:
            runs.append((line[pos:m.start()], state["fg"], state["bold"]))
        pos = m.end()
        codes = [int(c) if c else 0 for c in m.group(1).split(";")] if m.group(1) else [0]
        i = 0
        while i < len(codes):
            c = codes[i]
            if c == 0:
                state["fg"], state["bold"] = None, False
            elif c == 1:
                state["bold"] = True
            elif c == 2:
                state["fg"] = theme["dim"]
            elif c == 22:
                state["bold"] = False
            elif 30 <= c <= 37:
                state["fg"] = theme["ansi"][c - 30]
            elif 90 <= c <= 97:
                state["fg"] = theme["ansi"][c - 90 + 8]
            elif c == 39:
                state["fg"] = None
            elif c in (38, 48) and i + 1 < len(codes):
                colour = None
                if codes[i + 1] == 5 and i + 2 < len(codes):
                    colour = color_256(max(0, min(255, codes[i + 2])), theme["ansi"])
                    i += 2
                elif codes[i + 1] == 2 and i + 4 < len(codes):
                    colour = "#%02x%02x%02x" % tuple(max(0, min(255, v)) for v in codes[i + 2:i + 5])
                    i += 4
                if c == 38 and colour:
                    state["fg"] = colour
            i += 1
    if pos < len(line):
        runs.append((line[pos:], state["fg"], state["bold"]))
    return runs


def layout(runs, cols):
    """Expand tabs, drop control characters and hard-wrap runs into rows of at most `cols` cells."""
    rows, cur, col = [], [], 0
    for text, colour, bold in runs:
        buf = ""
        for ch in text:
            if ch == "\t":
                ch = " " * (8 - col % 8)
            elif ord(ch) < 32 or ord(ch) == 127:
                continue
            w = text_width(ch)
            if col + w > cols:
                if buf:
                    cur.append((buf, colour, bold))
                rows.append(cur)
                cur, col, buf = [], 0, ""
            buf += ch
            col += w
        if buf:
            cur.append((buf, colour, bold))
    rows.append(cur)
    return rows


def output_rows(raw, cols, theme, max_lines, keep):
    raw = raw.replace("\r\n", "\n")
    lines = [l.split("\r")[-1] if "\r" in l else l for l in raw.split("\n")]
    state = {"fg": None, "bold": False}
    rows = []
    for l in lines:
        rows.extend(layout(parse_ansi(l, theme, state), cols))
    blank = lambda r: not "".join(t for t, _, _ in r).strip()
    while rows and blank(rows[-1]):
        rows.pop()
    while rows and blank(rows[0]):
        rows.pop(0)
    if max_lines and len(rows) > max_lines:
        cut = len(rows) - (max_lines - 1)
        marker = [("… %d more line%s" % (cut, "" if cut == 1 else "s"), theme["dim"], False)]
        rows = [marker] + rows[cut:] if keep == "tail" else rows[:max_lines - 1] + [marker]
    return rows


def execute(command, cwd, env_extra, timeout, color, cols, rows):
    env = os.environ.copy()
    env.update({"TERM": "xterm-256color", "COLUMNS": str(cols), "LINES": str(rows)})
    if color:
        env.pop("NO_COLOR", None)
        env.update({"FORCE_COLOR": "1", "CLICOLOR_FORCE": "1", "PY_COLORS": "1"})
    env.update({k: str(v) for k, v in (env_extra or {}).items()})
    try:
        p = subprocess.run(command, shell=True, cwd=cwd, env=env, timeout=timeout,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except subprocess.TimeoutExpired:
        sys.exit("term_demo.py: timed out after %ss: %s" % (timeout, command))
    return p.stdout.decode("utf-8", errors="replace"), p.returncode


class Line:
    __slots__ = ("row", "runs", "show", "hide", "typing", "cursor", "final")

    def __init__(self, row, runs, show):
        self.row, self.runs, self.show = row, runs, show
        self.hide = None      # time the line disappears (a later `clear`), or None
        self.typing = None    # (t0, t1, first_cell, cells): the typed part of the row
        self.cursor = None    # (t0, t1): when the block cursor sits on this row
        self.final = False


def build(spec, base_cwd):
    theme = THEMES.get(spec.get("theme", "dark"), THEMES["dark"])
    cols = int(spec.get("cols", 80))
    rows = int(spec.get("rows") or 10 ** 6)     # no "rows": measure first, main() fits the window
    prompt = spec.get("prompt", "$ ")
    spec_cwd = os.path.join(base_cwd, spec.get("cwd", "."))
    lines, scroll, transcript, resolved = [], [], [], []
    t, row, screen_start, tallest = START, 0, 0, 0

    def place(n_rows, at):
        nonlocal row, tallest
        first = row
        row += n_rows
        tallest = max(tallest, row)
        if row > rows:
            scroll.append((at, row - rows))
        return first

    def typed(text, colour, at):
        """A prompt line typed character by character. Returns the time typing ends."""
        wrapped = layout([(prompt, theme["prompt"], False), (text, colour, False)], cols)
        cells = max(1, text_width(text))
        speed = min(TYPE_SPEED, TYPE_MAX / cells)
        now = at
        for j, runs in enumerate(wrapped):
            first_cell = text_width(prompt) if j == 0 else 0
            n = sum(text_width(s) for s, _, _ in runs) - first_cell
            ln = Line(place(1, now), runs, now)
            end = now + max(n, 0) * speed
            ln.typing = (now, end, first_cell, max(n, 0))
            ln.cursor = (now, end if j < len(wrapped) - 1 else end + ENTER_PAUSE)
            lines.append(ln)
            now = end
        return now

    for step in spec.get("steps", []):
        if "pause" in step:
            t += float(step["pause"])
            resolved.append(step)
        elif step.get("clear"):
            for ln in lines[screen_start:]:
                ln.hide = t
            screen_start, row = len(lines), 0
            scroll.append((t, 0))
            t += 0.3
            resolved.append(step)
        elif "comment" in step:
            text = "# " + step["comment"]
            t = typed(text, theme["dim"], t) + AFTER_STEP * 0.7
            transcript.append(prompt + text)
            resolved.append(step)
        elif "cmd" in step:
            cmd = step["cmd"]
            code = None
            if "output" in step:
                raw = step["output"]
            else:
                raw, code = execute(step.get("exec", cmd), os.path.join(spec_cwd, step.get("cwd", ".")),
                                    step.get("env"), float(step.get("timeout", spec.get("timeout", 60))),
                                    step.get("color", spec.get("color", True)), cols, rows)
                if code != 0:
                    sys.stderr.write("term_demo.py: warning: exit status %d from: %s\n" % (code, step.get("exec", cmd)))
            t = typed(cmd, None, t) + ENTER_PAUSE
            out = output_rows(raw, cols, theme, int(step.get("max_lines", spec.get("max_lines", 16))), step.get("keep", "head"))
            gap = min(LINE_STAGGER, OUTPUT_MAX / len(out)) if out else 0
            for runs in out:
                lines.append(Line(place(1, t), runs, t))
                t += gap
            t += AFTER_STEP
            transcript.append(prompt + cmd)
            transcript.extend("".join(s for s, _, _ in runs) for runs in out)
            done = {k: v for k, v in step.items() if k != "output"}
            done["output"] = raw
            if code is not None:
                done["exit_status"] = code
            resolved.append(done)
        else:
            sys.exit("term_demo.py: step needs one of cmd, comment, pause, clear: %s" % json.dumps(step))

    last = Line(place(1, t), [(prompt, theme["prompt"], False)], t)
    last.cursor = (t, None)
    last.final = True
    lines.append(last)
    total = t + float(spec.get("hold", HOLD))
    final_screen = lines[screen_start:]
    out_spec = dict(spec)
    out_spec["steps"] = resolved
    return {
        "theme": theme, "cols": cols, "rows": rows, "tallest": tallest, "prompt": prompt, "lines": lines, "scroll": scroll,
        "total": total, "final_screen": set(id(l) for l in final_screen), "transcript": transcript,
        "title": spec.get("title", ""), "loop": spec.get("loop", True), "resolved": out_spec,
    }


def render(model):
    th, cols, rows, total = model["theme"], model["cols"], model["rows"], model["total"]
    width = round(PAD * 2 + cols * CW)
    height = BAR + PAD + rows * LH + PAD
    loop = "infinite" if model["loop"] else "1 forwards"
    pct = lambda t: "%.3f%%" % max(0.0, min(100.0, 100.0 * t / total))
    css, body, keyframes = [], [], {}

    def anim(kind, frames, timing="step-end"):
        """Register a keyframes rule once and return its class name."""
        key = (kind, frames, timing)
        if key not in keyframes:
            name = "%s%d" % (kind, len(keyframes))
            keyframes[key] = name
            css.append("@keyframes %s{%s}.%s{animation:%s %.2fs %s %s}" % (name, frames, name, name, total, timing, loop))
        return keyframes[key]

    final_scroll = 0
    for ln in model["lines"]:
        y = BAR + PAD + ln.row * LH
        on_final = id(ln) in model["final_screen"]
        if ln.hide is None:
            vis = anim("v", "0%%{opacity:0}%s{opacity:1}100%%{opacity:1}" % pct(ln.show))
        else:
            vis = anim("v", "0%%{opacity:0}%s{opacity:1}%s{opacity:0}100%%{opacity:0}" % (pct(ln.show), pct(ln.hide)))
        parts = []
        plain = "".join(s for s, _, _ in ln.runs)
        indent = len(plain) - len(plain.lstrip(" "))
        if plain.strip():
            # Leading spaces become an x offset, so they survive every renderer.
            text, left = "", indent
            for s, colour, bold in ln.runs:
                if left:
                    cut = min(left, len(s) - len(s.lstrip(" ")))
                    s, left = s[cut:], left - cut
                if not s:
                    continue
                attrs = (' fill="%s"' % colour if colour else "") + (' font-weight="700"' if bold else "")
                text += "<tspan%s>%s</tspan>" % (attrs, xml(s)) if attrs else xml(s)
            cells = text_width(plain.rstrip()) - indent
            tl = ' textLength="%.1f"' % (cells * CW) if cells > 1 else ""
            parts.append('<text class="t" x="%.1f" y="%d"%s xml:space="preserve">%s</text>'
                         % (PAD + indent * CW, y + 14, tl, text))
        if ln.typing:
            t0, t1, first_cell, n = ln.typing
            x0 = PAD + first_cell * CW
            shift = n * CW
            inner = ""
            if n:
                # a background-coloured cover that slides right one cell per keystroke
                inner += '<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s"/>' % (x0, y, width - PAD + 4 - x0, LH, th["bg"])
            c0, c1 = ln.cursor
            cur = anim("c", "0%%{opacity:0}%s{opacity:.75}%s{opacity:0}100%%{opacity:0}" % (pct(c0), pct(c1)))
            inner += '<rect class="%s" x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" opacity="0"/>' % (cur, x0, y + 2, CW, LH - 4, th["fg"])
            if n:
                slide = anim("k", "0%%,%s{transform:translateX(0);animation-timing-function:steps(%d,end)}%s,100%%{transform:translateX(%.1fpx)}"
                             % (pct(t0), n, pct(t1), shift), "linear")
                parts.append('<g class="%s" transform="translate(%.1f,0)">%s</g>' % (slide, shift, inner))
            else:
                parts.append(inner)
        elif ln.final:
            x0 = PAD + text_width(model["prompt"]) * CW
            parts.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" fill="%s" opacity=".75"/>' % (x0, y + 2, CW, LH - 4, th["fg"]))
        hidden = "" if on_final else ' opacity="0"'
        body.append('<g class="%s"%s>%s</g>' % (vis, hidden, "".join(parts)))

    scroll_attr = ""
    if any(off for _, off in model["scroll"]):
        frames = "0%{transform:translateY(0)}"
        for at, off in model["scroll"]:
            frames += "%s{transform:translateY(%dpx)}" % (pct(at), -off * LH)
            final_scroll = off
        frames += "100%%{transform:translateY(%dpx)}" % (-final_scroll * LH)
        scroll_attr = ' class="%s" transform="translate(0,%d)"' % (anim("s", frames), -final_scroll * LH)

    label = "Terminal demo" + (": " + model["title"] if model["title"] else "")
    desc = " | ".join(l for l in model["transcript"] if l.startswith(model["prompt"]))
    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">'
               % (width, height, width, height, xml(label)))
    out.append("<title>%s</title><desc>%s</desc>" % (xml(label), xml(desc)))
    out.append("<style>.t{font-family:%s;font-size:%dpx;fill:%s;white-space:pre}%s"
               "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>"
               % (FONT, FONT_SIZE, th["fg"], "".join(css)))
    out.append('<rect x=".5" y=".5" width="%d" height="%d" rx="10" fill="%s" stroke="%s"/>' % (width - 1, height - 1, th["bg"], th["border"]))
    out.append('<path d="M.5 %d V10.5 a10 10 0 0 1 10 -10 H%.1f a10 10 0 0 1 10 10 V%d z" fill="%s" stroke="%s"/>'
               % (BAR, width - 10.5, BAR, th["bar"], th["border"]))
    for i, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append('<circle cx="%d" cy="%d" r="6" fill="%s"/>' % (20 + i * 20, BAR // 2, colour))
    if model["title"]:
        out.append('<text x="%d" y="%d" text-anchor="middle" font-family="%s" font-size="13" fill="%s">%s</text>'
                   % (width // 2, BAR // 2 + 4, xml(FONT), th["title"], xml(model["title"])))
    out.append('<clipPath id="view"><rect x="1" y="%d" width="%d" height="%d"/></clipPath>' % (BAR + PAD - 2, width - 2, rows * LH + 4))
    out.append('<g clip-path="url(#view)"><g%s>' % scroll_attr)
    out.extend(body)
    out.append("</g></g></svg>")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Record real commands into an animated terminal SVG (no dependencies).")
    ap.add_argument("--spec", help="JSON spec file (see the top of this script for the format)")
    ap.add_argument("--cmd", action="append", default=[], help="a command to run and record; repeat for several")
    ap.add_argument("-o", "--output", default="demo.svg")
    ap.add_argument("--cwd", default=None, help="directory the commands run in (default: the spec's folder, or .)")
    ap.add_argument("--title", default=None)
    ap.add_argument("--cols", type=int, default=None)
    ap.add_argument("--rows", type=int, default=None)
    ap.add_argument("--theme", choices=sorted(THEMES), default=None)
    ap.add_argument("--max-lines", type=int, default=None, help="cap on output lines per command (default 16)")
    ap.add_argument("--dump", metavar="FILE", help="also write the spec with the recorded output filled in; "
                                                   "re-rendering from it runs nothing")
    ap.add_argument("--frame", type=float, metavar="SECONDS",
                    help="write a still: the animation frozen at this time, for checking a moment in a browser")
    ap.add_argument("--quiet", action="store_true", help="do not print the recorded transcript")
    args = ap.parse_args()

    if args.spec:
        with open(args.spec, encoding="utf-8") as fh:
            spec = json.load(fh)
        base = os.path.dirname(os.path.abspath(args.spec))
    else:
        spec, base = {"steps": []}, os.getcwd()
    spec["steps"] = list(spec.get("steps", [])) + [{"cmd": c} for c in args.cmd]
    if not spec["steps"]:
        ap.error("nothing to record: pass --cmd or --spec")
    for key in ("title", "cols", "rows", "theme"):
        if getattr(args, key) is not None:
            spec[key] = getattr(args, key)
    if args.max_lines is not None:
        spec["max_lines"] = args.max_lines
    if args.cwd:
        base, spec["cwd"] = os.path.abspath(args.cwd), "."

    model = build(spec, base)
    need = model["tallest"]
    if not spec.get("rows"):
        # Fit the window to what was recorded. The second pass reuses the captured output, so nothing runs twice.
        fitted = dict(model["resolved"])
        fitted["rows"] = max(6, min(need, AUTO_ROWS_MAX))
        fitted["cwd"] = spec.get("cwd", ".")
        resolved = model["resolved"]
        model = build(fitted, base)
        model["resolved"] = resolved
    if need > model["rows"]:
        sys.stderr.write("term_demo.py: note: the recording is %d rows tall and the window is %d, so the first %d row(s) "
                         "scroll away before the final frame. Raise \"rows\", lower \"max_lines\", or split it with "
                         "a \"clear\" step.\n" % (need, model["rows"], need - model["rows"]))
    svg = render(model)
    if args.frame is not None:
        # A negative delay on a paused animation shows the frame at that time.
        svg = svg.replace("</style>", "*{animation-delay:-%.2fs!important;animation-play-state:paused!important}</style>"
                          % max(0.0, min(args.frame, model["total"] - 0.01)), 1)
    out_dir = os.path.dirname(os.path.abspath(args.output))
    os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(svg)
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            json.dump(model["resolved"], fh, indent=2)
            fh.write("\n")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if not args.quiet:
        print("\n".join(model["transcript"]))
        print("")
    size = len(svg.encode("utf-8"))
    if args.frame is not None:
        print("wrote %s  (still frame at %.1fs of %.1fs; not for the README)" % (args.output, args.frame, model["total"]))
    else:
        print("wrote %s  (%.1fs loop, %d lines, %.1f KB)" % (args.output, model["total"], len(model["lines"]), size / 1024.0))
    if size > 600 * 1024:
        print("warning: the SVG is large; lower max_lines or record fewer commands", file=sys.stderr)


if __name__ == "__main__":
    main()
