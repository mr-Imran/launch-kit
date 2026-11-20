"""Tests for the bundled scripts. Standard library only:

    python3 -m unittest discover tests
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "launch-kit", "scripts")
EVALS = os.path.join(ROOT, "skills", "launch-kit", "evals")
WEAK = os.path.join(EVALS, "full-launch-prep-weak-readme", "files")
DECENT = os.path.join(EVALS, "launch-posts-only-no-edits", "files")


def run(script, *args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=cwd)


def audit(path):
    p = run("audit.py", path, "--json", "--no-remote")
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(folder, name, text):
    path = os.path.join(folder, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class AuditTest(unittest.TestCase):
    def test_points_add_up_to_100(self):
        res = audit(WEAK)
        self.assertEqual(sum(c["max"] for c in res["checks"]), 100)

    def test_weak_readme_scores_low(self):
        res = audit(WEAK)
        status = {c["id"]: c["status"] for c in res["checks"]}
        self.assertLess(res["score"], 30)
        self.assertEqual(status["readme.pitch"], "partial")      # "This is a tool I made..."
        self.assertEqual(status["readme.visual"], "fail")
        self.assertEqual(status["readme.install"], "fail")
        self.assertEqual(status["repo.license"], "fail")
        self.assertEqual(status["gh.topics"], "skip")            # --no-remote

    def test_decent_readme_scores_higher(self):
        res = audit(DECENT)
        status = {c["id"]: c["status"] for c in res["checks"]}
        self.assertGreater(res["score"], 65)
        self.assertEqual(status["readme.pitch"], "pass")
        self.assertEqual(status["readme.install"], "pass")
        self.assertEqual(status["repo.license"], "pass")
        self.assertEqual(status["readme.visual"], "fail")        # still no demo

    def test_skipped_checks_do_not_count(self):
        res = audit(DECENT)
        live = [c for c in res["checks"] if c["status"] != "skip"]
        self.assertEqual(res["points_possible"], sum(c["max"] for c in live))
        self.assertLess(res["points_possible"], 100)

    def test_headline_accounts_for_every_point_left_out(self):
        with tempfile.TemporaryDirectory() as d:                  # no manifest: that check does not apply
            write(d, "README.md", "# x\n")
            res = audit(d)
            self.assertEqual(res["not_checked_points"], 15)
            self.assertEqual(sum(i["points"] for i in res["not_applicable"]), 2)
            self.assertEqual(res["points_possible"], 100 - 15 - 2)
            p = run("audit.py", d, "--no-remote", "--summary")
            self.assertIn("GitHub metadata (15 points) not checked", p.stdout)
            self.assertIn("Package metadata filled in (2) does not apply", p.stdout)

    def test_empty_folder_does_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            res = audit(d)
            self.assertLess(res["score"], 20)

    def test_broken_image_and_secret_file_are_caught(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n\nCompares two files and prints the difference.\n\n![demo](assets/missing.gif)\n")
            write(d, ".env", "TOKEN=abc\n")
            status = {c["id"]: c for c in audit(d)["checks"]}
            self.assertEqual(status["readme.links"]["status"], "fail")
            self.assertIn("assets/missing.gif", status["readme.links"]["detail"])
            self.assertEqual(status["repo.secrets"]["status"], "fail")

    def test_nothing_is_earned_for_what_is_absent(self):
        # A README with no links, images or badges must not collect points for them.
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n")
            res = audit(d)
            earned = {c["id"]: c["earned"] for c in res["checks"] if c["earned"]}
            # What is left: the file exists (3), nothing in it is broken (2+2+1), no secrets (4).
            self.assertEqual(set(earned), {"readme.exists", "readme.placeholders", "readme.links", "readme.h1", "repo.secrets"})
            self.assertEqual(res["points_earned"], 12)

    def test_image_without_alt_text_loses_points(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "demo.gif", "x")
            write(d, "README.md", "# x\n\nCompares two files and prints the difference.\n\n![](demo.gif)\n")
            status = {c["id"]: c for c in audit(d)["checks"]}
            self.assertEqual(status["readme.visual"]["earned"], 8)

    def test_saying_there_is_no_license_is_not_a_license_mention(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n\nThere is no license yet.\n")
            self.assertEqual({c["id"]: c["status"] for c in audit(d)["checks"]}["readme.license"], "fail")
            write(d, "README.md", "# x\n\n## License\n\nMIT\n")
            self.assertEqual({c["id"]: c["status"] for c in audit(d)["checks"]}["readme.license"], "pass")

    def test_folder_inside_another_repository_does_not_borrow_its_remote(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as d:
            sub = os.path.join(d, "examples", "tool")
            write(sub, "README.md", "# tool\n")
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(["git", "-C", d, "remote", "add", "origin", "https://github.com/someone/outer.git"], check=True)
            p = run("audit.py", sub, "--json")                   # remote checks on
            res = json.loads(p.stdout)
            self.assertEqual(res["not_checked_reason"], "inside another repository")
            self.assertEqual(res["repo"], "tool")                # not "outer"

    def test_env_example_is_not_a_secret(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n")
            write(d, ".env.example", "TOKEN=\n")
            status = {c["id"]: c["status"] for c in audit(d)["checks"]}
            self.assertEqual(status["repo.secrets"], "pass")

    def test_navigation_links_are_not_a_pitch(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n\n[Docs](a) | [Install](b) | [Chat](c) | [Blog](e)\n\n## Install\n")
            status = {c["id"]: c["status"] for c in audit(d)["checks"]}
            self.assertEqual(status["readme.pitch"], "fail")

    def test_unfilled_owner_in_a_code_block_is_caught(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n\nCompares two files and prints the difference.\n\n"
                                  "```sh\npipx install git+https://github.com/OWNER/x\n```\n")
            status = {c["id"]: c["status"] for c in audit(d)["checks"]}
            self.assertEqual(status["readme.placeholders"], "fail")

    def test_todo_in_a_code_block_is_not_a_placeholder(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "README.md", "# x\n\nCompares two files and prints the difference.\n\n"
                                  "```py\n# TODO: handle tabs\n```\n")
            status = {c["id"]: c["status"] for c in audit(d)["checks"]}
            self.assertEqual(status["readme.placeholders"], "pass")

    def test_fixes_are_grouped_by_piece_of_work(self):
        res = audit(WEAK)
        self.assertEqual(res["repo"], "envdiff")                 # from pyproject.toml, not the folder name
        demo = [f for f in res["fixes"] if f["title"] == "Demo"][0]
        self.assertEqual(demo["points"], 14)                     # 10 in the README + 4 as a file
        points = [f["points"] for f in res["fixes"]]
        self.assertEqual(points, sorted(points, reverse=True))   # biggest gain first
        titles = [f["title"] for f in res["fixes"]]
        self.assertIn("Package metadata", titles)                # GitHub half skipped, so it is not named
        gained = sum(f["points"] for f in res["fixes"])
        self.assertEqual(gained, res["points_possible"] - res["points_earned"])

    def test_summary_is_short_and_plain_when_piped(self):
        p = run("audit.py", WEAK, "--no-remote", "--summary")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Launch score: 15/100", p.stdout)
        self.assertIn("First impression", p.stdout)
        self.assertNotIn("\x1b[", p.stdout)                      # no colour codes when not a terminal
        self.assertLess(p.stdout.count("\n"), 16)

    def test_min_flag_sets_exit_status(self):
        self.assertEqual(run("audit.py", WEAK, "--no-remote", "--min", "90").returncode, 1)
        self.assertEqual(run("audit.py", WEAK, "--no-remote", "--min", "5").returncode, 0)


class TermDemoTest(unittest.TestCase):
    def test_records_real_output(self):
        with tempfile.TemporaryDirectory() as d:
            out, dump = os.path.join(d, "demo.svg"), os.path.join(d, "dump.json")
            p = run("term_demo.py", "--cmd", "echo hello-from-test", "-o", out, "--dump", dump)
            self.assertEqual(p.returncode, 0, p.stderr)
            svg = read(out)
            xml.dom.minidom.parseString(svg)                      # well-formed
            self.assertIn("hello-from-test", svg)
            self.assertIn("prefers-reduced-motion", svg)
            step = json.loads(read(dump))["steps"][0]
            self.assertEqual(step["output"].strip(), "hello-from-test")
            self.assertEqual(step["exit_status"], 0)

    def test_given_output_is_not_executed(self):
        with tempfile.TemporaryDirectory() as d:
            marker = os.path.join(d, "ran")
            spec = {"steps": [{"cmd": "touch %s" % marker, "output": "<b> & \x1b[31mred\x1b[0m"}]}
            write(d, "spec.json", json.dumps(spec))
            out = os.path.join(d, "demo.svg")
            p = run("term_demo.py", "--spec", os.path.join(d, "spec.json"), "-o", out)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertFalse(os.path.exists(marker))
            svg = read(out)
            xml.dom.minidom.parseString(svg)
            self.assertIn("&lt;b&gt; &amp;", svg)
            self.assertNotIn("\x1b", svg)

    def test_frame_option_freezes_the_animation(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "still.svg")
            p = run("term_demo.py", "--cmd", "echo hi", "-o", out, "--frame", "1.5")
            self.assertEqual(p.returncode, 0, p.stderr)
            svg = read(out)
            xml.dom.minidom.parseString(svg)
            self.assertIn("animation-play-state:paused", svg)

    def test_window_fits_the_recording_unless_rows_is_set(self):
        with tempfile.TemporaryDirectory() as d:
            text = "\n".join("line %d" % i for i in range(9))
            out = os.path.join(d, "demo.svg")
            write(d, "fit.json", json.dumps({"steps": [{"cmd": "x", "output": text}]}))
            p = run("term_demo.py", "--spec", os.path.join(d, "fit.json"), "-o", out)
            self.assertEqual(p.stderr, "")
            fitted = xml.dom.minidom.parseString(read(out)).documentElement.getAttribute("height")
            write(d, "small.json", json.dumps({"rows": 5, "steps": [{"cmd": "x", "output": text}]}))
            p = run("term_demo.py", "--spec", os.path.join(d, "small.json"), "-o", out)
            self.assertIn("scroll away", p.stderr)                # 11 rows do not fit in 5, and it says so
            small = xml.dom.minidom.parseString(read(out)).documentElement.getAttribute("height")
            self.assertGreater(int(fitted), int(small))

    def test_long_output_is_capped(self):
        with tempfile.TemporaryDirectory() as d:
            text = "\n".join("line %d" % i for i in range(50))
            write(d, "spec.json", json.dumps({"steps": [{"cmd": "seq", "output": text, "max_lines": 5}]}))
            out = os.path.join(d, "demo.svg")
            run("term_demo.py", "--spec", os.path.join(d, "spec.json"), "-o", out)
            svg = read(out)
            self.assertIn("46 more lines", svg)
            self.assertNotIn("line 49", svg)


class SocialPreviewTest(unittest.TestCase):
    def test_svg_card(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "card.svg")
            p = run("social_preview.py", "--title", "my<tool>", "--tagline", "Does one thing & does it well",
                    "--command", "npx mytool", "--svg-only", "-o", out)
            self.assertEqual(p.returncode, 0, p.stderr)
            svg = read(out)
            doc = xml.dom.minidom.parseString(svg)
            self.assertEqual(doc.documentElement.getAttribute("width"), "1280")
            self.assertEqual(doc.documentElement.getAttribute("height"), "640")
            self.assertIn("my&lt;tool&gt;", svg)


if __name__ == "__main__":
    unittest.main()
