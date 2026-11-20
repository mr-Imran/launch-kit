import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import envdiff


def test_diff():
    a = {"A": "1", "B": "2", "C": "3"}
    b = {"B": "2", "C": "9", "D": "4"}
    assert envdiff.diff(a, b) == {
        "missing_in_second": ["A"],
        "missing_in_first": ["D"],
        "different": ["C"],
    }


def test_parse(tmp_path):
    p = tmp_path / "x.env"
    p.write_text('# c\nexport A=1\nB="two"\n\nbad line\n')
    assert envdiff.parse(str(p)) == {"A": "1", "B": "two"}
