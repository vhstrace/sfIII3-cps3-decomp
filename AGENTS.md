# AGENTS.md

This is a matching decompilation of the CPS3 arcade game *Street Fighter III 3rd Strike* (`sfiii3nr1`), in C
and SH-2 assembler, built with Hitachi's SHC toolchain (fork at `vhstrace/sfIII3-cps3-decomp`). We use it to
make cheats as **C source diffs**, and ship each one as **BPS patches for the program chips**, so a player can
patch their own dump. Also read `~/vhstrace/disassemblies/AGENTS.md` (the shared rules) and
`../../nintendo_64/oot/AGENTS.md` (the OoT setup this one copies). Where they differ, this file wins.

There is no `CLAUDE.md` in this project (user's choice, 2026-11-15). Keep all instructions here.

## What is different from the other games

- **No ROMs are kept** (user's choice, 2026-11-15). A ROM set is 70 MB. For each cheat we save the C diff
  and its BPS patches, nothing else. No per-cheat, curated or collection ROMs, no `untagged/` or
  `interesting/` builds, no Batocera or MinUI sync, no Mesen2 sync. A full patched set is built only to
  test, in the session scratchpad (`--zip`), and deleted afterwards.
- **Except ROMs the user asks for** (2026-11-19). Build them only on request, as full non-merged sets
  (`--zip ~/Downloads/sf3_ggpatch/<name>/sfiii3nr1.zip`, next to that build's BPS files), and copy each to
  Batocera at `/Volumes/share/roms/mame/Game Genie Hacked/Street Fighter III 3rd Strike/<name>/sfiii3nr1.zip`
  (check with `cmp`). The file must be named `sfiii3nr1.zip`, so each build gets its own folder. `<name>` is
  the cheat's slug, or `sf3-curated` (Batocera folder `curated`) for the cheats tagged `curated`. The curated
  build uses `patches/_curated-specials.diff` in place of the four `curated` cheats that hook
  `Player_attack` (50% faster, 1.5x as far, 75% less high, ground specials in the air). Built so far: `sf3-curated`, `half-speed`,
  `time-moves-only-with-input`, `jump-again-in-mid-air`, `fighters-face-away`, `slippery-floors`, `conveyor-belt-floor`, `every-attack-hits-anywhere`, `music-and-sound-effects-high-pitched`, `fighters-move-each-other`. They launch on Batocera (checked by the user, 2026-11-19).
  They go in `mame`, not `fbneo` (2026-11-19): FBNeo finds each chip by its CRC, so it reports the four
  patched program chips as missing. MAME only warns about the wrong checksums.
  Batocera's `mame` folder runs MAME 2003-Plus by default, which has no CPS3, so `batocera.conf` has
  `mame["sfiii3nr1.zip"].emulator=mame` and `.core=mame` (standalone MAME). MAME loads the program flash
  from nvram over the ROM, keyed by `sfiii3nr1`, so `/userdata/system/scripts/sf3-cheat-nvram.sh` deletes
  that nvram whenever a ROM under `Game Genie Hacked/Street Fighter III 3rd Strike/` starts. (Both set up
  2026-11-19.)
- **BPS patches are per chip.** People's `sfiii3nr1.zip` files differ (split, merged or non-merged sets, and
  different zip tools), but the chip files inside are always the same. So each cheat's BPS patches the
  program chip files (`sfiii3-simm1.0` to `.3`), not the zip.
- The user tests in MAME, on the Mac and on Batocera (FBNeo rejects patched chips, see above). Write "Not
  tested." as usual.

## ROM

- `rom/sfiii3nr1.zip` (ignored by git) is a full, non-merged set (41 files, md5
  `e38cefe000e2e27ae631cbb2c18d56af`), made on 2026-11-15 from the user's split set
  `~/Downloads/sfiii3nr1.zip` (5 files, md5 `6573a2754d340847344c88a734111a13`) plus the shared files of
  `~/ROMs/mamecurrent/sfiii3.zip`, each checked by CRC against `mame -listroms sfiii3nr1`. MAME verifies it as
  good on its own. The build needs a full set: it reads SIMM 2 and copies every file into its output.
- Never write to it or to the user's dumps. The build worktree has its own copy.
- The program SIMM chip CRCs are listed in `README.md`.

## Building (Wine)

The tools in `bin/` are 32-bit Windows programs. They run in Wine:

- Wine is Gcenx's `wine-devel` 11.21 (`Gcenx/macOS_Wine_builds`, release 11.21, sha256
  `9909b486657e10ab66c7279371ae1f990345b596b3b1b3a0cf21f28af24fa0ce`), unpacked as
  `~/vhstrace/wine/Wine Devel.app`. Homebrew disabled all its Wine casks on 2026-09-01 (they fail
  Gatekeeper); the user chose this unsigned build. It runs under Rosetta.
- The prefix is `~/vhstrace/wine/sfiii3`. Its `Z:` drive (all of `/`) is removed, and the folders under
  `drive_c/users/jay/` that linked to `~/Desktop`, `~/Documents`, `~/Downloads` and the rest are plain empty
  folders. The only drives are `C:` (the prefix) and `D:` (the build worktree). Keep it that way: if Wine
  adds `Z:` or the links back, remove them before building (`sf3_cheat.py` refuses to build while `z:`
  exists). This stops the tools from finding the user's files the usual way; it is not a sandbox. The four
  rebuilt compiler stages in `bin/` (`shcasm`, `shcgen`, `shcmdl`, `shcpep`) were not checked against their
  source (`gibletto/shc-5r26-decomp-sf3`, checked clean on 2026-11-15).
- The Makefile runs unchanged:

  ```
  export WINEPREFIX=~/vhstrace/wine/sfiii3 WINEDEBUG=-all WINEDLLOVERRIDES="mscoree,mshtml,winemenubuilder.exe=d"
  export PATH="$HOME/vhstrace/wine/Wine Devel.app/Contents/Resources/wine/bin:$PATH"
  gmake -j8 BIN="wine bin" SHC_TMP=tmp PYTHON=python3
  ```

  A full build takes about 2.5 minutes, a relink about 10 seconds. `prog.bin sha1 ...: matches` means the
  program is the arcade's. `sed` on this Mac is GNU sed (`sed -i`, not `sed -i ''`).

### Build worktree

Build only in `~/vhstrace/worktrees/sfiii3-build` (detached at `main`, with its own `rom/sfiii3nr1.zip`).
This checkout is on `cheat-hunt` and is never built in. Same rule as OoT: the worktree's `git status` must
be empty before and after every build. Apply the diffs, build, and `git apply -R` them right away.
`cheats/sf3_cheat.py` does all of this; use it rather than building by hand. If the worktree isn't clean,
stop and ask. When `main` moves, `git -C ~/vhstrace/worktrees/sfiii3-build checkout --detach main` and run
`sf3_cheat.py reference` again.

## Memory layout: why cheats are written the way they are

- The program is 06000000-06FFFFFF: SIMM 1 is 06000000-067FFFFF (code, tables, data, sound), SIMM 2 is
  06800000-06FFFFFF (graphics, not built).
- Code (`P`) ends at 0613BD97, and `sf3.sub` fixes the tables and data (`CTBL,D`) at 0613BD98. There is no
  free space: code that grows by even 2 bytes overlaps the tables. The linker only warns
  (`** 117 ADDRESS SPACE DUPLICATE`), `rof2bin` prints `address space duplicate P,CTBL`, and a broken ROM is
  still written. `sf3_cheat.py` treats this as an error.
- The encryption depends on each byte's address. If anything moves, every encrypted byte after it changes,
  and the BPS grows to megabytes (tested: moving the tables gave 4.2 MB of chip patches). If nothing moves,
  only the changed bytes change (tested: a double-damage cheat changed 36 bytes and gave four 39-52 byte
  patches).
- 066166E4-06787FFF is empty (zeros) in the arcade ROM. `patches/_cheat-section.diff` adds
  `PCHEAT,CCHEAT(06700000)` to `sf3.sub`, so cheat code and constants go at 06700000 (about 550 KB, up to the
  sound bank at 06788000). With no cheat code, it changes nothing (the linker notes
  `121 CANNOT FIND SECTION`, which is fine) and the build still matches. `sf3_cheat.py` always applies it
  first. Cheat diffs never change `sf3.sub`.

## Writing a cheat diff

Rule: **nothing outside 06700000-06787FFF may move.** `sf3_cheat.py build` compares every link-map range
and symbol address with the reference build and refuses the cheat if any moved.

- **Same-size changes** go in place: a constant, a table value, a comparison that compiles to the same
  number of instructions. Check with the build; if it moves anything, use a hook instead.
- **Anything else is a hook.** Rename the original function (a name doesn't change any bytes), and add the
  new version under the original name in the CHEAT section at the end of the same file:

  ```c
  void cal_damage_vitality_orig(PLW* as, PLW* ds) {   /* was cal_damage_vitality: unchanged */
      ...
  }
  ...
  #pragma section CHEAT
  void cal_damage_vitality(PLW* as, PLW* ds) {
      cal_damage_vitality_orig(as, ds);
      ds->wu.dm_vital = ds->wu.dm_vital * 2;
  }
  #pragma section
  ```

  Callers in other files load the function's address from a literal pool, so only those 4-byte addresses
  change. The new function can call the original, or replace it entirely.
- A caller in the same file may use a short call (`bsr`) whose size depends on the distance. If the build
  refuses the cheat because that caller moved, hook the caller too.
- `#pragma inline` functions and `static` functions: hook the function that uses them instead.
- **No new global or static variables.** They would go in `DCHEAT`/`BCHEAT`, which have no RAM placed yet;
  `sf3_cheat.py` refuses new sections. Use the game's own work areas (`include/work.h`) or locals. Constant
  tables (`const`) are fine: they go in `CCHEAT`.
- Don't change headers unless needed: the Makefile has no header dependencies, so a header change rebuilds
  everything (2.5 minutes).
- `functions.tsv` lists every routine with its address, size and file. `docs/HOW_THE_GAME_WORKS.md` is a
  tour of the frame loop, input, specials, hit boxes and damage.

## Building a cheat

```
python3 -I cheats/sf3_cheat.py reference          # once, and after main moves
python3 -I cheats/sf3_cheat.py build <slug>       # writes ~/Downloads/sf3_ggpatch/<slug>/*.bps
python3 -I cheats/sf3_cheat.py build <slug> --zip <scratchpad>/<slug>/sfiii3nr1.zip   # also a full set to test
```

- It prints each changed address with the nearest symbol. Check that the bytes outside the cheat area are
  only the expected literal-pool addresses (or the in-place change).
- It writes one BPS per changed chip (`sfiii3-simm1.0.bps` ... `.3.bps`; an SH-2 instruction spans two
  chips, so most cheats change all four), and applies each back to the original chip to check it.
- Logs and maps are in `$TMPDIR/sf3_cheat/`.
- **Combining cheats:** `build a b --name a+b`. Every cheat puts its code at 06700000, so single-cheat
  patches can't be stacked; a combined build gets its own patches.
- **Testing in MAME:** MAME keeps the program flash in nvram and loads it over the ROM files, so always use
  an empty `-nvram_directory` (see `README.md`). Only launch an emulator when the user asks:

  ```
  SDL_JOYSTICK_MFI=0 mame sfiii3nr1 -rompath <scratchpad>/<slug> \
    -nvram_directory <empty scratchpad folder> -skip_gameinfo -window
  ```

  MAME warns about wrong checksums for the patched chips; that is expected.
- **MAME config and controller** (set up 2026-11-15): `~/.mame/mame.ini` sets `cfg_directory` to
  `~/.mame/cfg`, so MAME no longer writes `cfg/` into the current folder. Don't pass `-cfg_directory`:
  `~/.mame/cfg/sfiii3nr1.cfg` holds the user's Xbox 360 pad layout (punches X/Y/RB, kicks A/B/RT, keyboard
  keys kept). `SDL_JOYSTICK_MFI=0` (also exported in `~/.zshenv`) makes SDL find the pad at startup; without
  it macOS reports the pad late and MAME never sees it.
- Patched ROMs no longer play Fightcade replays or load savestates from the original.

### Applying a patch (for the player)

Unzip `sfiii3nr1.zip`, apply each `sfiii3-simm1.N.bps` to the file of the same name (Flips, or
RomPatcher.js), and zip the files back up as `sfiii3nr1.zip`. A split set also needs the parent
`sfiii3.zip`, as before.

## Files

On `cheat-hunt`:

- `cheats/sf3_patches.md`: one entry per cheat, newest last.
- `cheats/patches/<slug>.diff`: the C change, made against `main` with no other patch applied
  (`git diff -- src data include lib`). `_cheat-section.diff` is the shared `sf3.sub` change.
- `cheats/TODO.md`, `cheats/sf3_cheat.py`.
- `cheats/ref/`: the reference map and decrypted program. Not in git (it holds data from the ROM).

Outputs: `~/Downloads/sf3_ggpatch/<slug>/sfiii3-simm1.N.bps`. When a cheat is removed, delete its folder.

## Entry format

```
## Short title that says what the player sees

**Source diff:** `patches/<slug>.diff`
**BPS:** `sf3_ggpatch/<slug>/` (simm1.0-.3), or "not built yet"
**Changes:** the changed addresses (from sf3_cheat.py), or "not built yet"
**Recorded:** YYYY-MM-DD HH:MM:SS

**Mechanism:** what the original code does (quote the C, with the function and file), and what the
patched code does. Say whether it is in place or a hook.

**Evidence:** functions, variables and headers checked, and the `git apply --check` result.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Side effects and limits.
```

No `Tags:` line unless the user asks. When porting a cheat from another game, say which one in the
Mechanism.

## Cloud sessions (phone and web)

A cloud session has no ROM and no Wine, so it can't build. It:

- works on `cheat-hunt`, and commits only files in `cheats/`. `.claude/settings.json` turns on
  `cheats/githooks/pre-commit` in cloud sessions; it refuses anything else and anything that looks like a
  ROM;
- writes the diff as above (`git diff -- src data include lib > cheats/patches/<slug>.diff`, then
  `git checkout -- src data include lib`, then `git apply --check`), and the entry with **BPS:** and
  **Changes:** "not built yet" and the caveat "Not built";
- follows the hook rules above, since it can't run the size check;
- never commits ROMs, `rom/`, `build/`, `obj/` or bytes copied from a ROM.

On the Mac, `git pull` on `cheat-hunt`, build each new diff with `sf3_cheat.py`, fill in **BPS:** and
**Changes:**, remove "Not built", commit and push.

## Commits

- Commit `cheats/` and this file on `cheat-hunt` after each change, and push. Messages: `Add: <title>`,
  `Remove: <title> (doesn't work)`, or a short plain sentence. No attribution lines.
- Don't commit the source on `main` unless the user asks.
