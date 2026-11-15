#!/usr/bin/env python3
"""Build Street Fighter III 3rd Strike cheat diffs into BPS patches for the program chips.

    python3 -I cheats/sf3_cheat.py reference
        Build the unpatched source (with only patches/_cheat-section.diff) in the build worktree. The program
        must match the arcade's SHA-1. Saves the link map and the decrypted program in cheats/ref/ (not in
        git), which "build" compares against. Run it again whenever main moves.

    python3 -I cheats/sf3_cheat.py build SLUG [SLUG ...] [--name NAME] [--zip OUT.zip] [--no-bps]
        Apply patches/_cheat-section.diff and patches/<SLUG>.diff (in that order) in the build worktree,
        build, then undo the diffs again. Checks:
          - the linker reports no overlap ("ADDRESS SPACE DUPLICATE") and no other problem;
          - no section other than the game's and PCHEAT/CCHEAT exists;
          - no code, table or data outside the cheat area (06700000-06787FFF) moved: every link-map range
            and every symbol address outside it is the same as in the reference build.
        Then writes one BPS per changed program chip to ~/Downloads/sf3_ggpatch/<NAME>/ (NAME defaults to
        the only SLUG), and applies each one back to the original chip to check it. --zip also writes the
        whole patched ROM set (about 70 MB) there, for testing in an emulator.

The build worktree is ~/vhstrace/worktrees/sfiii3-build (SF3_WORKTREE overrides it). It must be at main with
a clean `git status`, and holds its own rom/sfiii3nr1.zip (the full, non-merged set). The Windows tools run in
the Wine prefix ~/vhstrace/wine/sfiii3 (see AGENTS.md).
"""
import argparse, os, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

CHEATS = Path(__file__).resolve().parent
PATCHES = CHEATS / "patches"
REF = CHEATS / "ref"
SECTION_DIFF = PATCHES / "_cheat-section.diff"
WT = Path(os.environ.get("SF3_WORKTREE", Path.home() / "vhstrace/worktrees/sfiii3-build"))
WINE_BIN = Path.home() / "vhstrace/wine/Wine Devel.app/Contents/Resources/wine/bin"
WINEPREFIX = Path.home() / "vhstrace/wine/sfiii3"
FLIPS = Path.home() / "vhstrace/flips/flips"
OUT = Path.home() / "Downloads/sf3_ggpatch"
LOGS = Path(os.environ.get("TMPDIR", "/tmp")) / "sf3_cheat"

CHEAT_LO, CHEAT_HI = 0x06700000, 0x06788000            # PCHEAT, CCHEAT up to CSNDBANK
GAME_SECTIONS = {"CVECT", "P", "CTBL", "D", "R", "B", "CSNDBANK", "CSND", "CCDVOL"}
CHEAT_SECTIONS = {"PCHEAT", "CCHEAT"}
OK_LINK_MESSAGES = {"** 121 CANNOT FIND SECTION(PCHEAT)", "** 121 CANNOT FIND SECTION(CCHEAT)"}
EXPECTED_SHA1 = "7340968c4b2aba9496fa63be7a5c183205ff1dae"


