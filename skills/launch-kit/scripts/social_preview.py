#!/usr/bin/env python3
"""social_preview.py: make the 1280x640 card GitHub shows when a repo link is shared.

    python3 social_preview.py --title "mytool" \
        --tagline "Find and kill whatever is holding a port" \
        --command "npx mytool 3000" --footer "github.com/you/mytool" \
        -o assets/social-preview.png

The card is drawn as SVG (standard library only) and converted to PNG with
whichever of these is installed: rsvg-convert, resvg, inkscape, ImageMagick,
Chrome/Chromium/Edge, ffmpeg, or the cairosvg Python package. GitHub accepts
PNG, JPG or GIF under 1 MB, so if none is available the SVG is kept and the
script says how to finish the job.

GitHub has no API for the social preview: the author uploads the PNG by hand
under Settings > General > Social preview.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import textwrap

W, H = 1280, 640
MARGIN = 80
SANS = 'Inter,"Segoe UI","Helvetica Neue",Helvetica,Arial,"Liberation Sans","DejaVu Sans",sans-serif'
MONO = '"JetBrains Mono","SF Mono",Menlo,Consolas,"Liberation Mono","DejaVu Sans Mono",monospace'
THEMES = {
    "dark": {"bg": "#0d1117", "panel": "#161b22", "border": "#30363d", "title": "#ffffff",
             "text": "#c9d1d9", "dim": "#8b949e", "accent": "#58a6ff"},
    "light": {"bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "title": "#1f2328",
              "text": "#424a53", "dim": "#656d76", "accent": "#0969da"},
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def build_svg(title, tagline, command, footer, label, theme, accent):
    th = dict(THEMES[theme])
    if accent:
        th["accent"] = accent
    usable = W - 2 * MARGIN
    # Width estimates are deliberately generous: the real font is whatever the
    # converting machine has, so text must fit even in a wide one.
    title_size = int(max(52, min(108, usable / (0.60 * max(len(title), 1)))))
    tag_size = 42
    tag_lines = textwrap.wrap(tagline, width=int(usable / (0.52 * tag_size)))[:3] if tagline else []
    cmd_size = 30
    if command and len(command) * 0.61 * cmd_size > usable - 90:
        cmd_size = int(max(20, (usable - 90) / (0.61 * len(command))))

    block = title_size + (24 + len(tag_lines) * tag_size * 1.3 if tag_lines else 0) + (56 + 72 if command else 0)
    top = MARGIN + (30 if label else 0)
    bottom = H - MARGIN - (40 if footer else 0)
    y = top + max(0, (bottom - top - block) / 2.0)

    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H)]
    out.append('<defs><radialGradient id="glow" cx="88%%" cy="8%%" r="75%%">'
               '<stop offset="0" stop-color="%s" stop-opacity=".30"/><stop offset="1" stop-color="%s" stop-opacity="0"/>'
               '</radialGradient></defs>' % (th["accent"], th["accent"]))
    out.append('<rect width="%d" height="%d" fill="%s"/>' % (W, H, th["bg"]))
    out.append('<rect width="%d" height="%d" fill="url(#glow)"/>' % (W, H))
    out.append('<rect x="0" y="0" width="%d" height="8" fill="%s"/>' % (W, th["accent"]))
    if label:
        out.append('<text x="%d" y="%d" font-family="%s" font-size="26" font-weight="600" letter-spacing="2" fill="%s">%s</text>'
                   % (MARGIN, MARGIN + 12, esc(SANS), th["accent"], esc(label.upper())))
    y += title_size * 0.82
    out.append('<text x="%d" y="%.0f" font-family="%s" font-size="%d" font-weight="800" fill="%s">%s</text>'
               % (MARGIN, y, esc(SANS), title_size, th["title"], esc(title)))
    if tag_lines:
        y += 24
        for line in tag_lines:
            y += tag_size * 1.3
            out.append('<text x="%d" y="%.0f" font-family="%s" font-size="%d" fill="%s">%s</text>'
                       % (MARGIN, y, esc(SANS), tag_size, th["text"], esc(line)))
    if command:
        y += 56
        chip_w = min(usable, 34 + len("$ " + command) * 0.61 * cmd_size + 34)
        out.append('<rect x="%d" y="%.0f" width="%.0f" height="72" rx="14" fill="%s" stroke="%s" stroke-width="2"/>'
                   % (MARGIN, y, chip_w, th["panel"], th["border"]))
        out.append('<text x="%d" y="%.0f" font-family="%s" font-size="%d" fill="%s" xml:space="preserve">'
                   '<tspan fill="%s">$ </tspan>%s</text>'
                   % (MARGIN + 30, y + 36 + cmd_size * 0.35, esc(MONO), cmd_size, th["title"], th["accent"], esc(command)))
    if footer:
        out.append('<text x="%d" y="%d" font-family="%s" font-size="28" fill="%s">%s</text>'
                   % (MARGIN, H - MARGIN + 14, esc(SANS), th["dim"], esc(footer)))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def png_size(path):
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n":
            return None
        return struct.unpack(">II", head[16:24])
    except Exception:
        return None


def chrome_paths():
    names = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
             "microsoft-edge", "microsoft-edge-stable", "brave-browser"]
    found = [shutil.which(n) for n in names]
    found += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
    return [p for p in found if p and os.path.exists(p)]


def converters(svg, png):
    """(name, argv) for every converter present on this machine, most faithful first."""
    out = []
    if shutil.which("rsvg-convert"):
        out.append(("rsvg-convert", ["rsvg-convert", "-w", str(W), "-h", str(H), svg, "-o", png]))
    if shutil.which("resvg"):
        out.append(("resvg", ["resvg", "-w", str(W), "-h", str(H), svg, png]))
    if shutil.which("inkscape"):
        out.append(("inkscape", ["inkscape", svg, "--export-type=png", "--export-filename=" + png, "-w", str(W), "-h", str(H)]))
    for im in ("magick", "convert"):
        if shutil.which(im):
            out.append((im, [im, "-background", "none", svg, "-resize", "%dx%d!" % (W, H), png]))
            break
    for chrome in chrome_paths()[:1]:
        out.append(("chrome", [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                               "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H),
                               "--screenshot=" + png, "file://" + svg.replace(os.sep, "/")]))
    if shutil.which("ffmpeg"):
        out.append(("ffmpeg", ["ffmpeg", "-y", "-loglevel", "error", "-i", svg, "-frames:v", "1", "-update", "1", png]))
    return out


def to_png(svg_path, png_path):
    svg_path, png_path = os.path.abspath(svg_path), os.path.abspath(png_path)
    try:
        import cairosvg  # noqa: optional
        cairosvg.svg2png(url=svg_path, write_to=png_path, output_width=W, output_height=H)
        if png_size(png_path) == (W, H):
            return "cairosvg"
    except Exception:
        pass
    for name, argv in converters(svg_path, png_path):
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
            subprocess.run(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
        except Exception:
            continue
        if png_size(png_path) == (W, H):
            return name
    if os.path.exists(png_path):
        os.remove(png_path)
    return None


def main():
    ap = argparse.ArgumentParser(description="Generate a 1280x640 GitHub social preview card.")
    ap.add_argument("--title", required=True, help="project name")
    ap.add_argument("--tagline", default="", help="the one-line pitch from the README")
    ap.add_argument("--command", default="", help="install or run command shown in a terminal chip")
    ap.add_argument("--footer", default="", help='small line at the bottom, e.g. "github.com/owner/repo"')
    ap.add_argument("--label", default="", help='small caption above the title, e.g. "CLI" or "Agent skill"')
    ap.add_argument("--theme", choices=sorted(THEMES), default="dark")
    ap.add_argument("--accent", default="", help="accent colour as #rrggbb")
    ap.add_argument("-o", "--output", default="social-preview.png")
    ap.add_argument("--svg-only", action="store_true", help="write the SVG and skip PNG conversion")
    args = ap.parse_args()

    svg = build_svg(args.title, args.tagline, args.command, args.footer, args.label, args.theme, args.accent)
    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    svg_out = os.path.splitext(out)[0] + ".svg"
    if args.svg_only or out.lower().endswith(".svg"):
        with open(svg_out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("wrote %s (SVG only; GitHub needs PNG, JPG or GIF)" % svg_out)
        return

    tmp_dir = tempfile.mkdtemp(prefix="social-preview-")
    tmp_svg = os.path.join(tmp_dir, "card.svg")
    with open(tmp_svg, "w", encoding="utf-8") as fh:
        fh.write(svg)
    used = to_png(tmp_svg, out)
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if not used:
        with open(svg_out, "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("No SVG-to-PNG converter found, so only the SVG was written: %s" % svg_out)
        print("Install one of rsvg-convert, resvg, inkscape, ImageMagick or Chrome and run again,")
        print("or open the SVG in a browser and export it as a 1280x640 PNG.")
        sys.exit(2)
    size = os.path.getsize(out)
    print("wrote %s  (%dx%d, %.0f KB, via %s)" % (out, W, H, size / 1024.0, used))
    if size >= 1024 * 1024:
        print("warning: over GitHub's 1 MB limit; compress it before uploading", file=sys.stderr)
    print("Upload it by hand: repository Settings > General > Social preview > Edit > Upload an image.")


if __name__ == "__main__":
    main()
