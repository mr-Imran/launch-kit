#!/usr/bin/env python3
"""launch-kit audit: score how launch-ready a repository is (0-100).

Standard library only. Reads the local working tree, and asks GitHub about
description, topics and social preview when the `gh` CLI is available.

    python3 audit.py [REPO_DIR] [--summary] [--json] [--no-remote] [--min N]

The score is a checklist of things that are known to matter on a repository
page. It measures how well the repository presents itself. It does not predict
stars.
"""

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote

SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target", ".venv", "venv",
    "__pycache__", ".next", ".nuxt", ".cache", "coverage", ".tox", ".idea", ".vscode",
}
FOLD_LINES = 40        # how far down "the top of the README" reaches
INSTALL_LINES = 60     # an install command should appear at least this early
BADGE_RE = re.compile(
    r"shields\.io|badgen\.net|badge|codecov\.io|coveralls\.io|travis-ci|circleci\.com|"
    r"appveyor|snyk\.io|sonarcloud|gitter\.im|star-history|visitor|hits\.", re.I)
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
MD_LINK_RE = re.compile(r"(?<!\!)\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_SRC_RE = re.compile(r"<(img|video|source)\b[^>]*?\bsrc\s*=\s*[\"']([^\"']+)[\"'][^>]*>", re.I)
HTML_HREF_RE = re.compile(r"<a\b[^>]*?\bhref\s*=\s*[\"']([^\"']+)[\"']", re.I)
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
VIDEO_URL_RE = re.compile(
    r"https://(?:github\.com/user-attachments/assets/\S+|user-images\.githubusercontent\.com/\S+\.(?:mp4|mov|webm))", re.I)
INSTALL_RE = re.compile(
    r"\b(npm (i|install|create|init)\b|npx |pnpm (add|i|install|dlx|create)\b|yarn (add|global|create|dlx)\b|"
    r"bun (add|install|x|create)\b|bunx |deno (install|add|run)\b|pip3? install\b|pipx (install|run)\b|"
    r"uv (add|pip|tool|run)\b|uvx |poetry add\b|conda install\b|cargo (install|add|binstall)\b|"
    r"go (install|get|run)\b|brew (install|tap)\b|docker (run|pull|compose)\b|gem install\b|"
    r"composer (require|create-project)\b|dotnet (add|tool install)\b|apt(-get)? install\b|"
    r"winget install\b|scoop install\b|choco install\b|nix(-env| run| profile| shell)\b|"
    r"git clone\b|curl [^\n]*\|\s*(ba|z)?sh|claude plugin\b|/plugin\b|make install\b|"
    r"flutter pub add\b|dart pub\b|mix (deps|archive)\b|helm (install|repo)\b|kubectl apply\b)", re.I)
SHELL_LANG_RE = re.compile(r"^(sh|bash|zsh|fish|shell|console|terminal|shellsession|shell-session|powershell|pwsh|ps1|cmd|bat)\b", re.I)
USAGE_HEADING_RE = re.compile(r"usage|example|quick\s?-?start|getting started|how (it works|to use)|tutorial|demo", re.I)
WHY_HEADING_RE = re.compile(
    r"\bwhy\b|features?|what (it|you|is|does)|how it works|highlights|comparison|\bvs\.?\b|motivation|"
    r"benefits|use cases?|what's inside|overview", re.I)
# Template leftovers in prose. (TODO inside a code block is just code.)
PLACEHOLDER_RE = re.compile(
    r"lorem ipsum|project title|description goes here|a short description of|insert .{0,40} here|"
    r"\bTODO\b|\bFIXME\b|\bTBD\b", re.I)
# Unfilled names. These hide in install commands, so code blocks are searched too.
NAME_GAP_RE = re.compile(
    r"\bOWNER/REPO\b|\bOWNER/[\w.-]+|"
    r"github\.com/(?:(?:[a-z]+[-_])?owner|user(?:name)?|your(?:[-_]\w+|username|name|handle|org)|"
    r"<[^>/]+>|\{[^}/]+\}|\[[^\]/]+\])(?=/|\s|$)|"
    r"your[-_ ]?user[-_ ]?name|your[-_](?:org|handle)\b|<your[- _][^>]*>|example\.com/your|\[\[author:", re.I)
WEAK_OPENER_RE = re.compile(
    r"^(welcome to\b|this (is|project|repo|repository|package|library|tool|app)\b|"
    r"a (simple|basic|small) (project|repo|repository|app|tool|script)\b)", re.I)
# A License heading, "licensed under ...", or a licence named next to the word. "No license yet" does not count.
LICENSE_MENTION_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*licen[sc]e\b|<h[1-6][^>]*>\s*licen[sc]e|licen[sc]ed under|"
    r"\b(MIT|Apache|BSD|GPL|LGPL|AGPL|MPL|ISC|Unlicense|CC0|CC[ -]BY|EUPL|Zlib)\b[\w .,()-]{0,24}licen[sc]e|"
    r"licen[sc]e[\w .:,()-]{0,24}\b(MIT|Apache|BSD|GPL|LGPL|AGPL|MPL|ISC|Unlicense|CC0|EUPL|Zlib)\b", re.I | re.M)
