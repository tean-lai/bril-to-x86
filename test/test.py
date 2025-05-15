#!/usr/bin/env python3
import subprocess
import glob
import os
import sys
import tempfile


def extract_args(bril_file):
    """
    Scan the Bril program for a line beginning with '# ARGS:' and extract its arguments.
    Returns a list of argument strings, or an empty list if no ARGS line is found.
    """
    with open(bril_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#"):
                parts = line.lstrip("#").strip().split(None, 1)
                if parts and parts[0].upper() == "ARGS:" and len(parts) == 2:
                    return parts[1].split()
    return []


def normalize_whitespace(s):
    """
    Normalize whitespace in a string by collapsing all whitespace sequences to single spaces
    and stripping leading/trailing space.
    """
    return " ".join(s.split())


def run_reference(bril_file, args):
    with open(bril_file, "r") as f:
        p1 = subprocess.Popen(
            ["bril2json"],
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p2 = subprocess.Popen(
            ["brili"] + args,
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p1.stdout.close()
        out, err = p2.communicate()
    return p2.returncode, out, err


def run_compiled(bril_file, args, rt_c_path):
    with open(bril_file, "r") as f:
        p1 = subprocess.Popen(
            ["bril2json"],
            stdin=f,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p2 = subprocess.Popen(
            ["python3", "bril2x86.py"],
            stdin=p1.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        p1.stdout.close()
        asm, err_asm = p2.communicate()
        if p2.returncode != 0:
            return None, None, f"[bril2x86.py failed] {err_asm}"

    fd, exec_path = tempfile.mkstemp(prefix="bril_exec_")
    os.close(fd)
    gcc = subprocess.run(
        ["gcc", rt_c_path, "-x", "assembler", "-o", exec_path, "-"],
        input=asm,
        text=True,
        capture_output=True,
    )
    if gcc.returncode != 0:
        os.unlink(exec_path)
        return None, None, f"[gcc failed] {gcc.stderr}"

    run = subprocess.run([exec_path] + args, capture_output=True, text=True)
    out, code = run.stdout, run.returncode

    os.unlink(exec_path)
    return code, out, None


def main():
    use_fallback = False
    fallback_args = []
    if len(sys.argv) > 1 and sys.argv[1] == "--fallback-args":
        use_fallback = True
        fallback_args = sys.argv[2:]

    bril_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../bril/benchmarks/core/")
    )
    rt_c = os.path.join(os.path.dirname(__file__), "../rt.c")

    if not os.path.isfile(rt_c):
        print(f"Error: could not find runtime C file at {rt_c}", file=sys.stderr)
        sys.exit(1)

    pattern = os.path.join(bril_root, "**", "*.bril")
    files = sorted(glob.glob(pattern, recursive=True))
    if not files:
        print("No .bril files found!", file=sys.stderr)
        sys.exit(1)

    failures = []
    for f in files:
        rel = os.path.relpath(f, bril_root)
        args = fallback_args if use_fallback else extract_args(f)

        print(f"Testing {rel} with args: {args} ...", end=" ")
        ref_code, ref_out, ref_err = run_reference(f, args)
        if ref_code is None:
            failures.append((rel, "reference", ref_err))
            print("REF_FAIL")
            continue

        cmp_code, cmp_out, cmp_err = run_compiled(f, args, rt_c)
        if cmp_err:
            failures.append((rel, "compiled", cmp_err))
            print("CMP_FAIL")
            continue

        # Compare codes and normalized outputs to ignore whitespace differences
        if ref_code != cmp_code or normalize_whitespace(
            ref_out
        ) != normalize_whitespace(cmp_out):
            failures.append(
                (
                    rel,
                    "mismatch",
                    {
                        "ref_code": ref_code,
                        "cmp_code": cmp_code,
                        "ref_out": ref_out,
                        "cmp_out": cmp_out,
                    },
                )
            )
            print("DIFF")
        else:
            print("ok")

    if failures:
        print("\n=== FAILURES ===")
        for rel, kind, info in failures:
            print(f"\nFile: {rel} — {kind}")
            if isinstance(info, str):
                print(info)
            else:
                print(f"  ref exit {info['ref_code']}, cmp exit {info['cmp_code']}")
                print("  --- ref stdout ---")
                print(info["ref_out"], end="")
                print("  --- cmp stdout ---")
                print(info["cmp_out"], end="")
        sys.exit(1)
    else:
        print("\nAll tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
