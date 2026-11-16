# Street Fighter III 3rd Strike (sfiii3nr1) cheat patches

Each entry is a C source diff in `patches/` and BPS patches for the program chips in
`~/Downloads/sf3_ggpatch/<slug>/`. See `../AGENTS.md` for how they are written, built and applied.
Entries are in **Recorded:** order, newest last.

## Normal hits do double damage

**Source diff:** `patches/normal-hits-do-double-damage.diff`
**BPS:** `sf3_ggpatch/normal-hits-do-double-damage/` (simm1.0-.3)
**Changes:** 36 bytes. 06700000-0670001F: the new `cal_damage_vitality` (32 bytes of code and literal
pool). 0608D875, 0608EF91, 0608F381: the address of `cal_damage_vitality` in the literal pools of
`set_damage_and_piyo`, `player_at_vs_effect_dm` and `effect_at_vs_effect_dm` (3 bytes each).
**Recorded:** 2026-11-15 19:02:32

**Mechanism:** `cal_damage_vitality` (`src/pow_pow.c`) works out the damage of a hit:

```c
ds->wu.dm_vital = power * rate / 100;
if (as->wu.work_id == 1) {
    ds->wu.dm_vital = ds->wu.dm_vital * as->att_plus / 8;
}
if (ds->wu.work_id == 1) {
    ds->wu.dm_vital = ds->wu.dm_vital * ds->def_plus / 8;
}
```

`power` comes from `Power_Data` (the attack's power), `rate` from `Pow_Control_Data_1` (the round
level). This is a hook: the original is renamed `cal_damage_vitality_orig` and stays where it was, and a
new `cal_damage_vitality` in the CHEAT section (06700000) calls it, then doubles the result:

```c
ds->wu.dm_vital = ds->wu.dm_vital * 2;
```

The callers in other files load the function's address from their literal pools, so they now call the
new one. Nothing else moves.

**Evidence:** `cal_damage_vitality` is called from `set_damage_and_piyo` (`src/HITCHECK.c`, a
fighter's attack hitting the other fighter), `player_at_vs_effect_dm` (`src/HITPLEF.c`) and
`effect_at_vs_effect_dm` (`src/HITEFEF.c`). The last two only call it for effects with work id 122 or
123; other effects get `dm_vital = 256`. Projectiles hitting a fighter go through
`effect_at_vs_player_dm` (`src/HITEFPL.c`), which calls `cal_damage_vitality_eff` instead.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME on 2026-11-15: it works.
- Projectiles (fireballs and other effects that hit a fighter) do normal damage. Doubling them too
  would need the same hook on `cal_damage_vitality_eff`.
- Both fighters, player or CPU, do double damage.
- `set_damage_and_piyo` scales the doubled damage again afterwards (for example x125/100 for some
  hit states), as before.
- The stun gauge (`dm_piyo`) is not changed.

## Projectiles do double damage

**Source diff:** `patches/projectiles-do-double-damage.diff`
**BPS:** `sf3_ggpatch/projectiles-do-double-damage/` (simm1.0-.3)
**Changes:** 30 bytes. 06700000-0670001F: the new `cal_damage_vitality_eff` (code and literal pool).
0608F105: the address of `cal_damage_vitality_eff` in the literal pool of `effect_at_vs_player_dm` (3 bytes).
**Recorded:** 2026-11-15 19:56:29

**Mechanism:** This is the projectile version of "Normal hits do double damage".
`cal_damage_vitality_eff` (`src/pow_pow.c`) works out the damage when an effect (a fireball or other
projectile) hits a fighter, the same way as `cal_damage_vitality`:

```c
ds->wu.dm_vital = power * rate / 100;
```

then the attacker's and defender's power-ups. This is a hook: the original is renamed
`cal_damage_vitality_eff_orig`, and a new `cal_damage_vitality_eff` in the CHEAT section calls it, then
doubles the result:

```c
ds->wu.dm_vital = ds->wu.dm_vital * 2;
```

**Evidence:** the only caller is `effect_at_vs_player_dm` (`src/HITEFPL.c`), called from HITCHECK when an
effect's attack hits a fighter. After the call it scales `dm_vital` for the defender's state (x1.25,
x1.5 or x2), the owner's taunt power-ups, and combo scaling, as before. `sf3_cheat.py` found no moved code
or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Normal hits (punches, kicks and specials that hit with the fighter's own body) do normal damage.
  "Normal hits do double damage" covers those. Both diffs add a hook at the end of `src/pow_pow.c`,
  so `sf3_cheat.py build` can't apply them together (checked); a combined cheat needs one diff with
  both hooks.
- Both fighters' projectiles, player or CPU, do double damage. Chip damage on block comes from the
  same value, so it doubles too.

## Player 1 never takes damage

**Source diff:** `patches/player-1-never-takes-damage.diff`
**BPS:** `sf3_ggpatch/player-1-never-takes-damage/` (simm1.0-.3)
**Changes:** 58 bytes. 06700000-06700037: the new `Player_damage` and `subtract_dm_vital_aiuchi`.
065EAF89: the `Player_damage` entry of the `routine_no[1]` jump table (`data/PLMAIN_tbl.c`).
06116F05, 06118CF1: the address of `subtract_dm_vital_aiuchi` in the literal pools of `plcnt_move` and
`plcnt_b_move` (3 bytes each).
**Recorded:** 2026-11-15 19:58:07

**Mechanism:** The EarthBound "Enemies never hurt the party" and SMB3 "Enemies and spikes never hurt the
Player" idea. Health only goes down in `subtract_dm_vital` and `subtract_dm_vital_aiuchi`
(`src/PLPDM.c`):

```c
wk->wu.vital_new -= wk->wu.dm_vital;
```

`subtract_dm_vital` is called (by a short `bsr`) from `get_damage_reaction_data`, which
`Player_damage` calls on the first frame of a hit (`routine_no[3] == RN3_START`). Hooking
`subtract_dm_vital` itself moved code (the `bsr` became a longer call), so the hook is on
`Player_damage`, which is only reached through the jump table in `data/PLMAIN_tbl.c`. Both hooks set
the damage to 0 for side 0 (player 1) and then run the original:

```c
if (wk->wu.id == 0 && wk->wu.routine_no[3] == RN3_START) {
    wk->wu.dm_vital = 0;
}
Player_damage_orig(wk);
```

`subtract_dm_vital_aiuchi` (trades, where both fighters hit each other on the same frame, called from
`src/PLCNT2.c` and `src/plcntset_2.c`) gets the same check.

**Evidence:** `grep` finds `vital_new -=` for fighters only in these two functions. `Player_damage` runs
for hits and for blocked hits (chip damage). `get_damage_reaction_data` already sets `dm_vital = 0` for
`atemi_flag == 2`. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Player 1 still reacts to hits (hit stun, knockdown) and the stun gauge still fills, so player 1 can
  be dizzied. Only the health bar stays full.
- Player 2 gets no score for hitting player 1, since `Additinal_Score_DM` only runs when `dm_vital` is not 0.
- Throw damage was not traced separately; if a throw takes health some other way, it still does.
- Player 2 takes damage as normal.
