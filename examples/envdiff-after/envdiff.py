#!/usr/bin/env python3
"""envdiff - compare two .env files and report what is missing or different."""
import argparse
import json
import os
import sys


def parse(path):
    data = {}
    with open(path) as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def diff(a, b):
    return {
        "missing_in_second": sorted(set(a) - set(b)),
        "missing_in_first": sorted(set(b) - set(a)),
        "different": sorted(k for k in set(a) & set(b) if a[k] != b[k]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="envdiff", description="Compare two .env files.")
    ap.add_argument("first")
    ap.add_argument("second")
    ap.add_argument("--values", action="store_true", help="show differing values (hidden by default)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    a, b = parse(args.first), parse(args.second)
    d = diff(a, b)
    if args.json:
        print(json.dumps(d, indent=2))
        return 1 if any(d.values()) else 0

    n1, n2 = os.path.basename(args.first), os.path.basename(args.second)
    if d["missing_in_second"]:
        print("Missing in %s (%d):" % (n2, len(d["missing_in_second"])))
        for k in d["missing_in_second"]:
            print("  - %s" % k)
    if d["missing_in_first"]:
        print("Missing in %s (%d):" % (n1, len(d["missing_in_first"])))
        for k in d["missing_in_first"]:
            print("  + %s" % k)
    if d["different"]:
        print("Different values (%d):" % len(d["different"]))
        for k in d["different"]:
            if args.values:
                print("  ~ %s: %s -> %s" % (k, a[k], b[k]))
            else:
                print("  ~ %s" % k)
    same = len(set(a) & set(b)) - len(d["different"])
    print("%d key%s match." % (same, "" if same == 1 else "s"))
    return 1 if any(d.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