def git(*args, check=True):
    p = subprocess.run(["git", "-C", str(WT), *args], capture_output=True, text=True)
    if check and p.returncode:
        sys.exit(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p


def check_worktree():
    if not (WT / "rom/sfiii3nr1.zip").exists():
        sys.exit(f"{WT}/rom/sfiii3nr1.zip is missing (see AGENTS.md)")
    st = git("status", "--porcelain").stdout.strip()
    if st:
        sys.exit(f"the build worktree {WT} is not clean; stop and ask the user:\n{st}")
    head, main = git("rev-parse", "HEAD").stdout.strip(), git("rev-parse", "main").stdout.strip()
    if head != main:
        sys.exit(f"the build worktree is at {head[:10]}, not main ({main[:10]}): "
                 f"git -C {WT} checkout --detach main, then run reference again")
    return head


def build(log):
    """Run the Makefile under Wine. Returns the log text; the caller decides what counts as failure."""
    for f in ("sf3.abs", "sf3.bin", "sf3.map", "build/prog.bin", "build/sfiii3nr1.zip"):
        (WT / f).unlink(missing_ok=True)                 # never pick up a stale output
    env = dict(os.environ, WINEPREFIX=str(WINEPREFIX), WINEDEBUG="-all",
               WINEDLLOVERRIDES="mscoree,mshtml,winemenubuilder.exe=d",
               PATH=f"{WINE_BIN}:{os.environ['PATH']}")
    if (WINEPREFIX / "dosdevices/z:").exists():
        sys.exit(f"{WINEPREFIX}/dosdevices/z: exists again: remove it (see AGENTS.md) before building")
    with open(log, "w") as f:
        subprocess.run(["gmake", "-j8", "BIN=wine bin", "SHC_TMP=tmp", "PYTHON=python3"],
                       cwd=WT, env=env, stdout=f, stderr=subprocess.STDOUT)
    return log.read_text(errors="replace").replace("\r", "")


def link_problems(text):
    msgs = [l.strip() for l in text.splitlines() if l.startswith("** ")]
    bad = [m for m in msgs if m not in OK_LINK_MESSAGES]
    if "address space duplicate" in text:
        bad.append("rof2bin: " + re.search(r".*address space duplicate.*", text).group(0).strip())
    return bad


def read_map(path):
    """(sections, ranges, symbols) of a link map: section names, (start, end) of every section and unit
    line, and {address: names} of every symbol."""
    sections, ranges, symbols = set(), [], {}
    for line in Path(path).read_text(errors="replace").replace("\r", "").splitlines():
        m = re.match(r"^(\S+)?\s+H'([0-9A-F]{8})\s+-\s+H'([0-9A-F]{8})\s+H'[0-9A-F]{8}\s*$", line)
        if m:
            if m.group(1):
                sections.add(m.group(1))
            ranges.append((int(m.group(2), 16), int(m.group(3), 16)))
            continue
        m = re.match(r"^(\S+)\s+H'([0-9A-F]{8})\s+(ENT|DAT|EQU)\s*$", line)
        if m:
            symbols.setdefault(int(m.group(2), 16), []).append(m.group(1))
    return sections, ranges, symbols


def outside(a):
    return not (CHEAT_LO <= a < CHEAT_HI)


def check_map(ref_map, new_map):
    rs, rr, ry = read_map(ref_map)
    ns, nr, ny = read_map(new_map)
    problems = []
    extra = ns - GAME_SECTIONS - CHEAT_SECTIONS
    if extra:
        problems.append(f"new sections {sorted(extra)}: only PCHEAT and CCHEAT are placed (no new globals: "
                        "DCHEAT/BCHEAT have no RAM yet, see AGENTS.md)")
    r1 = [r for r in rr if outside(r[0])]
    r2 = [r for r in nr if outside(r[0])]
    if r1 != r2:
        first = next((i for i, (a, b) in enumerate(zip(r1, r2)) if a != b), min(len(r1), len(r2)))
        a = r1[first] if first < len(r1) else None
        b = r2[first] if first < len(r2) else None
        problems.append(f"code or data moved: the link map's range {first} was "
                        f"{a and '%08X-%08X' % a}, now {b and '%08X-%08X' % b}")
    a1 = {a for a in ry if outside(a)}
    a2 = {a for a in ny if outside(a)}
    if a1 != a2:
        gone = sorted(a1 - a2)[:5]
        new = sorted(a2 - a1)[:5]
        problems.append("symbol addresses outside the cheat area changed: "
                        + ", ".join([f"{a:08X} {ry[a][0]} gone" for a in gone]
                                    + [f"{a:08X} {ny[a][0]} new" for a in new]))
    return problems, ny


def apply_diffs(diffs):
    for d in diffs:
        p = git("apply", "--check", str(d), check=False)
        if p.returncode:
            sys.exit(f"{d.name} does not apply to main:\n{p.stderr.strip()}")
    done = []
    try:
        for d in diffs:
            git("apply", str(d))
            done.append(d)
    except SystemExit:
        undo_diffs(done)
        raise
    return done


def undo_diffs(done):
    for d in reversed(done):
        p = git("apply", "-R", str(d), check=False)
        if p.returncode:
            print(f"!! could not undo {d.name}: {p.stderr.strip()}", file=sys.stderr)
    st = git("status", "--porcelain").stdout.strip()
    if st:
        print(f"!! the build worktree is not clean after undoing the diffs; fix it by hand:\n{st}", file=sys.stderr)


def cmd_reference():
    head = check_worktree()
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / "reference.log"
    done = apply_diffs([SECTION_DIFF])
    try:
        text = build(log)
        if (WT / "sf3.map").exists():
            shutil.copy(WT / "sf3.map", LOGS / "reference.map")
    finally:
        undo_diffs(done)
    bad = link_problems(text)
    if bad or f"sha1 {EXPECTED_SHA1}: matches" not in text:
        sys.exit("the reference build does not match the arcade program; see " + str(log) + "\n" + "\n".join(bad))
    REF.mkdir(exist_ok=True)
    shutil.copy(LOGS / "reference.map", REF / "sf3.map")
    shutil.copy(WT / "build/prog.bin", REF / "prog.bin")
    (REF / "HEAD").write_text(head + "\n")
    print(f"reference build matches; saved {REF}/sf3.map and prog.bin for {head[:10]}")


def chips(zpath, simm):
    with zipfile.ZipFile(zpath) as z:
        return {f"sfiii3-simm{simm}.{i}": z.read(f"sfiii3-simm{simm}.{i}") for i in range(4)}


def cmd_build(slugs, name, zip_out, no_bps):
    head = check_worktree()
    if not (REF / "HEAD").exists() or (REF / "HEAD").read_text().strip() != head:
        sys.exit("cheats/ref/ is missing or was made from another commit: run `sf3_cheat.py reference` first")
    if not name:
        if len(slugs) != 1:
            sys.exit("give --name for a build of several cheats")
        name = slugs[0]
    diffs = [PATCHES / f"{s}.diff" for s in slugs]
    for d in diffs:
        if not d.exists():
            sys.exit(f"{d} not found")
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{name}.log"
    done = apply_diffs([SECTION_DIFF, *diffs])
    try:
        text = build(log)
        built = (WT / "build/sfiii3nr1.zip").exists() and "build/sfiii3nr1.zip written" in text
        if built:
            shutil.copy(WT / "sf3.map", LOGS / f"{name}.map")
            new_prog = (WT / "build/prog.bin").read_bytes()
            tmpzip = LOGS / f"{name}.zip"
            shutil.copy(WT / "build/sfiii3nr1.zip", tmpzip)
    finally:
        undo_diffs(done)
    if not built:
        errs = [l for l in text.splitlines() if ") : " in l or "rror" in l][:20]
        sys.exit(f"the build failed; see {log}\n" + "\n".join(errs))
    bad = link_problems(text)
    problems, symbols = check_map(REF / "sf3.map", LOGS / f"{name}.map")
    if bad or problems:
        sys.exit(f"{name}: refused (log {log}, map {LOGS / (name + '.map')})\n" + "\n".join(bad + problems))

    old_prog = (REF / "prog.bin").read_bytes()
    diff = [i for i in range(len(old_prog)) if old_prog[i] != new_prog[i]]
    runs = []
    for i in diff:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
        else:
            runs.append([i, i])
    inside = sum(1 for i in diff if not outside(0x06000000 + i))
    print(f"{name}: {len(diff)} bytes changed ({inside} in the cheat area, {len(diff) - inside} outside)")
    for a, b in runs:
        addr = 0x06000000 + a
        near = max((s for s in symbols if s <= addr), default=None)
        label = f"  {symbols[near][0]}+{addr - near:X}" if near is not None and addr - near < 0x10000 else ""
        print(f"  {addr:08X} {b - a + 1:5d}{label}")

    if not no_bps:
        dest = OUT / name
        dest.mkdir(parents=True, exist_ok=True)
        for old in dest.glob("*.bps"):
            old.unlink()
        rom = WT / "rom/sfiii3nr1.zip"
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            for simm in (1, 2):
                o, n = chips(rom, simm), chips(tmpzip, simm)
                for chip in o:
                    if o[chip] == n[chip]:
                        continue
                    (t / "o").write_bytes(o[chip]); (t / "n").write_bytes(n[chip])
                    bps = dest / f"{chip}.bps"
                    subprocess.run([str(FLIPS), "--create", "--bps", str(t / "o"), str(t / "n"), str(bps)],
                                   check=True, capture_output=True)
                    subprocess.run([str(FLIPS), "--apply", str(bps), str(t / "o"), str(t / "c")],
                                   check=True, capture_output=True)
                    if (t / "c").read_bytes() != n[chip]:
                        sys.exit(f"{bps}: applying it to the original chip does not give the built chip")
                    print(f"  {bps} ({bps.stat().st_size} bytes, checked)")
    if zip_out:
        Path(zip_out).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(tmpzip, zip_out)
        print(f"  full ROM set: {zip_out} (run MAME with an empty -nvram_directory)")
    tmpzip.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("reference")
    b = sub.add_parser("build")
    b.add_argument("slugs", nargs="+")
    b.add_argument("--name")
    b.add_argument("--zip")
    b.add_argument("--no-bps", action="store_true")
    a = ap.parse_args()
    if a.cmd == "reference":
        cmd_reference()
    else:
        cmd_build(a.slugs, a.name, a.zip, a.no_bps)


if __name__ == "__main__":
    main()