SECRET_PATTERNS = [
    ".env", ".env.local", ".env.production", ".env.development", ".env.prod", ".env.dev",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "*.pem", "*.p12", "*.pfx", "*.keystore",
    "credentials.json", "secrets.json", "secret.json", "service-account*.json", ".netrc",
]
FIX_GROUPS = [
    ("Secret files in the repository", ("repo.secrets",)),
    ("README", ("readme.exists",)),
    ("One-line pitch", ("readme.pitch",)),
    ("Demo", ("readme.visual", "launch.demo")),
    ("Install command and usage example", ("readme.install", "readme.usage")),
    ("License", ("repo.license", "readme.license")),
    ("README body", ("readme.substance", "readme.why", "readme.h1")),
    ("README clean-up", ("readme.placeholders", "readme.links")),
    ("Description, topics and package metadata", ("gh.description", "gh.topics", "gh.homepage", "repo.manifest")),
    ("Social preview image", ("gh.social", "launch.social")),
    ("Launch post notes and drafts", ("launch.posts",)),
    ("Housekeeping", ("repo.gitignore", "repo.contributing", "repo.release")),
]
DEMO_NAME_RE = re.compile(r"demo|screenshot|screencast|screen[-_]?shot|preview|showcase|hero|usage|example|recording", re.I)
DEMO_EXTS = (".gif", ".mp4", ".webm", ".mov", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".apng", ".tape", ".cast")
SOCIAL_NAME_RE = re.compile(r"social[-_ ]?(preview|card|image)|og[-_ ]?image|open[-_ ]?graph|^og\.|^social\.", re.I)


# --------------------------------------------------------------------------- helpers

def run(cmd, cwd, timeout=20):
    """Run a command, return (ok, stdout). Never raises."""
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, text=True, encoding="utf-8", errors="replace")
        return p.returncode == 0, p.stdout
    except Exception:
        return False, ""


def walk(repo, max_depth=3):
    """Yield repo-relative paths (posix style) down to max_depth."""
    root_depth = repo.rstrip(os.sep).count(os.sep)
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if base.count(os.sep) - root_depth >= max_depth:
            dirs[:] = []
        for name in files:
            yield os.path.relpath(os.path.join(base, name), repo).replace(os.sep, "/")


def find_readme(repo):
    """GitHub shows .github/, then root, then docs/. Root is by far the common case."""
    for sub in (".github", "", "docs"):
        folder = os.path.join(repo, sub)
        if not os.path.isdir(folder):
            continue
        names = sorted(os.listdir(folder))
        for want in ("readme.md", "readme.markdown", "readme.mdx", "readme.rst", "readme.txt", "readme"):
            for name in names:
                if name.lower() == want and os.path.isfile(os.path.join(folder, name)):
                    return os.path.join(folder, name)
    return None


def strip_markup(text):
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = MD_IMAGE_RE.sub(" ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links -> their text
    text = re.sub(r"<[^>]+>", " ", text)                       # html tags
    text = re.sub(r"[`*_~>#|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class Readme:
    """A light, line-based view of a Markdown README (good enough for a checklist)."""

    def __init__(self, path):
        self.path = path
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        # Blank out HTML comments but keep the line count stable.
        self.text = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), raw, flags=re.S)
        self.lines = self.text.splitlines()
        self.in_code = []
        self.fences = 0
        self.shell_fences = []          # line numbers of ```sh / ```bash / ... blocks
        fence = None
        for n, line in enumerate(self.lines):
            s = line.lstrip()
            marker = s[:3] if s[:3] in ("```", "~~~") else None
            if fence is None and marker:
                fence = marker
                self.fences += 1
                if SHELL_LANG_RE.match(s[3:].strip()):
                    self.shell_fences.append(n)
                self.in_code.append(True)
            elif fence is not None and marker == fence:
                fence = None
                self.in_code.append(True)
            else:
                self.in_code.append(fence is not None)
        self.prose_lines = [(i, l) for i, l in enumerate(self.lines) if not self.in_code[i]]
        self.prose = "\n".join(l for _, l in self.prose_lines)

    def headings(self, level):
        out = []
        prefix = "#" * level + " "
        for i, line in self.prose_lines:
            if line.startswith(prefix):
                out.append((i, line[level + 1:].strip().strip("#").strip()))
        for m in re.finditer(r"<h%d\b[^>]*>(.*?)</h%d>" % (level, level), self.prose, re.S | re.I):
            line_no = self.prose[:m.start()].count("\n")
            out.append((self.prose_lines[line_no][0] if line_no < len(self.prose_lines) else 0,
                        strip_markup(m.group(1))))
        return sorted(out)

    def images(self):
        """(line_no, url, alt_or_None, is_badge) for every image or video outside code."""
        out = []
        for i, line in self.prose_lines:
            for m in MD_IMAGE_RE.finditer(line):
                out.append((i, m.group(2), m.group(1), bool(BADGE_RE.search(m.group(2)))))
            for m in HTML_SRC_RE.finditer(line):
                tag = m.group(0)
                alt = re.search(r"\balt\s*=\s*[\"']([^\"']*)[\"']", tag, re.I)
                is_img = m.group(1).lower() == "img"
                out.append((i, m.group(2), (alt.group(1) if alt else None) if is_img else "video",
                            bool(BADGE_RE.search(m.group(2)))))
            for m in VIDEO_URL_RE.finditer(line):
                if "](" not in line and "src=" not in line:
                    out.append((i, m.group(0), "video", False))
        return out

    def link_targets(self):
        out = []
        for i, line in self.prose_lines:
            for m in MD_IMAGE_RE.finditer(line):
                out.append((i, m.group(2)))
            for m in MD_LINK_RE.finditer(line):
                out.append((i, m.group(1)))
            for m in HTML_SRC_RE.finditer(line):
                out.append((i, m.group(2)))
            for m in HTML_HREF_RE.finditer(line):
                out.append((i, m.group(1)))
        return out


# --------------------------------------------------------------------------- checks

class Audit:
    def __init__(self, repo, use_remote=True):
        self.repo = os.path.abspath(repo)
        self.use_remote = use_remote
        self.checks = []
        self.notes = []
        self.files = list(walk(self.repo))
        self.root_files = sorted(os.listdir(self.repo))
        self.is_git = run(["git", "rev-parse", "--is-inside-work-tree"], self.repo)[0] if shutil.which("git") else False
        # A folder inside someone else's repository (an example, a package in a monorepo) must not
        # borrow that repository's remote, tags or history.
        self.is_git_root = False
        if self.is_git:
            ok, top = run(["git", "rev-parse", "--show-toplevel"], self.repo)
            self.is_git_root = ok and os.path.realpath(top.strip()) == os.path.realpath(self.repo)
        self.skip_reason = ""

    def add(self, cid, category, title, points, earned, detail="", fix="", skipped=False):
        self.checks.append({
            "id": cid, "category": category, "title": title,
            "max": points, "earned": 0 if skipped else earned,
            "status": "skip" if skipped else ("pass" if earned >= points else ("partial" if earned > 0 else "fail")),
            "detail": detail, "fix": "" if (skipped or earned >= points) else fix,
        })

    # ---- README: first impression -------------------------------------------------
    def readme_checks(self):
        cat = "First impression"
        path = find_readme(self.repo)
        if not path:
            self.add("readme.exists", cat, "README exists", 3, 0, "no README found",
                     "Create README.md. It is the whole landing page of the repository.")
            for cid, title, pts in (("readme.pitch", "One-line pitch at the top", 10),
                                    ("readme.visual", "Demo or screenshot near the top", 10),
                                    ("readme.install", "Install or run command near the top", 9),
                                    ("readme.usage", "Usage example", 6),
                                    ("readme.placeholders", "No placeholder text", 2)):
                self.add(cid, cat, title, pts, 0, "no README", "Write the README first.")
            for cid, title, pts in (("readme.substance", "Enough substance and structure", 8),
                                    ("readme.why", "Says why it exists or what is different", 7),
                                    ("readme.links", "Relative links and images resolve", 2),
                                    ("readme.license", "Mentions the license", 2),
                                    ("readme.h1", "Exactly one top-level title", 1)):
                self.add(cid, "README depth", title, pts, 0, "no README", "Write the README first.")
            return
        rel = os.path.relpath(path, self.repo).replace(os.sep, "/")
        self.add("readme.exists", cat, "README exists", 3, 3, rel)
        if not path.lower().endswith((".md", ".markdown", ".mdx")):
            self.notes.append("README is not Markdown; the README checks assume Markdown and may be off.")
        r = Readme(path)
        self.readme = r

        # One-line pitch -------------------------------------------------------
        h1 = r.headings(1)
        pitch, pitch_line = None, None
        if h1:
            m = re.search(r"\s[-–—:|]\s+(.+)$", h1[0][1])
            if m and len(m.group(1).split()) >= 4:
                pitch, pitch_line = m.group(1).strip(), h1[0][0]
        if pitch is None:
            start = h1[0][0] + 1 if h1 else 0
            for i, line in r.prose_lines:
                if i < start or i >= start + 25:
                    continue
                s = line.strip()
                if not s or s.startswith("#") or re.fullmatch(r"[-=*_ ]{3,}", s) or s.startswith("|"):
                    continue
                if re.match(r"^\s*([-*+]|\d+\.)\s", line):
                    continue          # a list item is not a pitch
                text = strip_markup(s)
                outside_links = strip_markup(re.sub(r"!?\[[^\]]*\]\([^)]*\)", " ", s))
                if len(re.findall(r"\w+", outside_links)) < 2:
                    continue          # a row of navigation links is not a pitch
                if len(re.findall(r"\w+", text)) >= 4:
                    pitch, pitch_line = text, i
                    break
        if pitch is None:
            self.add("readme.pitch", cat, "One-line pitch at the top", 10, 0, "no sentence found under the title",
                     "Put one plain sentence directly under the title: what it does and for whom. See references/readme-hook.md.")
        else:
            first = re.split(r"(?<=[.!?])\s+", pitch)[0]
            if WEAK_OPENER_RE.match(first):
                self.add("readme.pitch", cat, "One-line pitch at the top", 10, 2, 'opens with "%s..."' % first[:40],
                         "Drop the generic opener and start with what the tool does. See references/readme-hook.md.")
            elif len(first) > 160:
                self.add("readme.pitch", cat, "One-line pitch at the top", 10, 5, "first sentence is %d characters" % len(first),
                         "Lead with one sentence of about 120 characters or less; move the rest below.")
            else:
                self.add("readme.pitch", cat, "One-line pitch at the top", 10, 10, '"%s"' % (first[:90] + ("..." if len(first) > 90 else "")))

        # Visual near the top ---------------------------------------------------
        images = r.images()
        visuals = [im for im in images if not im[3]]
        early = [im for im in visuals if im[0] < FOLD_LINES]
        if early and (early[0][2] is None or not early[0][2].strip()):
            self.add("readme.visual", cat, "Demo or screenshot near the top", 10, 8,
                     "line %d: %s has no alt text" % (early[0][0] + 1, early[0][1][:60]),
                     "Add alt text that says what the image shows, for screen readers and for when it fails to load.")
        elif early:
            self.add("readme.visual", cat, "Demo or screenshot near the top", 10, 10, "line %d: %s" % (early[0][0] + 1, early[0][1][:70]))
        elif visuals:
            self.add("readme.visual", cat, "Demo or screenshot near the top", 10, 4, "first visual is on line %d" % (visuals[0][0] + 1),
                     "Move the demo above the fold (within the first %d lines)." % FOLD_LINES)
        else:
            self.add("readme.visual", cat, "Demo or screenshot near the top", 10, 0, "no image, GIF or video in the README",
                     "Record a short demo and embed it right under the pitch. See references/demo.md.")

        # Install command near the top -----------------------------------------
        install_line = None
        for i, line in enumerate(r.lines):
            if (r.in_code[i] or "`" in line) and INSTALL_RE.search(line):
                install_line = i
                break
        if r.shell_fences and (install_line is None or r.shell_fences[0] < install_line):
            install_line = min(r.shell_fences[0] + 1, len(r.lines) - 1)   # first line inside the shell block
        if install_line is not None and install_line < INSTALL_LINES:
            self.add("readme.install", cat, "Install or run command near the top", 9, 9,
                     "line %d: %s" % (install_line + 1, r.lines[install_line].strip()[:70]))
        elif install_line is not None:
            self.add("readme.install", cat, "Install or run command near the top", 9, 5, "first install command is on line %d" % (install_line + 1),
                     "Move a copy-pasteable install command into the first %d lines." % INSTALL_LINES)
        else:
            self.add("readme.install", cat, "Install or run command near the top", 9, 0, "no install or run command found in a code block",
                     "Add the exact command to install or try it, in a code block, near the top.")

        # Usage example ---------------------------------------------------------
        h2 = r.headings(2)
        h3 = r.headings(3)
        has_usage_heading = any(USAGE_HEADING_RE.search(t) for _, t in h2 + h3)
        if r.fences >= 2 or (r.fences >= 1 and has_usage_heading):
            self.add("readme.usage", cat, "Usage example", 6, 6, "%d code block(s)" % r.fences)
        elif r.fences == 1:
            self.add("readme.usage", cat, "Usage example", 6, 2, "only one code block",
                     "Show a real usage example with its output, not only the install command.")
        else:
            self.add("readme.usage", cat, "Usage example", 6, 0, "no code blocks",
                     "Show a real usage example with its output in a code block.")

        # Badges carry no points: having none is fine. A wall of them is worth a remark.
        badge_count = sum(1 for im in images if im[3] and im[0] < 15)
        if badge_count > 6:
            self.notes.append("%d badges in the first 15 lines of the README. Keep the few that carry information "
                              "(build, version, license); the rest push the pitch down." % badge_count)

        # Placeholders ----------------------------------------------------------
        hits = []
        for i, line in enumerate(r.lines):
            m = NAME_GAP_RE.search(line) or (None if r.in_code[i] else PLACEHOLDER_RE.search(line))
            if m:
                hits.append("line %d: %s" % (i + 1, m.group(0)))
        if hits:
            self.add("readme.placeholders", cat, "No placeholder text", 2, 0, "; ".join(hits[:3]),
                     "Fill in or remove these before anyone sees them. Unfilled names (OWNER, your-username) need the "
                     "author; a TODO list belongs in issues or a Roadmap section near the end.")
        else:
            self.add("readme.placeholders", cat, "No placeholder text", 2, 2)

        # ---- README depth ----------------------------------------------------
        cat = "README depth"
        words = len(strip_markup(r.prose).split())
        # A short README is fine; a README that only names the project is not.
        if words >= 80 and len(h2) >= 3:
            self.add("readme.substance", cat, "Enough substance and structure", 8, 8, "%d words, %d sections" % (words, len(h2)))
        elif words >= 40 and len(h2) >= 2:
            self.add("readme.substance", cat, "Enough substance and structure", 8, 4, "%d words, %d sections" % (words, len(h2)),
                     "Cover install, usage and how it works under their own ## headings.")
        else:
            self.add("readme.substance", cat, "Enough substance and structure", 8, 0, "%d words, %d sections" % (words, len(h2)),
                     "Cover install, usage and how it works under their own ## headings.")

        if any(WHY_HEADING_RE.search(t) for _, t in h2 + h3):
            self.add("readme.why", cat, "Says why it exists or what is different", 7, 7)
        else:
            self.add("readme.why", cat, "Says why it exists or what is different", 7, 0, "no why / features / how-it-works section",
                     "Add a short section on why this exists or how it differs from the obvious alternative.")

        broken = []
        readme_dir = os.path.dirname(path)
        for i, target in r.link_targets():
            t = target.strip()
            if not t or re.match(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", t, re.I):
                continue
            t = unquote(t.split("#")[0].split("?")[0])
            if not t:
                continue
            full = os.path.join(self.repo, t.lstrip("/")) if t.startswith("/") else os.path.join(readme_dir, t)
            if not os.path.exists(full):
                broken.append("line %d: %s" % (i + 1, target))
        if broken:
            self.add("readme.links", cat, "Relative links and images resolve", 2, 0, "; ".join(broken[:4]),
                     "Fix or remove these paths. A broken image at the top is the worst first impression.")
        else:
            self.add("readme.links", cat, "Relative links and images resolve", 2, 2)

        if LICENSE_MENTION_RE.search(r.prose):
            self.add("readme.license", cat, "Mentions the license", 2, 2)
        else:
            self.add("readme.license", cat, "Mentions the license", 2, 0, "",
                     "End the README with a one-line License section, once the author has chosen a license.")

        if len(h1) == 1:
            self.add("readme.h1", cat, "Exactly one top-level title", 1, 1)
        else:
            self.add("readme.h1", cat, "Exactly one top-level title", 1, 0, "%d top-level titles" % len(h1),
                     "Use one # title (the project name) and ## for everything else.")

    # ---- repository hygiene ----------------------------------------------------
    def repo_checks(self):
        cat = "Repository hygiene"
        lic = [f for f in self.root_files if re.match(r"^(licen[sc]e|copying|unlicense)", f, re.I)]
        if lic:
            self.add("repo.license", cat, "LICENSE file", 6, 6, lic[0])
        else:
            self.add("repo.license", cat, "LICENSE file", 6, 0, "no license file",
                     "Add a LICENSE file. Without one nobody may legally use the code. Ask the author which license; never pick silently.")

        if ".gitignore" in self.root_files:
            self.add("repo.gitignore", cat, ".gitignore", 1, 1)
        else:
            self.add("repo.gitignore", cat, ".gitignore", 1, 0, "", "Add a .gitignore for the stack.")

        tracked = None
        if self.is_git:
            ok, out = run(["git", "ls-files"], self.repo)
            if ok:
                tracked = out.splitlines()
        ignore_patterns = []
        gi = os.path.join(self.repo, ".gitignore")
        if os.path.isfile(gi):
            with open(gi, encoding="utf-8", errors="replace") as fh:
                ignore_patterns = [l.strip().strip("/") for l in fh if l.strip() and not l.startswith("#")]
        candidates = tracked if tracked is not None else self.files
        exposed = []
        for f in candidates:
            base = f.split("/")[-1]
            if any(fnmatch.fnmatch(base, p) for p in SECRET_PATTERNS):
                if tracked is None and any(fnmatch.fnmatch(base, p) or fnmatch.fnmatch(f, p) for p in ignore_patterns):
                    continue
                exposed.append(f)
        where = "tracked by git" if tracked is not None else "present and not in .gitignore"
        if exposed:
            self.add("repo.secrets", cat, "No secret files in the repository", 4, 0, "%s: %s" % (where, ", ".join(exposed[:5])),
                     "Stop here and tell the author. Remove these from git, rotate the credentials, then continue.")
        else:
            self.add("repo.secrets", cat, "No secret files in the repository", 4, 4)

        manifest = self.manifest_metadata()
        if manifest is None:
            self.add("repo.manifest", cat, "Package metadata filled in", 2, 0, "no package manifest", skipped=True)
        else:
            name, ok, detail = manifest
            if "still says OWNER" in detail and "," not in detail:
                fix = "Replace OWNER in the repository URL in %s once the handle is known." % name
            else:
                fix = "Fill in description, keywords and repository in %s; registries show them." % name
            self.add("repo.manifest", cat, "Package metadata filled in", 2, 2 if ok else 0, "%s: %s" % (name, detail), fix)

        if any(re.match(r"^(\.github/|docs/)?contributing(\.\w+)?$", f, re.I) for f in self.files):
            self.add("repo.contributing", cat, "CONTRIBUTING guide", 1, 1)
        else:
            self.add("repo.contributing", cat, "CONTRIBUTING guide", 1, 0, "",
                     "Add a short CONTRIBUTING.md: how to run it locally and how to send a change.")

        has_log = any(re.match(r"^(changelog|history|releases|news)(\.\w+)?$", f, re.I) for f in self.root_files)
        has_tag = False
        if self.is_git_root:
            ok, out = run(["git", "tag", "--list"], self.repo)
            has_tag = ok and bool(out.strip())
        if has_log or has_tag:
            self.add("repo.release", cat, "A tagged release or changelog", 1, 1)
        else:
            self.add("repo.release", cat, "A tagged release or changelog", 1, 0, "",
                     "Tag a first version (for example v0.1.0) so people can pin it.")

    def project_name(self):
        p = os.path.join(self.repo, "package.json")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    name = json.load(fh).get("name")
                if name:
                    return str(name)
            except Exception:
                pass
        for manifest in ("pyproject.toml", "Cargo.toml"):
            p = os.path.join(self.repo, manifest)
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    m = re.search(r"^\s*name\s*=\s*[\"']([^\"']+)[\"']", fh.read(), re.M)
                if m:
                    return m.group(1)
        if self.is_git_root:
            ok, out = run(["git", "remote", "get-url", "origin"], self.repo)
            m = re.search(r"[:/]([^/\s]+?)(?:\.git)?/?\s*$", out) if ok else None
            if m:
                return m.group(1)
        return os.path.basename(self.repo)

    def manifest_metadata(self):
        p = os.path.join(self.repo, "package.json")
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception:
                return ("package.json", False, "could not be parsed")
            missing = [k for k in ("description", "keywords", "repository") if not data.get(k)]
            if NAME_GAP_RE.search(json.dumps(data.get("repository") or "")):
                missing.append("a real repository url (it still says OWNER)")
            return ("package.json", not missing, "missing " + ", ".join(missing) if missing else "ok")
        for name in ("pyproject.toml", "Cargo.toml"):
            p = os.path.join(self.repo, name)
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                missing = []
                if not re.search(r"^\s*description\s*=\s*[\"'][^\"']+[\"']", text, re.M):
                    missing.append("description")
                if not re.search(r"^\s*keywords\s*=", text, re.M):
                    missing.append("keywords")
                if not re.search(r"^\s*(repository|homepage)\s*=|^\s*\[project\.urls\]", text, re.M | re.I):
                    missing.append("repository url")
                elif NAME_GAP_RE.search(text):
                    missing.append("a real repository url (it still says OWNER)")
                return (name, not missing, "missing " + ", ".join(missing) if missing else "ok")
        return None

    def commit_identity_note(self):
        """Commit authors become public on the first push. Flag the ones that are clearly stand-ins."""
        if not self.is_git_root:
            return
        ok, out = run(["git", "log", "--format=%an <%ae>", "-n", "200"], self.repo)
        if not ok:
            return
        odd = sorted(set(l for l in out.splitlines()
                         if re.search(r"@(example\.(com|org|net)|localhost|.*\.(local|invalid|test))>$|<>$|^(root|user|dev|test) <", l, re.I)))
        if odd:
            self.notes.append("Some commits are authored by %s. Author names and emails become public on the first push; "
                              "fix them first if that is not the identity you want shown." % ", ".join(odd[:3]))

    # ---- GitHub metadata -------------------------------------------------------
    def github_checks(self):
        cat = "GitHub metadata"
        items = (("gh.description", "Repository description", 5), ("gh.topics", "Topics", 5),
                 ("gh.social", "Custom social preview image", 4), ("gh.homepage", "Homepage link", 1))
        reason = None
        slug = None
        if not self.use_remote:
            reason = "remote checks turned off"
        elif not self.is_git:
            reason = "not a git repository"
        elif not self.is_git_root:
            reason = "inside another repository"
        elif not shutil.which("gh"):
            reason = "gh CLI not installed"
        else:
            ok, out = run(["git", "remote", "get-url", "origin"], self.repo)
            m = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?\s*$", out) if ok else None
            if not m:
                reason = "no GitHub remote yet"
            else:
                slug = (m.group(1), m.group(2))
        data = None
        if slug:
            query = ("query($o:String!,$n:String!){repository(owner:$o,name:$n){description homepageUrl "
                     "usesCustomOpenGraphImage isPrivate stargazerCount "
                     "repositoryTopics(first:30){nodes{topic{name}}}}}")
            ok, out = run(["gh", "api", "graphql", "-f", "query=" + query, "-f", "o=" + slug[0], "-f", "n=" + slug[1]],
                          self.repo, timeout=30)
            try:
                data = json.loads(out)["data"]["repository"] if ok else None
            except Exception:
                data = None
            if not data:
                reason = "could not read %s/%s (not pushed yet, or gh not logged in)" % slug
        if not data:
            for cid, title, pts in items:
                self.add(cid, cat, title, pts, 0, reason, skipped=True)
            self.skip_reason = reason
            return
        self.github = {"slug": "%s/%s" % slug, "stars": data.get("stargazerCount"), "private": data.get("isPrivate")}
        if data.get("isPrivate"):
            self.notes.append("The repository is private. Topics and the social preview only matter once it is public.")
        desc = (data.get("description") or "").strip()
        if desc:
            self.add("gh.description", cat, "Repository description", 5, 5, '"%s"' % desc[:80])
        else:
            self.add("gh.description", cat, "Repository description", 5, 0, "empty",
                     "Set a description: it is the text shown in search results and link previews. See references/metadata.md.")
        topics = [n["topic"]["name"] for n in (data.get("repositoryTopics") or {}).get("nodes", [])]
        if len(topics) >= 5:
            self.add("gh.topics", cat, "Topics", 5, 5, ", ".join(topics[:8]))
        elif topics:
            self.add("gh.topics", cat, "Topics", 5, 2, "only %d: %s" % (len(topics), ", ".join(topics)),
                     "Add topics until there are 5 to 10. See references/metadata.md.")
        else:
            self.add("gh.topics", cat, "Topics", 5, 0, "none",
                     "Add 5 to 10 topics; topic pages are how people browse GitHub. See references/metadata.md.")
        if data.get("usesCustomOpenGraphImage"):
            self.add("gh.social", cat, "Custom social preview image", 4, 4)
        else:
            self.add("gh.social", cat, "Custom social preview image", 4, 0, "GitHub's generated card is in use",
                     "Generate one with scripts/social_preview.py, then upload it in Settings > General > Social preview (there is no API for this).")
        if (data.get("homepageUrl") or "").strip():
            self.add("gh.homepage", cat, "Homepage link", 1, 1, data["homepageUrl"])
        else:
            self.add("gh.homepage", cat, "Homepage link", 1, 0, "empty",
                     "Point the homepage at docs, a demo or the package page, if one exists.")

    # ---- launch assets ----------------------------------------------------------
    def launch_checks(self):
        cat = "Launch assets"
        demos = [f for f in self.files
                 if f.lower().endswith(DEMO_EXTS) and DEMO_NAME_RE.search(f.split("/")[-1])
                 and not SOCIAL_NAME_RE.search(f.split("/")[-1])]
        if demos:
            self.add("launch.demo", cat, "Demo recording or screenshot in the repo", 4, 4, demos[0])
        else:
            self.add("launch.demo", cat, "Demo recording or screenshot in the repo", 4, 0, "",
                     "Record one with scripts/term_demo.py (no dependencies) or VHS. See references/demo.md.")
        social = [f for f in self.files
                  if f.lower().endswith((".png", ".jpg", ".jpeg")) and SOCIAL_NAME_RE.search(f.split("/")[-1])]
        if social:
            self.add("launch.social", cat, "Social preview image file", 2, 2, social[0])
        else:
            self.add("launch.social", cat, "Social preview image file", 2, 0, "",
                     "Generate a 1280x640 card with scripts/social_preview.py.")
        drafts = [f for f in self.files
                  if re.match(r"^(docs/)?\.?launch/[^/]+\.(md|txt)$", f, re.I)
                  and not re.match(r"^readme", f.split("/")[-1], re.I)]
        if len(drafts) >= 2:
            self.add("launch.posts", cat, "Launch post notes and drafts", 4, 4, ", ".join(drafts[:4]))
        elif drafts:
            self.add("launch.posts", cat, "Launch post notes and drafts", 4, 2, drafts[0],
                     "Draft for at least two channels. See references/launch-posts.md.")
        else:
            self.add("launch.posts", cat, "Launch post notes and drafts", 4, 0, "no launch/ folder",
                     "Prepare the announcement notes and drafts in launch/. See references/launch-posts.md.")

    # ---- result -----------------------------------------------------------------
    def result(self):
        self.readme_checks()
        self.repo_checks()
        self.commit_identity_note()
        self.github_checks()
        self.launch_checks()
        active = [c for c in self.checks if c["status"] != "skip"]
        earned = sum(c["earned"] for c in active)
        possible = sum(c["max"] for c in active)
        score = round(100.0 * earned / possible) if possible else 0
        grade = ("Launch-ready" if score >= 90 else "Nearly there" if score >= 75
                 else "Needs work" if score >= 50 else "Not ready")
        cats = []
        for name in ("First impression", "README depth", "Repository hygiene", "GitHub metadata", "Launch assets"):
            cs = [c for c in self.checks if c["category"] == name]
            live = [c for c in cs if c["status"] != "skip"]
            cats.append({"name": name, "earned": sum(c["earned"] for c in live), "max": sum(c["max"] for c in live),
                         "skipped": not live})
        # One fix often earns points in two places (a demo is 10 in the README and 4 as a file),
        # so fixes are reported by the piece of work, not by the check.
        fixes = []
        for title, ids in FIX_GROUPS:
            open_checks = [c for c in active if c["id"] in ids and c["earned"] < c["max"]]
            if open_checks:
                if title.startswith("Description, topics") and not any(c["id"].startswith("gh.") for c in open_checks):
                    title = "Package metadata"
                fixes.append({
                    "title": title, "points": sum(c["max"] - c["earned"] for c in open_checks),
                    "urgent": "repo.secrets" in ids,
                    "checks": [{"id": c["id"], "title": c["title"], "points": c["max"] - c["earned"], "fix": c["fix"]}
                               for c in sorted(open_checks, key=lambda c: c["earned"] - c["max"])],
                })
        fixes.sort(key=lambda f: (not f["urgent"], -f["points"]))
        skipped = [c for c in cats if c["skipped"]]
        return {
            "repo": self.project_name(), "path": self.repo, "score": score, "grade": grade,
            "points_earned": earned, "points_possible": possible,
            "not_checked": [c["name"] for c in skipped], "not_checked_reason": self.skip_reason,
            "not_checked_points": sum(c["max"] for c in self.checks if c["category"] in [k["name"] for k in skipped]),
            "not_applicable": [{"title": c["title"], "points": c["max"], "why": c["detail"]} for c in self.checks
                               if c["status"] == "skip" and c["category"] not in [k["name"] for k in skipped]],
            "categories": cats, "checks": self.checks, "fixes": fixes,
            "notes": self.notes, "github": getattr(self, "github", None),
        }


def render(res, color=False, summary=False):
    def paint(text, code):
        return "\x1b[%sm%s\x1b[0m" % (code, text) if color else text

    tone = "32" if res["score"] >= 75 else "33" if res["score"] >= 50 else "31"
    out = []
    out.append("launch-kit audit: %s" % paint(res["repo"], "1"))
    if not summary:
        out.append("")
    out.append("  Launch score: %s  (%s)" % (paint("%d/100" % res["score"], "1;" + tone), res["grade"]))
    if res["points_possible"] != 100:
        line = "  %d of %d points." % (res["points_earned"], res["points_possible"])
        if res["not_checked"]:
            line += " %s (%d points) not checked: %s." % (", ".join(res["not_checked"]), res["not_checked_points"],
                                                          res["not_checked_reason"] or "not available")
        for item in res["not_applicable"]:
            line += " %s (%d) does not apply: %s." % (item["title"], item["points"], item["why"])
        out.append(paint(line, "2"))
    out.append("")
    marks = {"pass": paint("\u2713", "32"), "fail": paint("\u2717", "31"), "partial": paint("~", "33"), "skip": paint("-", "2")}
    for cat in res["categories"]:
        head = "not checked" if cat["skipped"] else "%2d/%d" % (cat["earned"], cat["max"])
        if summary:
            out.append("  %-22s %s" % (cat["name"], paint(head, "2") if cat["skipped"] else head))
            continue
        out.append("%s%s %s" % (paint(cat["name"], "1"), " " * (38 - len(cat["name"])), head.strip()))
        for c in res["checks"]:
            if c["category"] != cat["name"]:
                continue
            pts = "  -  " if c["status"] == "skip" else "%2d/%-2d" % (c["earned"], c["max"])
            line = "  %s %-42s %s" % (marks[c["status"]], c["title"], pts)
            if c["detail"] and c["status"] != "pass":
                line += "  " + paint(c["detail"], "2")
            out.append(line.rstrip())
        out.append("")
    if summary:
        if res["fixes"]:
            out.append("  Next: " + ", ".join("%s %s" % (f["title"], paint("+%d" % f["points"], "32")) for f in res["fixes"][:3]))
        out.append("")
    elif res["fixes"]:
        scale = "" if res["points_possible"] == 100 else " (points are out of the %d in play)" % res["points_possible"]
        out.append(paint("What to fix, most points first%s:" % scale, "1"))
        for n, f in enumerate(res["fixes"], 1):
            out.append("  %d. %s  %s" % (n, paint("+%d" % f["points"], "32"), f["title"]))
            for c in f["checks"]:
                out.append("        %s (+%d). %s" % (c["title"], c["points"], c["fix"]))
        out.append("")
    for note in res["notes"]:
        out.append(paint("Note: %s" % note, "2"))
    return "\n".join(out).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser(description="Score how launch-ready a repository is (0-100).")
    ap.add_argument("repo", nargs="?", default=".", help="path to the repository (default: current directory)")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    ap.add_argument("--summary", action="store_true", help="print only the score and the five area totals")
    ap.add_argument("--no-remote", action="store_true", help="skip the GitHub metadata checks")
    ap.add_argument("--min", type=int, default=None, metavar="N", help="exit with status 1 when the score is below N")
    args = ap.parse_args()
    if not os.path.isdir(args.repo):
        sys.exit("audit.py: not a directory: %s" % args.repo)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    res = Audit(args.repo, use_remote=not args.no_remote).result()
    color = (sys.stdout.isatty() or bool(os.environ.get("FORCE_COLOR"))) and not os.environ.get("NO_COLOR")
    sys.stdout.write(json.dumps(res, indent=2) + "\n" if args.json else render(res, color=color, summary=args.summary))
    if args.min is not None and res["score"] < args.min:
        sys.exit(1)


if __name__ == "__main__":
    main()
