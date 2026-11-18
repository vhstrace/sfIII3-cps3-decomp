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

Tags: `demo-ready` `play-start`

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

- Tested by the user in MAME (2026-11-15): works.
- Normal hits (punches, kicks and specials that hit with the fighter's own body) do normal damage.
  "Normal hits do double damage" covers those. Both diffs add a hook at the end of `src/pow_pow.c`,
  so `sf3_cheat.py build` can't apply them together (checked); a combined cheat needs one diff with
  both hooks.
- Both fighters' projectiles, player or CPU, do double damage. Chip damage on block comes from the
  same value, so it doubles too.

## Player 1 never takes damage

**Source diff:** `patches/player-1-never-takes-damage.diff`
**BPS:** `sf3_ggpatch/player-1-never-takes-damage/` (simm1.0-.3)
**Changes:** 92 bytes. 06700000-0670005B: the new `setup_catch_atthit`, `Player_damage` and
`subtract_dm_vital_aiuchi`. 065EAF89: the `Player_damage` entry of the `routine_no[1]` jump table
(`data/PLMAIN_tbl.c`). 06125A01: the address of `setup_catch_atthit` in the literal pool of
`catch_cg_type_check`. 06116F05, 06118CF1: the address of `subtract_dm_vital_aiuchi` in the literal pools
of `plcnt_move` and `plcnt_b_move` (3 bytes each).
**Recorded:** 2026-11-15 19:58:07

Tags: `demo-ready` `play-start`

**Mechanism:** The EarthBound "Enemies never hurt the party" and SMB3 "Enemies and spikes never hurt the
Player" idea. Health only goes down in `subtract_dm_vital`, `subtract_dm_vital_aiuchi` (`src/PLPDM.c`)
and `subtract_cu_vital` (`src/PLPCA.c`, throws):

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
`src/PLCNT2.c` and `src/plcntset_2.c`) gets the same check. Throw damage is worked out by
`setup_catch_atthit` (`src/HITCHECK.c`, called only from `catch_cg_type_check` in `src/PLPCA.c`) and taken
off later by `subtract_cu_vital`, which has short calls from its own file; so `setup_catch_atthit` is
hooked instead, and sets `dm_vital = 0` after the original when the one thrown is player 1.

**Evidence:** `grep` finds `vital_new -=` for fighters only in these three functions. `Player_damage` runs
for hits and for blocked hits (chip damage). `get_damage_reaction_data` already sets `dm_vital = 0` for
`atemi_flag == 2`. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Player 1 still reacts to hits (hit stun, knockdown) and the stun gauge still fills, so player 1 can
  be dizzied. Only the health bar stays full.
- Player 2 gets no score for hitting player 1, since `Additinal_Score_DM` only runs when `dm_vital` is not 0.
- Player 2 takes damage as normal.

## Health drains slowly during a round

**Source diff:** `patches/health-drains-slowly.diff`
**BPS:** `sf3_ggpatch/health-drains-slowly/` (simm1.0-.3)
**Changes:** 159 bytes. 06700000-0670009F: the new `vital_cont_main`. 06095C21: its address in the literal
pool of `Game2_1` (`sf3_cheat.py` names the nearest symbol, `Game2_3`).
**Recorded:** 2026-11-15 19:59:03

Tags: `demo-ready` `curated` `play-start`

**Mechanism:** The 3rd Strike version of the OoT "Link loses a quarter heart every 20 seconds" drain (and
the Metroid, Zelda 1 and ALTTP drains). `vital_cont_main` (`src/VITAL.c`) runs once per fight frame
from `Game2_1` and redraws the health bars from `plw[pl].wu.vital_new`. This is a hook: the original is
renamed `vital_cont_main_orig`, and the new one first takes 1 point from each fighter every 30 frames:

```c
if (Allow_a_battle_f && Bonus_Game_Flag == 0 && !EXE_flag && !Game_pause && (Game_timer % 30) == 0) {
    for (i = 0; i < 2; i++) {
        if (plw[i].dead_flag == 0 && plw[i].wu.vital_new > 1 && plw[i].wu.vital_new <= VITAL_FULL) {
            plw[i].wu.vital_new--;
        }
    }
}
vital_cont_main_orig();
```

`Allow_a_battle_f` is the flag `Time_Control` uses to run the round clock, so the drain stops before
"Fight!" and after the round ends. `EXE_flag` stops it in the KO slow motion.

**Evidence:** `Game_timer` (u16) counts fight frames in `Game2_1`. A full bar is 160 points
(`VITAL_FULL`), so a full bar drains in 80 seconds; a round lasts 99 counts of 60 frames on the default
timer speed. `sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- The drain stops at 1 point, so it never KOs; the next hit does.
- Both fighters drain the same, so on time over the one who took less damage still wins.
- The red "recent damage" part of the bar should follow the drain, as it does for chip damage.

## Player 2 automatically parries every attack

**Source diff:** `patches/player-2-parries-every-attack.diff`
**BPS:** `sf3_ggpatch/player-2-parries-every-attack/` (simm1.0-.3)
**Changes:** 178 bytes. 06700000-06700093: the new `hit_check_main_process`. 30 bytes outside: its address in
10 literal pools (`Game2_1`, `Loop_Demo`, `Game08`, the bonus stages in `end_sub_*.c` and the
`debug_play*_move` routines).
**Recorded:** 2026-11-15 20:00:29

Tags: `demo-ready` `play-start`

**Mechanism:** A parry ("blocking") is decided in the hit check, from the defender's parry command flags.
`defense_ground` (`src/HITCHECK.c`) parries a high or mid attack when `ds->cp->waza_flag[3]` (forward
tapped) is set, a low one with `waza_flag[4]` (down tapped), and a jump-in with `waza_flag[12]`;
`defense_sky` uses `waza_flag[5]` and `[6]` for air parries. For example:

```c
} else if (ds->cp->waza_flag[3] != 0) {
    blocking_point_count_up(ds);
    as->wu.hf.hit.player = 64;
```

This is a hook on `hit_check_main_process`, which runs the whole hit check at the end of each frame. The
new one sets player 2's five parry flags to 10 (at least the 9 that `blocking_term_tbl` needs for a parry
just after a guard), runs the original, and puts the old values back, so the command code never sees the
change:

```c
wf[3] = wf[4] = wf[5] = wf[6] = wf[12] = 10;
hit_check_main_process_orig();
wf[3] = f3; ...
```

It skips this while `plw[1].cp` is still 0 (before `cmd_init` first runs).

**Evidence:** `waza_flag[3..6, 12]` are only read in `src/HITCHECK.c` and `src/cmd_main_2.c` (where the
command code keeps only the newest parry flag). Projectiles hitting a fighter are judged in the same pass.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Player 2 still can't parry where the game forbids it: while dizzy (`py->flag`), in moves that set the
  `spmv_ng_flag` parry bits, when `guard_flag & 2`, or against attacks whose `att.guard` has no parry
  bits (such as throws).
- Throws: `check_blocking_flag` also reads `waza_flag[3]` and `[4]`, so player 2 counts as "parrying"
  when a throw lands and can't tech it (`hazusenai_flag`).
- Player 2 gets the parry score, Super Art gauge and grade points for every parry.
- Works for player 2 whether human or CPU, including the attract-mode demo.
- Can't be built together with "Every attack hits the opponent no matter where they are" (both hook
  `hit_check_main_process`).

## Can always do a super art

**Source diff:** `patches/can-always-do-a-super-art.diff`
**BPS:** `sf3_ggpatch/can-always-do-a-super-art/` (simm1.0-.3)
**Changes:** 101 bytes. 06700000-06700053: the new `Player_control`. 21 bytes outside: its address in the literal
pools of `Game2_1` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:01:48

Tags: `demo-ready` `play-start`

**Mechanism:** The 3rd Strike version of FF2 "Spells cost no MP in battle" and EarthBound "PSI costs no
PP". Each fighter's gauge is a `SA_WORK` in `super_arts[2]`: `store` is the number of full stocks (up to
`store_max`) and `gauge.s.h` the part-filled bar. When the last stock fills, `add_super_arts_gauge`
(`src/PLSGAUGE.c`) does:

```c
wk->store = wk->store_max;
if (wk->gauge_type == SA_GAUGE_TIMER) {
    wk->gauge.s.h = wk->gauge_len;
} else {
    wk->gauge.i = 0;
}
```

This is a hook on `Player_control` (`src/plcntset_2.c`), which runs both fighters once per fight frame.
The new one does the same as the code above for both fighters, then runs the original. It leaves a
gauge alone while `sa->ok == -1` (a Super Art is running), so the state machines in `sag_normal` and
`sag_timer` (`src/PLMAIN.c`) can finish the art and take the stock; it is refilled on the next frame.
It does nothing in bonus stages (`Bonus_Game_Flag`), where the game gives no gauge either.

**Evidence:** `plw[i].sa` is `&super_arts[i]` (`src/PLCNTDAT.c`). EX moves need `store != 0` or
`gauge.s.h >= 40` (`eag_union`); a full store covers both. `sf3_cheat.py` found no moved code or data.
`git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Both fighters, player or CPU, have full gauges, so the CPU uses Super Arts and EX moves all the time.
- Timer-type arts (`SA_GAUGE_TIMER`, such as Yun's Genei-Jin) still drain while running; the bar is full again as soon as they end.
- The gauge flash and "MAX" lettering should play once when the gauge is first filled, then stay.
- Gill's Resurrection (`SA_GAUGE_REBIRTH`) still works only once per round: after it, `sag_rebirth`
  stays in `SA_REBIRTH`.

## Every hit stuns at once

**Source diff:** `patches/every-hit-stuns.diff`
**BPS:** `sf3_ggpatch/every-hit-stuns/` (simm1.0-.3)
**Changes:** 125 bytes. 06700000-06700073: the new `setup_catch_atthit`, `Player_damage` and
`subtract_dm_vital_aiuchi`. 065EAF89: the `Player_damage` entry of the jump table in `data/PLMAIN_tbl.c`.
06125A01, 06116F05, 06118CF1: the addresses of `setup_catch_atthit` and `subtract_dm_vital_aiuchi` in
the literal pools of `catch_cg_type_check`, `plcnt_move` and `plcnt_b_move` (3 bytes each).
**Recorded:** 2026-11-15 20:04:14

Tags: `demo-ready` `play-start`

**Mechanism:** The 3rd Strike version of EarthBound "Every enemy starts each battle feeling strange". Stun is added to the stun gauge (`py->now.quantity.h`) in three
places, and a fighter becomes dizzy when it reaches `py->genkai`:

```c
} else if (wk->py->flag == 0) {
    wk->py->now.quantity.h += wk->wu.dm_piyo;
    if (wk->py->now.quantity.h >= wk->py->genkai) {
        wk->py->now.timer = 0;
        wk->py->flag = 1;
    }
}
```

That is `subtract_dm_vital` and `subtract_dm_vital_aiuchi` (`src/PLPDM.c`, hits and trades) and
`subtract_cu_vital` (`src/PLPCA.c`, throws). `dm_piyo` is set earlier by the hit check
(`set_damage_and_piyo`, `effect_at_vs_player_dm`) and by `setup_catch_atthit` for throws. Those functions
and `subtract_dm_vital` and `subtract_cu_vital` have short calls from their own files, so the hooks are
on the functions around them, the same three as in "Player 1 never takes damage": `Player_damage`
(reached only from the jump table in `data/PLMAIN_tbl.c`; on the first frame of a hit, before it calls
`subtract_dm_vital`), `subtract_dm_vital_aiuchi`, and `setup_catch_atthit` (after the original). Each does:

```c
if (wk->wu.dm_piyo != 0) {
    wk->wu.dm_piyo = wk->py->genkai;
}
```

Hits that add no stun (guarded and parried hits set `dm_piyo = 0`) are left alone.

**Evidence:** `grep` finds `quantity.h += wk->wu.dm_piyo` only in those three functions. `sf3_cheat.py`
found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Both fighters, player or CPU. The first hit that adds any stun makes the defender dizzy (once they
  land or the combo ends, as for a normal stun).
- While dizzy (`py->flag`), no stun is added, so a dizzy fighter can be hit freely; the next stun
  comes with the first stunning hit after they recover.
- Mashing still shortens the dizzy time as usual.

## Stun never builds up

**Source diff:** `patches/stun-never-builds-up.diff`
**BPS:** `sf3_ggpatch/stun-never-builds-up/` (simm1.0-.3)
**Changes:** 100 bytes. 06700000-06700063: the new `setup_catch_atthit`, `Player_damage` and
`subtract_dm_vital_aiuchi`. 065EAF89: the `Player_damage` entry of the jump table in `data/PLMAIN_tbl.c`.
06125A01, 06116F05, 06118CF1: the addresses of `setup_catch_atthit` and `subtract_dm_vital_aiuchi` in
the literal pools of `catch_cg_type_check`, `plcnt_move` and `plcnt_b_move` (3 bytes each).
**Recorded:** 2026-11-15 20:04:14

Tags: `demo-ready` `play-start`

**Mechanism:** The opposite of "Every hit stuns at once", with the same hooks. Stun is added to the stun gauge (`py->now.quantity.h`) in three
places, and a fighter becomes dizzy when it reaches `py->genkai`:

```c
} else if (wk->py->flag == 0) {
    wk->py->now.quantity.h += wk->wu.dm_piyo;
    if (wk->py->now.quantity.h >= wk->py->genkai) {
        wk->py->now.timer = 0;
        wk->py->flag = 1;
    }
}
```

That is `subtract_dm_vital` and `subtract_dm_vital_aiuchi` (`src/PLPDM.c`, hits and trades) and
`subtract_cu_vital` (`src/PLPCA.c`, throws). `dm_piyo` is set earlier by the hit check
(`set_damage_and_piyo`, `effect_at_vs_player_dm`) and by `setup_catch_atthit` for throws. Those functions
and `subtract_dm_vital` and `subtract_cu_vital` have short calls from their own files, so the hooks are
on the functions around them, the same three as in "Player 1 never takes damage": `Player_damage`
(reached only from the jump table in `data/PLMAIN_tbl.c`; on the first frame of a hit, before it calls
`subtract_dm_vital`), `subtract_dm_vital_aiuchi`, and `setup_catch_atthit` (after the original). Each does:

```c
if (wk->wu.dm_piyo != 0) {
    wk->wu.dm_piyo = 0;
}
```

Hits that add no stun (guarded and parried hits set `dm_piyo = 0`) are left alone.

**Evidence:** `grep` finds `quantity.h += wk->wu.dm_piyo` only in those three functions. `sf3_cheat.py`
found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Both fighters, player or CPU. Nobody can be dizzied, and the stun gauge stays empty.
- This uses the same hooks as "Player 1 never takes damage" and "Every hit stuns at once", so it can't be
  built together with them as is.

## The game runs at half speed

**Source diff:** `patches/half-speed.diff`
**BPS:** `sf3_ggpatch/half-speed/` (simm1.0-.3)
**Changes:** 92 bytes. 06700000-06700047: the new `set_EXE_flag`. 27 bytes outside: its address in the
literal pools of `Game2_1`, `Game08`, `Title` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:05:21

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the half-speed cheats in Tetris, SMB3, Metroid, ALTTP, Super
Metroid and OoT. The KO slow motion works by skipping frames: `set_EXE_flag` (`src/SLOWF.c`) runs at the
start of each fight frame and does

```c
EXE_flag = Game_timer % (SLOW_flag + 1);
```

and fighters, effects, the health bars and the round clock only run when `EXE_flag` is 0. This is a hook:
the new `set_EXE_flag` runs the original, then, when no slow motion is playing (`SLOW_flag == 0`) and the
game isn't paused, sets

```c
EXE_flag = Game_timer % 2;
```

the same as `SLOW_flag` 1. The KO slow motion (`SLOW_flag` 1 and up) is left as it was.

**Evidence:** `EXE_flag` is read by `Player_control`, `vital_cont_main`, `src/count.c` (the round
clock) and over 100 effect routines. The screen, scrolling and sprites still update every frame, as in
the KO slow motion. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Movement is not smoothed: each picture is shown for 2 frames, so it looks choppier than real slow
  motion.
- Input is read every frame, but fighters only act every other frame. Special move timing windows are
  counted in fighter frames, so they feel twice as long.
- Also applies to the attract-mode fight demo (`Title` calls `set_EXE_flag`) and bonus stages.

## Time moves only while any controller input is held

**Source diff:** `patches/time-moves-only-with-input.diff`
**BPS:** `sf3_ggpatch/time-moves-only-with-input/` (simm1.0-.3)
**Changes:** 93 bytes. 06700000-06700043: the new `set_EXE_flag`. 27 bytes outside: its address in the
literal pools of `Game2_1`, `Game08`, `Title` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:06:14

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the "Superhot" cheats (Metroid, SMB3, ALTTP, SMW and SM64: time
moves only while a button is held). It uses the same switch as "The game runs at half speed": objects
only run in a fight frame when `EXE_flag` (set by `set_EXE_flag`, `src/SLOWF.c`) is 0. The new
`set_EXE_flag` runs the original, then stops this frame when neither player touches the lever or a
button:

```c
if (Demo_Flag && ((p1sw_0 | p2sw_0) & 0x3FF) == 0) {
    EXE_flag = 1;
}
```

`p1sw_0` and `p2sw_0` are this frame's inputs (lever bits 0x00F, the six buttons 0x3F0). `Demo_Flag` is 0
in attract mode, so the demo fight still plays.

**Evidence:** `EXE_flag` gates `Player_control`, `vital_cont_main`, the round clock in `src/count.c`
and the effect routines. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Either player's input moves time for both. Against the CPU, the CPU acts only while the human holds
  something.
- The round clock stops too, so a round never times out while nobody touches the controls.
- Start and coin don't count as input.
- Before "Fight!", `Player_control` runs anyway while both fighters are in their set-up step, so the
  intro poses may still play.

## Player 1 freezes the opponent by holding Start

**Source diff:** `patches/p1-start-freezes-player-2.diff`
**BPS:** `sf3_ggpatch/p1-start-freezes-player-2/` (simm1.0-.3)
**Changes:** 37 bytes. 06700000-06700027: the new `player_mv_4000`. 065EAF81: its entry in the
`routine_no[0]` jump table `plmain_lv_00` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-15 20:06:45

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of OoT "Freeze time for enemies by holding L". Start is the only
spare button in a fight. `player_mv_4000` (`src/PLMAIN.c`) is a fighter's whole frame once the round has
started: it reads the lever (or the CPU's virtual lever), runs hit stop or the current state through
`plmain_lv_02[routine_no[1]]`, the timers and the gauges. This is a hook: the new one returns at once for
player 2 while player 1 holds Start:

```c
if (wk->wu.id == 1 && (p1sw_0 & BUTTON_START)) {
    return;
}
player_mv_4000_orig(wk);
```

**Evidence:** `player_mv_4000` is only reached through `plmain_lv_00`. `BUTTON_START` is 0x1000 in
`p1sw_0` (`include/work.h`). `sf3_cheat.py` found no moved code or data. `git apply --check` against
main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Player 2 (human or CPU) stops in place, in mid-air too, with the animation held. Player 2 can still
  be hit: the hit lands, and the reaction plays when Start is let go.
- Player 2's projectiles and other effects keep moving.
- Player 2's inputs are not read while frozen, so a special motion started before can't finish.
- If Start does anything else in a fight on this board, it still does.
- Can't be built together with "The floor is a conveyor belt" (both diffs add to the end of
  `src/PLMAIN.c`).

## Every hit plays the KO slow motion

**Source diff:** `patches/every-hit-plays-ko-slow-motion.diff`
**BPS:** `sf3_ggpatch/every-hit-plays-ko-slow-motion/` (simm1.0-.3)
**Changes:** 58 bytes. 06700000-0670003B: the new `Player_damage`. 065EAF89: its entry in the jump table
`plmain_lv_02` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-15 20:07:23

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of SMW "Bullet Time for Banzai Bill". A KO calls
`set_conclusion_slow` (`src/SLOWF.c`), which sets `SLOW_timer = 95`; `set_EXE_flag` then eases
`SLOW_flag` from slow back to normal through `slow_timer_to_flag` as the timer runs down. This is a hook
on `Player_damage` (`src/PLPDM.c`, the defender's state while hit or guarding, reached only through
`plmain_lv_02`). On the first frame of a clean hit it starts the same slow motion, then runs the original:

```c
if (wk->wu.routine_no[3] == RN3_START && wk->wu.dm_guard_success == -1 && wk->wu.dm_vital != 0) {
    set_conclusion_slow();
}
Player_damage_orig(wk);
```

**Evidence:** the hit check sets `dm_guard_success = -1` for a hit, and the guard or parry number when the
hit was blocked (`src/HITCHECK.c`), so blocked hits and parries don't slow the game. Damage is still 0 at
that point only for hits that do none. `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Each hit restarts the 95-frame slow-down, so a long combo plays in slow motion all the way.
- The round clock also slows while it plays.
- Throws don't go through `Player_damage`, so they don't slow the game (unless they KO).

## Hold Start to pause, press a button to step one frame

**Source diff:** `patches/start-pauses-buttons-step.diff`
**BPS:** `sf3_ggpatch/start-pauses-buttons-step/` (simm1.0-.3)
**Changes:** 111 bytes. 06700000-06700053: the new `set_EXE_flag`. 27 bytes outside: its address in the
literal pools of `Game2_1`, `Game08`, `Title` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:09:40

Tags: `interesting` `demo-ready` `curated` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of ALTTP "L pauses the game, R steps one frame". The board has no L
and R, and Start is the only button a fighter doesn't use, so pausing is "hold player 1's Start" and
stepping is "press any of player 1's six buttons while holding Start". There is no free RAM for a
toggle, which is why Start has to be held. It uses the same switch as "The game runs at half speed":
fight objects only run when `EXE_flag` is 0. The new `set_EXE_flag` (`src/SLOWF.c`) runs the original,
then:

```c
if (Demo_Flag && (p1sw_0 & BUTTON_START)) {
    if (~p1sw_1 & p1sw_0 & BUTTON_SHOTS) {
        EXE_flag = 0;       /* a button went down this frame: run one frame */
    } else {
        EXE_flag = 1;       /* paused */
    }
}
```

**Evidence:** `p1sw_0` / `p1sw_1` are this and last frame's inputs, `BUTTON_START` 0x1000 and
`BUTTON_SHOTS` 0x3F0 (`include/work.h`). `EXE_flag` gates `Player_control`, the health bars, the round
clock and the effects. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- The button that steps a frame is also a real press for player 1's fighter in that frame (it may start
  an attack). Pressing a button player 1's fighter is already holding doesn't step.
- A step also runs a frame that the KO slow motion would have skipped.
- Off in attract mode (`Demo_Flag` is 0).
- The screen still updates while paused (the camera and stage animation may still move).

## Fighters walk twice as fast

**Source diff:** `patches/fighters-walk-twice-as-fast.diff`
**BPS:** `sf3_ggpatch/fighters-walk-twice-as-fast/` (simm1.0-.3)
**Changes:** 112 bytes. 06700000-0670006B: the new `Normal_03000` and `Normal_04000`. 065EBB41, 065EBB45:
their entries in the `routine_no[2]` jump table `plpnm_lv_00` (`data/PLPNM_tbl.c`).
**Recorded:** 2026-11-15 20:10:39

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the "runs twice as fast" cheats (Ness, Link, Cecil, SM64 Mario,
SMB2). `check_F_R_walk` (`src/PLS01.c`) starts a walk with `routine_no[2]` 3 (forward) or 4 (back).
Those states, `Normal_03000` and `Normal_04000` (`src/PLNORMAL.c`), move the fighter by the walk
speed from the character's move data each frame:

```c
case N03_MOVE:
    cal_mvxy_speed(&wk->wu);
    add_mvxy_speed(&wk->wu);
    char_move(&wk->wu);
```

These are hooks: the new ones run the original, then, if the fighter is still walking, call
`add_mvxy_speed` (`src/PLS02.c`) once more, which adds the same speed to the position again.

**Evidence:** both states are reached only through `plpnm_lv_00`. `add_mvxy_speed` adds `mvxy.a[0].sp`
to `xyz[0].cal` in the facing direction, and `mvxy.a[1].sp` (0 for a walk) to the height.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- The walk animation plays at its normal rate, so fighters slide a little.
- Both fighters, player or CPU. Dashes, jumps and the steps of moves are not changed.
- Characters whose walk is not states 3 and 4 (if any) are not changed.
- Can't be built together with "Low gravity: jumps go twice as high" (both diffs add to the end of
  `src/PLNORMAL.c`).
- Can't be built together with "The CPU opponent walks twice as fast" (same file end in `src/PLNORMAL.c`).

## Jump again in mid-air

**Source diff:** `patches/jump-again-in-mid-air.diff`
**BPS:** `sf3_ggpatch/jump-again-in-mid-air/` (simm1.0-.3)
**Changes:** 149 bytes. 06700000-0670009B: the new `check_air_jump`. 0611B5A9: its address in the
literal pool of `nm_18000`.
**Recorded:** 2026-11-15 20:12:08

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the Metroid, SMB2, SMB3 and Super Metroid "Jump again in
mid-air". `nm_18000` (`src/PLS00.c`) checks a jumping fighter's inputs each frame, and last calls
`check_air_jump` (`src/PLS01.c`). That starts the air jump only for the characters that have one
(`spmv_ng_table` bit 0x80000 clear), once per jump (`extra_jump`), and only above height 48:

```c
if (wk->spmv_ng_flag & 0x80000) return 0;
if (wk->extra_jump) return 0;
...
wk->wu.routine_no[2] = 53;
```

This is a hook. The new `check_air_jump` runs the original first, so a character with its own air jump
still does it. Otherwise, while jumping (`pat_status` 20-30) a new press of up (`cp->sw_now &
CMD_LV_UP`) starts a new jump from where the fighter is: `routine_no[2]` 21, 22 or 23 (forward,
straight, back, the same states `Normal_53000` goes to after its air jump) with `routine_no[3]` at
`RN3_START`, so `Normal_18000` sets up the jump's animation and full speed again. It uses the lever
direction the same way `Normal_53000` does (`check_jump_rl_dir`).

**Evidence:** `check_air_jump` is only called from `nm_18000` in `src/PLS00.c`. `cp->sw_now` is the
newly pressed inputs (`sw_0 & ~sw_old`, `src/cmd_main_2.c`). `Normal_18000` is states 18-26 in
`plpnm_lv_00`, and uses `jpdat_tbl`, which is shared by all characters. `sf3_cheat.py` found no moved
code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- No limit: pressing up again and again climbs to the top of the screen.
- Only when `nm_18000` gets to `check_air_jump`: not during an air attack, and an attack or special
  input in the same frame comes first. Up must be pressed again (holding it does nothing).
- Both fighters, player or CPU (the CPU rarely presses up in the air).
- There is no jump-start (squat) animation in the air; the jump animation restarts.

## Low gravity: jumps go twice as high

**Source diff:** `patches/low-gravity.diff`
**BPS:** `sf3_ggpatch/low-gravity/` (simm1.0-.3)
**Changes:** 76 bytes. 06700000-06700033: the new `Normal_18000`. 065EBB7D-065EBB9D: its 9 entries
(states 18-26) in the `routine_no[2]` jump table `plpnm_lv_00` (`data/PLPNM_tbl.c`).
**Recorded:** 2026-11-15 20:12:50

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of SMB3 "Low gravity" and Super Metroid "Samus jumps much higher".
Every jump (states 18-26) starts in `Normal_18000` (`src/PLNORMAL.c`), which reads the jump's speeds
from the character's move data:

```c
case RN3_START:
    ...
    setup_mvxy_data(&wk->wu, jpdat_tbl[wk->wu.routine_no[2] - 18][1]);
    add_mvxy_speed(&wk->wu);
```

`mvxy.a[1].sp` is the up speed and `mvxy.d[1].sp` is what `cal_mvxy_speed` (`src/PLS02.c`) adds to it
each frame (gravity, a negative number). This is a hook: the new `Normal_18000` runs the original, and
on the jump's first frame halves `mvxy.d[1].sp`. With the same take-off speed and half the gravity, a
jump goes twice as high and stays in the air twice as long.

**Evidence:** `Normal_18000` is reached only through `plpnm_lv_00`. Landing is found by height
(`jumping_union_process` in `src/PLS01.c`), not by animation time. `sf3_cheat.py` found no moved code
or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Both fighters. Normal, high and super jumps; not air jumps, wall jumps, jumping specials or being
  knocked into the air.
- The jump animation may reach its end before landing and hold its last frame.
- An attack in the air keeps the low gravity unless the move sets its own speeds.
- Jumps may go above the top of the screen.
- Can't be built together with "Fighters walk twice as fast" (both diffs add to the end of
  `src/PLNORMAL.c`).
- Can't be built together with "The CPU opponent walks twice as fast" (same file end in `src/PLNORMAL.c`).

## Fighters face away from each other

**Source diff:** `patches/fighters-face-away.diff`
**BPS:** `sf3_ggpatch/fighters-face-away/` (simm1.0-.3)
**Changes:** 06700000-0670002B: the new `set_rl_waza`. 0611788D, 06118FE1: its address in the literal
pools of `move_player_work` and `move_player_work_bonus`. 0611D0C0-0611D0C5: `check_hurimuki` (in place).
**Recorded:** 2026-11-15 20:13:35

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the "Enemies face away" cheats (SMB2, SMB3, ALTTP, SMW, OoT).
Each frame `set_rl_waza` (`src/PLS01.c`) works out which way each fighter should face (`rl_waza`), from
where the opponent is:

```c
dx = wk->wu.xyz[0].disp.pos - em->wu.xyz[0].disp.pos;
if (dx > 0) wk->wu.rl_waza = 0; else wk->wu.rl_waza = 1;
```

When `rl_waza` differs from the facing flag `rl_flag`, the fighter turns round (`check_rl_flag`,
`check_hurimuki`). This is a hook: the new `set_rl_waza` runs the original, then flips `rl_waza`
(`^= 1`), so each fighter turns to face away from the other.

A second check, `check_hurimuki` (`src/PLS01.c`), decides when a standing, walking or crouching
fighter turns round (`check_turn_to_back`). It works out the facing from the positions itself, not
from `rl_waza`:

```c
s16 result = wk->xyz[0].disp.pos - em->old_pos[0];
```

With only `rl_waza` flipped, the two disagreed: one turned the fighter away and the other turned
them back, so the fighters flickered between facings. The subtraction is now the other way round
(`em->old_pos[0] - wk->xyz[0].disp.pos`, in place, same size), so `check_hurimuki` agrees with the
flipped `rl_waza`. The flip now also applies in the bonus stages, except the car stage, which has
its own facing code; `check_hurimuki` is not used there.

(Fixed on 2026-11-15: the first version flipped only `rl_waza`, and the fighters flickered.)

**Evidence:** `set_rl_waza` is only called from `src/PLCNT2.c` and `src/plcntset_2.c`, for both
fighters each frame. In the car stage (`BONUS_CAR`) it uses the lever, so the flip is skipped there.
`check_hurimuki` is only called from `check_turn_to_back`.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- "Forward" is away from the opponent, so walking, dashing, blocking and motion inputs are mirrored.
  Projectiles fly away from the opponent. Back-facing attacks and crossed-up jumps can still hit.
- Both fighters, player or CPU. The CPU may play badly.
- Moves that set the facing themselves (some throws, intros and win poses) may face the usual way for
  a moment.
- After being hit, a fighter is set to face the attacker (from the hit's direction, `dm_rl`), then
  turns away again: one turn, not a flicker.
- The CPU's own facing checks (`src/Com_Sub.c`) are not changed.

## Fighters walk through each other

**Source diff:** `patches/fighters-walk-through-each-other.diff`
**BPS:** `sf3_ggpatch/fighters-walk-through-each-other/` (simm1.0-.3)
**Changes:** 26 bytes. 06700000-06700017: the new `check_body_touch`. 0611684D, 06118939: its address in
the literal pools of `Player_control` and `Player_control_bonus`.
**Recorded:** 2026-11-15 20:14:16

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of EarthBound "Ness walks through people" and ALTTP "Enemies pass
through Link". Each fight frame `check_body_touch` (`src/PLS02.c`) checks whether the two fighters'
push boxes (`h_hos->hos_box[0]`) overlap, and if so moves them apart:

```c
meri = hit_check_subroutine(&p1w->wu, &p2w->wu, &p1w->wu.h_hos->hos_box[0], &p2w->wu.h_hos->hos_box[0]);
...
p1w->wu.xyz[0].disp.pos += meri * (p1w->micchaku_flag != 1);
p2w->wu.xyz[0].disp.pos -= meri * (p2w->micchaku_flag != 2);
```

This is a hook that replaces it: the new `check_body_touch` only does what the original does when the
boxes don't overlap (`hos_em_flag = 0` for both), so the fighters are never pushed apart.

**Evidence:** `check_body_touch` is only called from `Player_control` (`src/plcntset_2.c`) and
`Player_control_bonus` (`src/PLCNT2.c`). The bonus stage with the car uses `check_body_touch2`,
which is not changed. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Fighters can stand in the same place and walk past each other; they then turn round as after a jump
  over.
- Hits still push the fighters apart (`check_damage_hosei`, not changed).
- A fighter in the corner can't be pushed out by the other's body, and the other can walk into the
  corner past them.

## Slippery floors: fighters slide after walking, dashing, jumping and getting hit, and sometimes fall

**Source diff:** `patches/slippery-floors.diff`
**BPS:** `sf3_ggpatch/slippery-floors/` (simm1.0-.3)
**Changes:** 559 bytes. 06700000-0670023D: the new `player_mv_4000`. 065EAF81: its entry in the
`routine_no[0]` jump table `plmain_lv_00` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-15 20:15:30

Tags: `interesting` `demo-ready` `curated` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the SMB2, SMB3, ALTTP and OoT "slippery floors" cheats.
`player_mv_4000` (`src/PLMAIN.c`) runs a fighter for one frame of the fight (standing, walking,
jumping, attacking, being hit), through `plmain_lv_02[routine_no[1]]`. This is a hook: the new
`player_mv_4000` notes the position (`xyz[0].cal`, 16.16), runs the original, and works out how far
the game moved the fighter sideways this frame. On the ground, it moves the fighter by its own speed
instead (kept in `pt_free[8-9]`, an unused part of the player work, in 1/256 pixels a frame). That
speed eases toward the game's movement by 1/16 of the difference a frame, when speeding up, slowing
down or turning alike. In the air, the speed just follows the
game's movement, so a landing carries the jump's speed into the slide.

Over time the fighter covers the same distance as without the cheat, just later: a steady walk
gives the same walking speed. From a standstill the fighter speeds up into the walk over about
a second, and after a stop slides on and comes to rest.

(Rewritten on 2026-11-16. The first version hooked only the standing state, `Normal_01000`, and
slid with the last `mvxy` speed. Walking moves by animation steps (`cg_add_xy`, `char_move` in
`src/CHARMOVE.c`), not by `mvxy`, and a landing goes through its own state first, so the fighter
stopped dead and then slid off. Changed again the same day: speeding up first used 1/4 of the
difference a frame; now it is 1/16 like slowing down, so walks start slowly too.)

**Falls (added 2026-11-17):** the hook also notes `routine_no[1]`, `routine_no[2]` and the height
(`xyz[1].disp.pos`) before running the original. A fall can happen when, in that frame:

- a fighter in the normal state (`PLAYER_NORMAL`), or in a normal jump attack (`PLAYER_ATTACK`
  with `routine_no[2] < ATTACK_SPECIAL`), goes from the air to the ground: a landing from a jump,
  a jump attack, an air block or a back dash that leaves the ground; or
- a fighter in a forward or back dash (`PLAYER_NORMAL`, `routine_no[2]` 5 or 6, `Normal_05000` /
  `Normal_06000`) leaves the dash state while still on the ground.

The roll uses each fighter's own random number, kept in `pt_free[10-11]`: a 16-bit LCG, `r = r *
25173 + 13849 + system_timer`, and a fall when `(r >> 8) < 13` (13 of 256, about 1 in 20). The first
version used the CPU's random table (`random_32_com`, `src/PLS02.c`, two calls in a row). Only 10 of
its 128 positions gave a fall, and the CPU's AI moves through that table on its own schedule, so a
fighter could go a long time without falling: the user saw only the CPU fall (2026-11-17). Changed
the same day. On a hit, the fighter is put in the damage state the way `setup_kuzureochi`
(`src/PLPDM.c`) does it, with damage reaction 89, the one a sweep uses (Ryu's `KAGAMI K A`,
`data/ryu_attr.c` row 25). On the next frame `Player_damage` runs `get_damage_reaction_data`, which
picks `dm_reaction_table[89]` (`Damage_16000`, knocked off the feet, then down and getting up). The
hook fills in what a hit would: `dmg_adrs` = the other fighter, `dm_attlv` 2, `dm_butt_type` 1,
`dm_plnum` = the fighter's own player number (for `parabora_own_table`), `dm_zuru` 7, `dm_koa` 0
(quick rise allowed), `dm_rl` set so the fighter keeps facing the same way and falls backward, and
no hit stop or shake. `dm_vital` is set to 0 so `subtract_dm_vital` adds no score; the hook takes 6
off `vital_new` itself (chip damage, about the chip of a heavy special; full life is 160 or 192),
but never below 0, so a fall can't KO.

Only while `Allow_a_battle_f` is set and neither fighter is KO'd (`dead_flag`), not during a
parry (`atemi_flag`) or hit stop.

**Evidence:** `player_mv_4000` is only called through `plmain_lv_00` (`data/PLMAIN_tbl.c`).
`check_lever_data` (input) and the state routine both run inside it, before `move_player_work`
(`src/plcntset_2.c`) pushes the fighters apart and keeps them on screen, so walls and the other
fighter still stop a slide. Not during hit stop (`hit_stop`, `dm_stop`; the speed is kept), not
while throwing or being thrown (`tsukami_f`, `tsukamare_f`; the speed is cleared), and not in bonus
stages. A jump of more than 32 pixels in one frame (a reset of the position) clears the speed.
No source uses `pt_free`. `sf3_cheat.py` found no moved code or data. `git apply --check` against
main: applies. For the falls: `Player_damage`, `get_damage_reaction_data`, `subtract_dm_vital`,
`check_bullet_damage`, `Damage_16000`, `buttobi_add_y_check`, `setup_butt_own_data`
(`src/PLS02.c`), `get_sky_dm_timer`, `dm_reaction_table` and `plpdm_lv_00`
(`data/PLPDM_tbl.c`), `add_arts_gauge` (`data/gauge.c`), `Max_vitality` (`src/mode_init.c`).

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works, including the falls.
- A fall comes one frame after the landing or dash end, so the landing pose may show for a frame.
- Both fighters, player or CPU, can fall.
- The fall is a damage state: it can be juggled or hit on the ground like after a real sweep, and
  it counts as a hit for anything that checks the damage state. It doesn't add to the combo
  counter.
- A dash cut short by an attack doesn't roll (the fighter leaves the normal state).
- Every ground movement is smoothed: walks, dashes, attacks that step forward, and pushback from
  hits and blocks. Dashes start much slower and slide further: a short dash may be mostly slide. Attacks that step forward may whiff
  where they used to hit.
- A fighter who reverses direction slides the old way for a moment first.
- Both fighters, player or CPU.
- Can't be built together with "Each fighter's movement moves the other fighter", "The floor is a
  conveyor belt" or other cheats that add to the end of `src/PLMAIN.c`, without merging the diffs
  by hand.

## The floor is a conveyor belt

**Source diff:** `patches/conveyor-belt-floor.diff`
**BPS:** `sf3_ggpatch/conveyor-belt-floor/` (simm1.0-.3)
**Changes:** 75 bytes. 06700000-06700047: the new `Player_move`. 06117989, 06117AB9: its address in the
literal pools near `move_P1_move_P2` and `check_damage_hosei` (used by the inlined `move_P1_move_P2`
and `move_P2_move_P1`).
**Recorded:** 2026-11-15 20:16:33

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the SMB2, SMB3 and ALTTP "conveyor belt" cheats. Each fight
frame `move_player_work` (`src/plcntset_2.c`) runs `Player_move` (`src/PLMAIN.c`) for each fighter,
then keeps them inside the screen:

```c
Player_move(&plw[0], processed_lvbt(p1sw_0));
if (bg_app_stop == 0 && bg_app == 0) {
    if (set_field_hosei_flag(&plw[0], scrr, 1)) {
        set_field_hosei_flag(&plw[0], scrl, 0);
```

This is a hook: the new `Player_move` moves a fighter who is on the ground 4 pixels to the right
(`xyz[0].disp.pos += 4`) every frame, then runs the original. The screen-edge check after it
stops them at the right edge.

**Evidence:** `Player_move` is only called from `src/plcntset_2.c`. A larger `xyz[0].disp.pos` is
further right (`set_field_hosei_flag` with `ix` 1 clamps against the right edge `scrr`). Only during
a battle (`Allow_a_battle_f`), not in bonus stages, not in the air, and not while throwing or being
thrown (`tsukami_f`, `tsukamare_f`). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Always to the right, at 4 pixels a frame (240 pixels a second). That is about as fast as a walk,
  so walking left barely moves or loses ground, and walking right is about twice as fast. Dashing
  or jumping is the way to go left.
- The camera follows, so both fighters drift to the right end of the stage and stay pinned there.
- Also moves fighters who are knocked down, stunned or in the KO animation, as long as they are on the
  ground.
- Can't be built together with "Player 1 freezes the opponent by holding Start" (both diffs add to the
  end of `src/PLMAIN.c`).
- Speed changed on 2026-11-16 from 1 pixel every other frame (30 pixels a second, which the user
  found too slow) to 8 times that. Not tested at the new speed.

## Every attack hits the opponent no matter where they are

**Source diff:** `patches/every-attack-hits-anywhere.diff`
**BPS:** `sf3_ggpatch/every-attack-hits-anywhere/` (simm1.0-.3)
**Changes:** 439 bytes. 06700000-067001A7: the new `hit_check_main_process`. 30 bytes outside: its
address in the literal pools of `Loop_Demo`, `Game2_3`, `Game08` and the `debug_play*_move`
routines.
**Recorded:** 2026-11-15 20:18:01

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of Zelda 1 "Sword hits every enemy on the screen" and the ALTTP and
OoT "Sword hits enemies across most of the screen". Once a frame `hit_check_main_process`
(`src/HITCHECK.c`) runs `attack_hit_check`, which tests each active attack box (`h_att->att_box`)
against the opponent's body and hand boxes with `hit_check_subroutine`. That places each box at the
work's position `xyz[0]`, `xyz[1]`:

```c
d0 = *hd1++;
d1 = *hd1++;
if (wk1->rl_flag) { d0 = -d0; d0 -= d1; }
d0 += wk1->xyz[0].disp.pos;
```

This is a hook. Before running the original, the new `hit_check_main_process` looks for a fighter
whose attack is active (`cg_ja.atix` and `att_hit_ok` set). It moves that fighter so the centre of
their first attack box is on the centre of the opponent's first body box (`h_bod->body_dm[0]`), in
both x and height. After the original, it puts the fighter back where they were, unless the hit check
itself moved them.

**Evidence:** `hit_check_main_process` is only called from other files (`src/Game_Main.c`, the
`debug_play` routines). Box layout (x, width, y, height) from `hit_check_subroutine` and
`include/structs.h`. The hit check doesn't draw anything, and the drawing position (`position_x`) was
already set by `add_next_position` in `Player_control`, earlier in the frame. Only during a battle (`Allow_a_battle_f`) and not in
bonus stages. `sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Both fighters, player or CPU. If both attack in the same frame, only player 1's attack is moved.
- The hit spark appears on the opponent, but the attacker stays far away. Pushback after a hit works
  from the real distance.
- Blocking and parrying still work, and so do the usual rules (a low attack can still be jumped; an
  attack still needs the opponent to be hittable).
- Projectiles are not changed. The moved fighter can't be hit by projectiles in that frame where they
  really are.
- Can't be built together with "Player 2 automatically parries every attack" (both hook
  `hit_check_main_process`).

## Every throw grabs the opponent no matter where they are

**Source diff:** `patches/every-throw-grabs-anywhere.diff`
**BPS:** `sf3_ggpatch/every-throw-grabs-anywhere/` (simm1.0-.3)
**Changes:** 409 bytes. The new `hit_check_main_process` at 06700000. 30 bytes outside: its address in
the literal pools of `Loop_Demo`, `Game2_3`, `Game08` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:19:01

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The throw version of "Every attack hits the opponent no matter where they are" (same
idea). `hit_check_main_process` (`src/HITCHECK.c`) runs `catch_hit_check` when `ca_check_flag` is
set, which tests a fighter's throw box (`h_cat->cat_box`) against the opponent's "can be thrown" box
(`h_cau->cau_box`):

```c
mh = &mad->h_cat->cat_box[0];
...
sh = &sad->h_cau->cau_box[0];
...
if (hit_check_subroutine(mad, sad, mh, sh)) {
```

This is a hook. Before running the original, the new `hit_check_main_process` looks for a fighter
with an active throw box (`att_hit_ok` set and a box of non-zero width). It moves that fighter so the
centre of the throw box is on the centre of the opponent's box, in both x and height. After the
original, it puts the fighter back, unless the hit check moved them. Once a throw has caught, the
thrown fighter is placed next to the thrower each frame (`catch_hos_x` in `src/PLPCU.c`), so they are
pulled across the screen.

**Evidence:** `hit_check_main_process` is only called from other files. Only during a battle
(`Allow_a_battle_f`) and not in bonus stages. The rules in `catch_hit_check` still apply (can't throw
a fighter in hit stun, `tsukamarenai_flag`, and so on). `sf3_cheat.py` found no moved code or data.
`git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Both fighters, player or CPU. If both throw in the same frame, only player 1's throw is moved.
- Throws include command grabs (Hugo, Alex) and air throws. A normal throw input is still needed: the
  game only makes a throw box when the throw starts, and some characters' throw inputs may do a normal
  attack when far away.
- The thrown fighter may jump across the screen in one frame.
- Can't be built together with the other cheats that hook `hit_check_main_process` ("Player 2
  automatically parries every attack", "Every attack hits the opponent no matter where they are").

## Projectiles fly twice as fast

**Source diff:** `patches/projectiles-fly-twice-as-fast.diff`
**BPS:** `sf3_ggpatch/projectiles-fly-twice-as-fast/` (simm1.0-.3)
**Changes:** 148 bytes. 06700000-06700097: the new `effect_13_move`. 061B8871: its entry in the effect
jump table `effmovejptbl` (`data/EFFECT_tbl.c`).
**Recorded:** 2026-11-15 20:20:25

Tags: `demo-ready` `curated` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the SMB1, SMB3, SMW, ALTTP and Zelda 1 "fly twice as fast"
cheats. Projectiles are effect 13 (`src/EFF13.c`, see "Worked example: Ryu throws a fireball" in
`docs/HOW_THE_GAME_WORKS.md`). Each frame `effect_13_move` runs the shell's own process from
`kind_of_tama_process`; most of them move the shell in their flight state like `kotp_00000`:

```c
case R1_MOVE:
    ...
    } else {
        add_mvxy_speed(&ewk->wu);
    }
    cal_mvxy_speed(&ewk->wu);
```

This is a hook: the new `effect_13_move` runs the original, and if the shell is still in flight
(`routine_no[1] == R1_MOVE`, no hit stop) and is a kind whose flight step is `add_mvxy_speed`
(kinds 0, 3, 5-9, 12, 15 and 16), calls `add_mvxy_speed` once more, so it moves twice as far each
frame.

**Evidence:** `effect_13_move` is reached only through `effmovejptbl`. The kinds were found by reading
each `kotp_*` routine's `R1_MOVE` case. Only on frames where the original moved the shell
(`EXE_flag` and `Game_pause` clear). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Both fighters' projectiles. Kinds 1, 2 (the tengu stones), 4, 10, 11, 13 and 14 are not changed;
  which characters use which kind was not checked.
- The animation runs at its normal rate. A shell's lifetime is in frames, so slow shells that end by
  time go twice as far.
- Homing shells (kind 6) turn at their normal rate, so they may miss more.
- Can't be built together with "Projectiles stay where they appear" (both hook `effect_13_move`).

## Projectiles stay where they appear

**Source diff:** `patches/projectiles-stay-where-they-appear.diff`
**BPS:** `sf3_ggpatch/projectiles-stay-where-they-appear/` (simm1.0-.3)
**Changes:** 97 bytes. 06700000-06700060: the new `effect_13_move`. 061B8871: its entry in the effect
jump table `effmovejptbl` (`data/EFFECT_tbl.c`).
**Recorded:** 2026-11-15 20:21:21

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of ALTTP "Sword beams stay where they appear". Same place as
"Projectiles fly twice as fast": each frame `effect_13_move` (`src/EFF13.c`) runs the shell's process,
which moves it in its flight state (`routine_no[1] == R1_MOVE`). This is a hook: the new
`effect_13_move` saves the shell's position (`xyz[0].cal`, `xyz[1].cal`), runs the original, and if
the shell was and still is in flight, puts the position back. The shell still animates, counts down
its lifetime and can hit.

**Evidence:** `effect_13_move` is reached only through `effmovejptbl`. The hit, end and explosion
states (`R1_HIT`, `R1_VANISH`) are not changed, so a shell that hits or runs out plays its end
pattern as usual. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- A fireball hangs in front of the fighter who threw it until it hits or its lifetime ends (999
  frames, about 16 seconds, for Ryu's). Most characters can't throw another one until then.
- All kinds of shell, including ones that work differently (Oro's tengu stones, falling shells); those
  stay where they are made too, which may look odd.
- Can't be built together with "Projectiles fly twice as fast" (both hook `effect_13_move`).

## Projectiles pass through each other

**Source diff:** `patches/projectiles-pass-through-each-other.diff`
**BPS:** `sf3_ggpatch/projectiles-pass-through-each-other/` (simm1.0-.3)
**Changes:** 70 bytes. 06700000-06700047: the new `effect_at_vs_effect_dm`. 0608D019: its address in the
literal pool after `cal_hit_mark_pos` (used by `set_struck_status`).
**Recorded:** 2026-11-15 20:22:17

**Mechanism:** The 3rd Strike version of the SMB1, SMB3, SMW and ALTTP "fly through enemies" cheats.
When `attack_hit_check` finds one effect's attack box on another effect, `set_struck_status`
(`src/HITCHECK.c`) calls `effect_at_vs_effect_dm` (`src/HITEFEF.c`). For two projectiles it trades
their power, so both usually vanish:

```c
} else if (ds->wu.id == 13) {
    switch (as->wu.work_id) {
    case 4:
        ds->wu.dm_vital = as->wu.vital_new;
        as->wu.dm_vital = ds->wu.vital_new;
```

and then sets the hit state (`routine_no[1] = 1`, hit stop 6). This is a hook: when both works are
projectiles (effect id 13), the new `effect_at_vs_effect_dm` does none of that and sets the attacking
shell's `att_hit_ok` back to 1 (`attack_hit_check` cleared it), so it can still hit the opponent.
Otherwise it runs the original.

**Evidence:** `effect_at_vs_effect_dm` is only called from `set_struck_status`. `effect_13_init` sets
`wu.id = 13` (`src/EFF13.c`). `sf3_cheat.py` found no moved code or data. `git apply --check` against
main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- In the frame the two meet, the hit check has already used up that frame's hit for both shells, so
  a shell that is touching the opponent and the other shell at once hits the opponent one frame late.
- Other effects that can hit projectiles (not effect 13) still stop them.

## No knockback from hits

**Source diff:** `patches/no-knockback-from-hits.diff`
**BPS:** `sf3_ggpatch/no-knockback-from-hits/` (simm1.0-.3)
**Changes:** 68 bytes. 06700000-06700043: the new `Player_damage`. 065EAF89: its entry in the
`routine_no[1]` jump table `plmain_lv_02` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-15 20:23:17

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** A fighter who is hit or blocks goes to `routine_no[1] = PLAYER_DAMAGE` (`set_struck_status`
and `set_guard_status` in `src/HITCHECK.c`), and `Player_damage` (`src/PLPDM.c`) runs the reaction,
whose movement data slides them away from the attacker. This is a hook: the new `Player_damage` saves
the fighter's sideways position (`xyz[0].cal`), runs the original, and if the fighter was and still is
on the ground and still in `PLAYER_DAMAGE`, puts the position back. So ground hits and blocks don't
push the fighter away.

**Evidence:** `Player_damage` is reached only through `plmain_lv_02`. Blocking is also
`PLAYER_DAMAGE` (`set_guard_status`). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Both fighters. Hits that launch still send the fighter flying (in the air the position isn't put
  back). A knocked-down fighter doesn't slide along the ground.
- The attacker still gets pushed back when the opponent is in the corner.
- Without knockback, combos and blockstrings stay at close range, so some moves combo that normally
  don't, and the opponent can't be pushed out of range.
- Can't be built together with the other cheats that hook `Player_damage` ("Player 1 never takes
  damage", "Every hit stuns at once", "Stun never builds up", "Every hit plays the KO slow motion").

## Blocking works holding either way

**Source diff:** `patches/block-holding-either-way.diff`
**BPS:** `sf3_ggpatch/block-holding-either-way/` (simm1.0-.3)
**Changes:** 33 bytes. 06700000-0670001B: the new `get_guard_direction`. 0608CB7D, 0608EE89, 0608F0F9: its
address in the literal pools of `set_caught_status`, `player_at_vs_player_dm` and
`effect_at_vs_player_dm`.
**Recorded:** 2026-11-15 20:25:06

Tags: `demo-ready` `play-start`

**Mechanism:** The 3rd Strike version of Zelda 1 and ALTTP "Shield blocks shots from any direction". When
a hit lands, `get_guard_direction` (`src/PLS02.c`) works out which way the defender must hold the
lever to block: 1 or 2 (away from the attacker), or 3 (either way). `defense_ground` and
`defense_sky` (`src/HITCHECK.c`) then test it against the lever (`saishin_lvdir`, 1 back or 2
forward):

```c
if (ds->saishin_lvdir & gddir) {
    as->wu.hf.hit.player = 0x20;
    ds->wu.routine_no[2] = 7;
```

This is a hook: the new `get_guard_direction` always returns 3, so holding the lever either way
(toward or away from the attacker, or the wrong way on a cross-up) blocks. The original already
returns 3 for a projectile that comes from behind.

**Evidence:** `get_guard_direction` is called from `src/HITCHECK.c`, `src/HITPLPL.c` and
`src/HITEFPL.c` only. Its result (`gddir`) is only used for the guard tests and
`check_guard_miss` (`src/Grade.c`, the grade's "missed a block" count). Not in bonus stages.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Both fighters, player or CPU.
- The fighter still needs to be able to block (not attacking or in the air without air block), and
  high/low still matters.
- Walking forward toward an attack now blocks it, so it is much harder to hit a fighter who is moving
  at all.

## The CPU opponent stands still

**Source diff:** `patches/cpu-stands-still.diff`
**BPS:** `sf3_ggpatch/cpu-stands-still/` (simm1.0-.3)
**Changes:** 39 bytes. The new `CPU_Sub` at 06700000. 06119639: its address in the literal pool of
`Player_move`.
**Recorded:** 2026-11-15 20:26:21

**Mechanism:** The 3rd Strike version of Metroid "Enemies can't move", EarthBound "Enemies on the map
can't move" and SMW "Every Chargin' Chuck stands there and does nothing". `Player_move`
(`src/PLMAIN.c`) gets a CPU fighter's input from `CPU_Sub` (`src/Com_Pl.c`), which runs the AI:

```c
if (wk->wu.operator) {
    wk->cp->sw_lvbt = lv_data;
} else {
    wk->cp->sw_lvbt = processed_lvbt(CPU_Sub(wk));
}
```

This is a hook: in a paid game (`Demo_Flag` set) and outside bonus stages, the new `CPU_Sub` returns 0
(no lever, no buttons) without running the AI. Otherwise it runs the original.

**Evidence:** `CPU_Sub` is only called from `Player_move`. The CPU's moves all come from this input
word; the original also returns 0 when the fight doesn't allow input (`Allow_a_battle_f`).
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- The CPU never blocks, parries, attacks, gets up quickly or techs throws.
- Gill's resurrection and other automatic things that don't need input still happen.
- The attract-mode demo and the bonus stages play as usual.
- Can't be built together with "The CPU opponent keeps running away" (both hook `CPU_Sub`).

## The CPU opponent keeps running away

**Source diff:** `patches/cpu-keeps-running-away.diff`
**BPS:** `sf3_ggpatch/cpu-keeps-running-away/` (simm1.0-.3)
**Changes:** 81 bytes. The new `CPU_Sub` at 06700000. 06119639: its address in the literal pool of
`Player_move`.
**Recorded:** 2026-11-15 20:26:54

**Mechanism:** The 3rd Strike version of EarthBound "Enemies on the map always run away from Ness" and
SMB2 "Enemies face and walk away". Same place as "The CPU opponent stands still": `CPU_Sub`
(`src/Com_Pl.c`) gives `Player_move` the CPU's input for the frame. This is a hook: in a paid game
(`Demo_Flag` set), outside bonus stages, and while the fight allows input (the same
`Allow_a_battle_f` and `pcon_dp_flag` test the original starts with), the new `CPU_Sub` returns
`LEVER_LEFT` if the CPU is left of its opponent and `LEVER_RIGHT` otherwise, without running the AI.

**Evidence:** `CPU_Sub` is only called from `Player_move`, which passes its result through
`processed_lvbt` like a player's `p1sw_0`. Lever bits from `include/work.h`. `sf3_cheat.py` found no
moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- The CPU walks backward until it reaches the edge of the screen, then stays there.
- Holding back also blocks, so the CPU blocks every high and mid attack (but not lows or throws).
- Can't be built together with "The CPU opponent stands still" (both hook `CPU_Sub`).
- The attract-mode demo and the bonus stages play as usual.

## The CPU opponent walks twice as fast

**Source diff:** `patches/cpu-walks-twice-as-fast.diff`
**BPS:** `sf3_ggpatch/cpu-walks-twice-as-fast/` (simm1.0-.3)
**Changes:** 144 bytes. The new `Normal_03000` and `Normal_04000` at 06700000. 065EBB41 and 065EBB45: their
addresses in the jump table `plpnm_lv_00`.
**Recorded:** 2026-11-15 20:27:34

**Mechanism:** The 3rd Strike version of Metroid "Most enemies move twice as fast" and ALTTP "Soldiers
chase Link at double speed". It is "Fighters walk twice as fast" for the CPU only: after the original
walk-forward and walk-back routines (`Normal_03000`, `Normal_04000`, `src/PLNORMAL.c`) move the
fighter, the hooks call `add_mvxy_speed` once more while the fighter is still walking, but only for a
CPU fighter (`wu.operator == 0`) in a paid game (`Demo_Flag` set).

**Evidence:** Same hook points as `fighters-walk-twice-as-fast.diff`. `operator` is what
`Player_move` uses to choose between the player's input and `CPU_Sub`. `sf3_cheat.py` found no
moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only walking is faster. Dashes, jumps, attacks and the CPU's reactions are the same speed. Making the
  whole CPU fighter run twice per frame was not done: its AI, command input and animation timers would
  all run twice against one hit check per frame.
- The CPU may still walk at a normal pace in places, since the AI picks how long to walk by its own
  timers and distances.
- Can't be built together with "Fighters walk twice as fast" or "Low gravity" (same hooks, or the end of
  the same file).

## Hold Start when picking a character to play as Gill or Shin Akuma

**Source diff:** `patches/gill-and-shin-akuma-selectable.diff`
**BPS:** `sf3_ggpatch/gill-and-shin-akuma-selectable/` (simm1.0-.3)
**Changes:** 213 bytes. The new `Sel_PL_3rd` at 06700000. 0619547D: its address in the constant copy of
`Sel_PL_Jmp_Tbl` (the nearest symbol is `Face_Order_Data`).
**Recorded:** 2026-11-15 20:29:24

Tags: `demo-ready` `curated` `play-start`

**Mechanism:** The 3rd Strike version of FF2 "New game: <character> is in the party". On the select
screen, `Sel_PL_3rd` (`src/sel_pl.c`) runs `Sel_PL_Sub`, which sets the character from the face grid
when a button is pressed:

```c
Sel_PL_Complete[PL_id] = 1;
My_char[PL_id] = ID_of_Face[Cursor_Y[PL_id]][Cursor_X[PL_id]];
```

The grid (`Face_Cursor_Data`, `data/Sel_Data.c`) has no Gill (`PL_GILL`, 0) or Shin Gouki
(`PL_GOUKI2`, 15). This is a hook: the new `Sel_PL_3rd` runs the original, and on the frame a
character is confirmed in a paid game with that player's Start held, it changes `My_char` to Shin
Gouki if it was Akuma and to Gill otherwise. It then does the same super-art and boss-intro reset that
`Sel_PL_Sub` does when the character changes.

**Evidence:** `Sel_PL_3rd` is only reached through `Sel_PL_Jmp_Tbl` in `Sel_PL`. Gill and Shin
Gouki are full fighters: the CPU uses them (`EM_Cand.c`, `Com_Pl.c`), and `PLMAIN.c`, `pow_pow.c`
and `plcntset_2.c` handle Shin Gouki as a player. Fighter numbers from `include/fighter.h`.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Hold Start, then press the punch or kick button that picks the colour.
- The select screen still shows the face you picked. The change shows from the super-art screen or the
  VS screen on.
- Gill's super-art list may not be like the others' (the CPU always gives him art 1). Picking art 2 or 3
  with Gill may not work.
- In single-player, the CPU's opponents and the boss order may act oddly (Gill against Gill).
- After a continue, the "same CPU opponent" check runs before the change.
- Not in the attract demo.

## Skip the boot screens, the logos and the opening movie

**Source diff:** `patches/skip-logos-and-opening.diff`
**BPS:** `sf3_ggpatch/skip-logos-and-opening/` (simm1.0-.3)
**Changes:** 895 bytes. The new `mode_init_task` at 06700000-0670038F, `CAPCOM_Logo` at
06700390 and `Title` at 06700394-067003B7. 06004E7D (`text_clear_task_exit`), 060055E9
(`test_mode_wait`) and 06005AF1 (`test_mode_exit`): `mode_init_task`'s address in their literal
pools. 0609501D and 06095025: `CAPCOM_Logo`'s and `Title`'s addresses in the literal pool of
`Loop_Demo`.
**Recorded:** 2026-11-15 20:30:41

Tags: `play-start` `utility`

**Mechanism:** The 3rd Strike version of EarthBound "Skip the logos and the title screen" and Super
Metroid "New games skip the opening cinematic". The attract loop in `Loop_Demo` (`src/Game_Main.c`)
runs `CAPCOM_Logo` (`src/demo00.c`: the warning, CAPCOM and other logo screens), then `Title`
(`src/demo01.c`: the opening movie), then demo fights and rankings. Both are hooks:

- The new `CAPCOM_Logo` returns 1 ("done") at once, so the logo screens never show.
- The new `Title` lets the original set up the screen and the colours, then skips the
  `TT_DEMO` step (`opening_demo_tick`) by moving to `TT_HOLD` with a 1-frame timer, so it goes
  straight to the usual wipe into the demo fight.

Before that, the start-up task `mode_init_task` (`src/mode_init.c`) shows two screens of its own.
The first is the title screen: `boot_title_str` (STREET FIGHTER III, 3rd STRIKE, 990512, the
program's date) and `boot_region_str` (the region, here JAPAN) in `data/Com_Pl_tbl.c`, for up to
166 frames. The second is the region's legal warning (`warning_mes[Country - 1]`) for up to 100
frames. A button cuts either one short. Also a hook (added 2026-11-17): `mode_init_task` is
renamed `mode_init_task_orig`, and the new `mode_init_task` is a copy of it without the two
`tilemap_print_string` screens and their wait loops. It still runs everything else the same
way and in the same order: `display_mode_setup`, `cd_ready_flag`/`no_cd_flag`, `load_char_gfx`,
`setup_kage_cells`, and the 6- and 16-frame `task_sleep`s (now on a blank screen). Then it
starts the frame and entry tasks as before.

**Evidence:** `CAPCOM_Logo` and `Title` are only called from `Loop_Demo`. `mode_init_task`
is only used by address: `boot_task` (`src/boot_task.c`) starts it at power-on, and the test
menu restarts it (`src/test_mode.c`) and kills it by address (`kill_tasks_by_func`). All of
these now get the new one. The parental advisory screen is `Logo_Warning`, inside
`CAPCOM_Logo`, and was already skipped. A coin already leaves the attract loop
from any step (`Ck_Coin` at the top of `Loop_Demo`), and the title after a coin is a different routine
(`Title_At_a_Dash`), which is not changed. `sf3_cheat.py` found no moved code or data.
`git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works.
- The attract mode becomes demo fights and rankings only. The opening movie after a coin (in
  `Title_At_a_Dash`) still plays.
- The CPS3 BIOS screens before the game starts are not part of this program and still show.
- Start-up still takes about 1.5 seconds of blank screen (the 60-frame wait before the screens, and
  the 6- and 16-frame waits kept for safety).
- Leaving the test menu also skips the two boot screens.
- The logo screens also cleared the screen and loaded backgrounds. If leftovers from a ranking screen
  show during the next demo fight, this is why.

## Hold Start + LP + LK in the attract mode for the debug menu

**Source diff:** `patches/debug-menu.diff`
**BPS:** `sf3_ggpatch/debug-menu/` (simm1.0-.3)
**Changes:** 146 bytes. The new `Loop_Demo` at 06700000. 06194159: its address in the constant copy of
`Main_Jmp_Tbl` (the nearest symbol is `grade_t_table`).
**Recorded:** 2026-11-15 20:32:31

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The game still has the developers' "OBJECT TEST" debug menu (`src/CMD_MAIN.c`): BG
SELECT, OBJECT LOOK, OBJECT EDIT, OBJECT EDIT 2, HIT, ALL CHARACTER, PARTS, and pages named after staff
(YOKOYAMA, NAKAI, YOSHIZUMI, YU, RAOH, INE, OHYA). Its top routine `debug_scene_outer_dispatch` is never
called. It reads the inputs itself, runs the menu (`Debug_R_No`: set-up, graphics, players, the
menu, then the chosen page), and returns 1 when P2 holds LP + MP + HP + LK:

```c
if ((dbg_p2sw_0 & (BUTTON_PUNCHES | BUTTON_LK)) == (BUTTON_PUNCHES | BUTTON_LK)) {
    return 1;
}
```

This is a hook on `Loop_Demo` (`src/Game_Main.c`), the attract loop that the game frame task runs
while no game is on. When P1 holds Start + LP + LK, the new `Loop_Demo` clears the menu's state (as
`test_menu_init` in `src/test_mode.c` still does) and sets `Debug_w[0]` to 0x5A. While it is 0x5A, it
runs `debug_scene_outer_dispatch` each frame instead of the attract mode. When that returns 1, it clears
the flag and restarts the attract loop (`G1_DEMO_INIT`). Otherwise it runs the original.

**Evidence:** `debug_scene_outer_dispatch` is in the ROM (060A4748 in `functions.tsv`), with
`debug_main_dispatch` and the staff pages (`debug_play07` and on, `src/end_sub_3.c`). The menu's own
set-up sets `G_No0` to 0, so it must run from `Loop_Demo`, which `bg0001` calls through
`Main_Jmp_Tbl` while `G_No0` is 0. That is also where the game frame task flips the sprites. `Debug_w`
(`src/Manage.c`, 02017004) is never read or written by the game. `sf3_cheat.py` found no moved code or
data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works.
- In the menu, P1 moves the cursor (up and down) and LP picks. The pages use both controllers, and some
  read the DIP switches.
- The source has no notes on how each page is used. Some may be unfinished or crash.
- Leaving with P2 LP + MP + HP + LK restarts the attract loop. If graphics are left over, reset the
  game.
- The `DEBUG_DISP`, `DEBUG_EDIT` and `DEBUG_SLOW` code in the source was compiled out of the arcade
  ROM (they are constant 0s), so it can't be turned on without moving code.
- A coin (or Start on free play) while holding Start + LP + LK opens the menu instead of starting a game.
- Can't be built together with other cheats that add to the end of `src/Game_Main.c`.

## No music

**Source diff:** `patches/no-music.diff`
**BPS:** `sf3_ggpatch/no-music/` (simm1.0-.3)
**Changes:** 38 bytes. The new `sound_driver_tick` at 06700000. 060007ED: its address in the vertical
blank interrupt's literal pool (`src/intr.src`; the nearest symbol is `frt_overflow_intr`).
**Recorded:** 2026-11-15 20:33:44

Tags: `demo-ready` `play-start` `utility`

**Mechanism:** The 3rd Strike version of the "No music" cheats in Metroid, SMB3, ALTTP, Super Metroid,
OoT, FF2 and EarthBound. `sound_seq_start` (`src/textsound_2.c`) starts a music sequence (header byte
0) on the 16 `bgm_voice`s and sets bit 2 of `bgm_state`. Sound effects and voices use the separate
`se_voice`s. `bgm_stop` stops the music:

```c
for (i = 0; i < 16; i++) {
    bgm_voice[i].status = 192;
}
bgm_state = 1;
```

This is a hook: the new `sound_driver_tick` (run from the vertical blank interrupt) calls `bgm_stop`
whenever music is on, then runs the original. A song is stopped on the first tick after it starts,
before any of its notes play.

**Evidence:** `sound_driver_tick` is only called from `src/intr.src`. The game never waits for the
music to end: `bgm_state` is only read by the sound driver and by the sound test
(`sound_status_read`). `sf3_cheat.py` found no moved code or data. `git apply --check` against
main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works.
- Music in the test mode's sound test is silent too.
- A short jingle that is a music sequence (not a sound effect) is silent too.
- Can't be built together with "Every sound effect is the next one in the list" (both add to the end of
  `src/textsound_2.c`).
- Can't be built together with "All music plays 1.5 times as fast" (the end of `src/textsound_2.c`).

## Music and sound effects high-pitched

**Source diff:** `patches/music-and-sound-effects-high-pitched.diff`
**BPS:** `sf3_ggpatch/music-and-sound-effects-high-pitched/` (simm1.0-.3)
**Changes:** 67 bytes. The new `voice_process_secondary` at 06700000. 0613A6A5: its address in the
literal pool of `sound_driver_tick`.
**Recorded:** 2026-11-15 20:34:47

Tags: `demo-ready` `curated` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the FF2, ALTTP and SMW "2 whole tones higher" cheats. At the end
of `voice_process_secondary` (`src/sound_voice_2.c`), each voice's pitch register is set from its
pitch (3072 units an octave, 256 a semitone):

```c
*(u16*)&regs->pitch = (u16)sound_note_to_pitch(
    (s16)((u32)voice->pitch_lfo >> 16) + voice->current_pitch + ...
```

`sound_note_to_pitch` is only called from this file, so hooking it would move code. Instead this is a
hook on `voice_process_secondary`: the new one adds 1024 (4 semitones) to `current_pitch`,
`target_pitch` and `decoded_pitch`, runs the original, then takes the 1024 off again. Inside the
original these three are only copied to each other, compared, or moved by a slide step, so the offset
changes nothing but the pitch written.

**Evidence:** `voice_process_secondary` is only called from `sound_driver_tick` (`src/textsound_2.c`),
for the 16 music voices and the 16 effect voices. Field types (all `s32`) from `include/structs.h`.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works.
- The CPS3 plays samples, so higher pitch also means faster: voices and effects are shorter and sound
  like chipmunks.
- The pitch register is 16 bits. A note already near the top may wrap around and play very low.
- The test mode's sound test is changed too.

## Every sound effect is the next one in the list

**Source diff:** `patches/next-sound-effect.diff`
**BPS:** `sf3_ggpatch/next-sound-effect/` (simm1.0-.3)
**Changes:** 269 bytes. The new code at 06700000 (`cheat_se_header`, `cheat_next_se`, `sound_request`,
`sound_request_pan`). 24 literal-pool addresses in the callers (`Se_Shock`, `Se_Myself`, `Se_Let`,
`Call_Se`, `Loop_Demo`, `Game_Manage_4th`, the sound test and others), 3 bytes each.
**Recorded:** 2026-11-15 20:36:22

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** The 3rd Strike version of the FF2, ALTTP and OoT "Every sound effect is the next one"
cheats. Every sound goes through `sound_request` (menus and `Sound_SE`) or `sound_request_pan` (fight
sounds and voices, from the `Se_` handlers in `src/se_3.c`). Both pass a code to `sound_seq_start`
(`src/textsound_2.c`), whose first sequence byte says what it is: 0 is music, 1-0x7F a sound effect
with that priority, 0x80 and up a control sequence:

```c
hdr = *p++;
if (!hdr) {
    bgm_stop();
```

This is a hook on both: the new versions play code + 1 when both the code and the next one are sound
effects (header 1-0x7F), and the original code otherwise. So no sound effect starts a song, and music
and control codes are not changed.

**Evidence:** Neither function is called from its own file (`sound_seq_start` is, so it is not
hooked). Codes wrap at `snd_seq_max` as in `sound_seq_start`. Each character's voices
are in their own block of 0x20 codes between 0x140 and 0x3FF (Ken 0x180, Chun-Li 0x1A0, Ryu
0x200 and so on, from the `se` values in `data/*_char.c`). Each block has 18-32 sound effects
in the sequence table (`snd_seq_rom_data`, 0678F000), so code + 1 is usually that character's
next voice line. Shared hit and swing sounds are at 0x100-0x13F (62). Player 2's copies of all
of these are 0x300 codes higher (`uid * 0x300` in `src/se_3.c`). `sf3_cheat.py` found no moved
code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-17): works.
- A fighter's voice lines often become the next voice line (a different move's shout).
- The test mode's sound test plays the next effect too.
- Can't be built together with "No music" (both add to the end of `src/textsound_2.c`).
- Can't be built together with "All music plays 1.5 times as fast" (the end of `src/textsound_2.c`).

## All music plays 1.5 times as fast

**Source diff:** `patches/music-plays-faster.diff`
**BPS:** `sf3_ggpatch/music-plays-faster/` (simm1.0-.3)
**Changes:** 28 bytes. The new `sound_driver_tick` at 06700000. 060007ED: its address in the vertical
blank interrupt's literal pool (`src/intr.src`).
**Recorded:** 2026-11-15 20:37:06

**Mechanism:** The 3rd Strike version of SMB1 "All music plays at hurry-up speed". Each tick,
`voice_process_secondary` (`src/sound_voice_2.c`) counts a music voice's note and event timers down
by the song's tick step plus an extra tempo value:

```c
voice->event_ticks -= bgm_tick_step + bgm_tempo_add;
```

`bgm_tempo_add` is only set by `bgm_tempo_set` (`src/textsound_2.c`), which the game never calls, and
`sound_seq_start` clears it. This is a hook: the new `sound_driver_tick` sets `bgm_tempo_add` to half
of `bgm_tick_step` (the song's own tempo, set by its tempo events), then runs the original. Music then
plays at 1.5 times its tempo.

**Evidence:** `sound_driver_tick` is only called from `src/intr.src`. Sound effects use
`se_tick_step` and are not changed. `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only the tempo changes, not the pitch.
- Can't be built together with "No music" or "Every sound effect is the next one in the list" (the
  same hook, or the end of the same file).

## Fighters use colours from past the end of their colour table

**Source diff:** `patches/colours-past-the-end.diff`
**BPS:** `sf3_ggpatch/colours-past-the-end/` (simm1.0-.3)
**Changes:** 453 bytes. The new `load_player_color` at 06700000. Its address in 9 literal pools: the
fight's colour load (06118635, in `src/PLCNTDAT.c`; the nearest symbol is `set_kizetsu_status`) and 8 in
the debug menu.
**Recorded:** 2026-11-15 20:39:04

**Mechanism:** The 3rd Strike version of Tetris "Level palettes are read from past the end of color
table". `load_player_color` (`src/color3rd.c`) copies a fighter's palette parts from the colour ROM to
colour RAM, using `player_color_tbl[fighter][side][colour 0-6]` (14 parts of source, destination and
size, `data/end_sub_tbl_b.c`):

```c
const XFER* p = player_color_tbl[a][b][c];
...
col_trans_result = col_dma_request(p->src, p->dst, p->size, 0, 0, 0);
```

Each part's source goes up by a fixed step from one colour to the next (0x100 for most parts, 0 for
parts all colours share). This is a hook: the new `load_player_color` loads each part from 7 steps on
(the step is colour 1 minus colour 0), that is, from where colours 7 to 13 would be, into the fighter's
own colour RAM. A colour number outside 0-6 goes to the original.

**Evidence:** `load_player_color` is not called from its own file. A check of all 19 x 2 x 14 parts in
the table: the step is the same from colour to colour for every part except Gill's (his colour 6
repeats colour 5, which is why the step comes from colours 0 and 1). Every new source stays inside the
colour data (0x3300700-0x336B680; the table spans 0x3300000-0x336B700), and 3612 of the 3668 are the
start of some fighter's real palette part, mostly the next fighter's. `sf3_cheat.py` found no moved
code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Most fighters get palettes made for a different fighter, so the colours land on the wrong body
  parts. The colour button still picks which of 7 such colourings you get.
- The select-screen and VS-screen portraits, the super-art background, and colours loaded by other
  routines (Gill's and Twelve's change colours, `metamor_color_restore`; the ending's
  `load_player_color_fade`) are not changed.
- The debug menu's colour viewers are changed too.

## Yang's Senkyuutai uses its old, unused version

**Source diff:** `patches/yang-old-senkyuutai.diff`
**BPS:** `sf3_ggpatch/yang-old-senkyuutai/` (simm1.2 and .3 only)
**Changes:** 4 bytes, in place: 065ED256 and 065ED266, two entries of `pl10_exatt_table`.
**Recorded:** 2026-11-15 20:40:14

**Mechanism:** Yang's 236+K (Senkyuutai, also EX) and his SA II (Tenshin Senkyuutai) run
`Att_TENSHINSENKYUUTAI` (`src/PLPATUNI.c`), from entries 1 and 5 of his move table
`pl10_exatt_table` (`data/plpat10_tbl.c`). The ROM also has `Att_TENSHINSENKYUUTAI_OLD`, which
nothing uses. It is the same except that it lacks the newer version's contact step:

```c
if (wk->wu.routine_no[3] != TENSHINSENKYUU2_MOVE2 && wk->hos_fi_flag | wk->hos_em_flag) {
    char_move_cmj4(&wk->wu);
    wk->wu.routine_no[3] = TENSHINSENKYUU2_MOVE2;
}
```

(when Yang is pushed by the opponent's body or a wall during the move, the new version skips the
animation ahead and moves on to a second phase; the script's cue 50 does the same). This is an
in-place change: the two table entries point to `Att_TENSHINSENKYUUTAI_OLD`.

**Evidence:** `Att_TENSHINSENKYUUTAI_OLD` is in the ROM (061278A8 in `functions.tsv`) and is not
referenced. `pl10_exatt_table` is Yang's only use of either routine. Only the low half of each
4-byte pointer changed (2 bytes each), so only chips simm1.2 and .3 change. `sf3_cheat.py` found no
moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- The difference only shows when Yang runs into the opponent or a wall during the move: the old
  version keeps playing the move's animation instead of cutting to its follow-up. This may make the
  move miss, hit differently, or look odd.
- Uses no cheat code space, so it can go into a combined build (`sf3_cheat.py build a b`) with any
  cheat that doesn't change `data/plpat10_tbl.c`. Its BPS files still only apply to the original chips.

## Yang's Kaihou uses its old, unused version

**Source diff:** `patches/yang-old-kaihou.diff`
**BPS:** `sf3_ggpatch/yang-old-kaihou/` (simm1.2 and .3 only)
**Changes:** 2 bytes, in place: 065ED26E, entry 7 of `pl10_exatt_table`.
**Recorded:** 2026-11-15 20:49:48

**Mechanism:** Yang's 623+K (Kaihou, the slide) runs `Att_PL10_MACH_SLIDE2` (`src/plpat10.c`), from
entry 7 of his move table `pl10_exatt_table` (`data/plpat10_tbl.c`). The ROM also has
`Att_PL10_MACH_SLIDE`, which nothing uses. Both start the slide on the animation's cue 30 and stop
it on cue 21, which Yang's three Kaihou scripts (`yang_saca_102` to `104`) have. The newer version
also:

```c
wk->wu.mvxy.a[1].sp = wk->wu.mvxy.d[1].sp = wk->wu.mvxy.kop[1] = 0;   /* no up or down speed */
...
if (wk->micchaku_flag) {   /* touching the opponent */
    char_move_z(&wk->wu);
} else {
    return;
}
```

The old version keeps the slide data's up and down speed, only checks for the cues after moving
(no wait for contact), and uses `char_move_z` when Yang has stopped moving (`old_pos_data`). This
is an in-place change: the table entry points to `Att_PL10_MACH_SLIDE`.

**Evidence:** `Att_PL10_MACH_SLIDE` is in the ROM (0612A340 in `functions.tsv`) and is not
referenced. `cmd_data.c` names routine 23 `YANG_KAIHOU`, and `pl10_exatt_table` is the only use of
`Att_PL10_MACH_SLIDE2`. Only the low half of the 4-byte pointer changed, so only chips simm1.2 and
.3 change. `sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- The newer version clears the vertical speed, which suggests the slide data has some. If so, Yang
  may rise or sink during the old slide. He may also slide differently when he reaches the opponent.
- It changes the same table line as "Yang's Senkyuutai uses its old, unused version", so the two
  diffs can't be combined as they are. Uses no cheat code space.

## Urien's SA II refills his health (his unused resurrection)

**Source diff:** `patches/urien-sa2-resurrection.diff`
**BPS:** `sf3_ggpatch/urien-sa2-resurrection/` (simm1.1-.3)
**Changes:** 10 bytes, in place: 065ED39E (entry 5 of `pl13_exatt_table`) and 8 bytes of Urien's
SA II row in `asstbl_sa_ground` (065F1831-065F184B).
**Recorded:** 2026-11-15 20:50:39

**Mechanism:** Gill's Resurrection is `Att_RESURRECTION` (`src/PLPAT00.c`), with animation 53. Urien
was built from Gill, and the ROM still has his copy: `Att_RESURRECTION2` (`src/PLPAT13.c`), its
refill table `glap_table2` (`data/plpat13_tbl.c`), and an animation 53 ("not started by a command",
`urien_saca_053`) with the same cues (26, 24, 22) as Gill's. Nothing starts them:

```c
case RESURRECTION2_CUE:
    char_move(&wk->wu);
    if (wk->wu.cg_type) {
        wk->wu.direction = get_life_add_point2(wk->wu.cg_type, wk->wu.direction);
    ...
    wk->wu.vital_new += wk->wu.direction;
    if (wk->wu.vital_new < wk->wu.vitality) {
        return;
```

(cue 26 refills 4 points a frame, 24 three and 22 two, until the bar is full). This cheat puts the
move on Urien's SA II, Temporal Thunder (236236+P), two in-place changes: entry 5 of
`pl13_exatt_table` (attack routine 21, `URIEN_TEMPORAL_THUNDER`) points to `Att_RESURRECTION2`, and
Urien's SA II row of `asstbl_sa_ground` (read by `execute_super_arts`, `src/PLS03.c`) starts
animation 53 instead of 66-69, the same row values as Gill's `{ 0, 53, 0 }`.

**Evidence:** `Att_RESURRECTION2` (0612AAE8 in `functions.tsv`) is not referenced. Routine 21 is
only Temporal Thunder for Urien (`cmd_data.c`). The other SA rows and table entries are unchanged.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only when Urien picks SA II. He loses Temporal Thunder. The super still uses a gauge stock.
- Gill's resurrection runs automatically on a KO through his rebirth gauge. This one is started by
  hand, while Urien is alive, so the refill works like a heal. With a full health bar the move ends
  at once (a small hop to the ground).
- Gill's glow effect (`EFFJ7.c`) checks for Gill only, so Urien may not glow.
- A CPU Urien with SA II uses it too.

## Air parries knock you backward (the old, unused air parry)

**Source diff:** `patches/old-air-parry.diff`
**BPS:** `sf3_ggpatch/old-air-parry/` (simm1.2 and .3 only)
**Changes:** 4 bytes, in place: 065EBBBE and 065EBBC2, entries 34 and 35 of `plpnm_lv_00`.
**Recorded:** 2026-11-15 20:51:16

**Mechanism:** A parry in the air sets the fighter's state to 34 or 35 (`defense_sky`,
`src/HITCHECK.c`), and both run `Normal_35000` (`src/PLNORMAL.c`) from the state table
`plpnm_lv_00` (`data/PLPNM_tbl.c`). The ROM also has `Normal_air_paring`, which nothing uses. It is
the same except for how it changes the fighter's speed. The used one only turns a fall into a small
rise:

```c
void remake_mvxy_PoSB(WORK* wk) {          /* Normal_35000 */
    if (wk->mvxy.a[1].sp < 0) {
        wk->mvxy.a[1].sp = wk->mvxy.a[1].sp * 30 / 100;
        wk->mvxy.a[1].sp = -wk->mvxy.a[1].sp;
    }
}
```

The old one (`setup_air_paring_mvxy`, `src/PLS02.c`) cuts the forward speed to 60% and the up or down
speed to 40%, then turns forward motion around so the fighter always moves backward, at least 2
pixels a frame. This is an in-place change: entries 34 and 35 point to `Normal_air_paring`.

**Evidence:** `Normal_air_paring` is in the ROM (06121F52 in `functions.tsv`) and is not
referenced. `plpnm_lv_00` is the only use of `Normal_35000`. Both routines read `guard_kind` the
same way and use the same animation (27). Only the low half of each pointer changed, so only chips
simm1.2 and .3 change. `sf3_cheat.py` found no moved code or data. `git apply --check` against
main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- A fighter who parries while falling keeps falling (40% as fast) instead of popping up, so there
  is less time to attack back in the air.
- For both players and the CPU. Ground parries are not changed.
- Uses no cheat code space.

## The CPU opponent only jumps backward and guards in the air (unused CPU AI)

**Source diff:** `patches/cpu-jumps-back-and-guards.diff`
**BPS:** `sf3_ggpatch/cpu-jumps-back-and-guards/` (simm1.0-.3)
**Changes:** 267 bytes. The new `Jump` at 06700000. Its address in 86 literal pools, all in the CPU
AI's `Passive*`, `Active*`, `Pattern*` and `Shell*` routines (`src/Com_*.c`, `src/active*.c` and
the rest).
**Recorded:** 2026-11-15 20:53:15

**Mechanism:** The CPU AI jumps with `Jump(wk, Jump_Dir)` (`src/Com_Sub.c`), which picks the jump
direction and checks once, as the CPU leaves the ground, whether to guard (`Check_Air_Guard`). The
ROM also has `Jump_Air_Guard`, which nothing uses:

```c
case 0:
    ...
    Free_Lever[wk->wu.id] = Setup_Guard_Lever(wk, Lever);   /* Lever 1: away from the opponent */
case 1:
    Lever_Buff[wk->wu.id] = Free_Lever[wk->wu.id] | 1;      /* up and away */
    ...
default:
    Check_Air_Guard(wk);                                     /* every frame in the air */
    Lever_Buff[wk->wu.id] = Lever_LR[wk->wu.id];
```

This is a hook: `Jump` is renamed `Jump_orig`, and the new `Jump` in the CHEAT section calls
`Jump_Air_Guard(wk, 1)`. `Keep_Away` in the same file now calls `Jump_orig`, so its code stays the
same size.

**Evidence:** `Jump_Air_Guard` (0600BB08 in `functions.tsv`) is not referenced. Its steps use
`CP_Index[id][1]` the same way `Jump` does, and end the AI step the same way when the CPU lands.
`Keep_Away` was the only same-file caller; calling `Jump` from the CHEAT section made it 16 bytes
shorter, which moved the code after it. `sf3_cheat.py` found no moved code or data. `git apply
--check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only the CPU. Every jump its AI picks becomes a back jump; it no longer jumps in, except for its
  high jumps (`Hi_Jump`), jump attacks (`Jump_Attack` and others) and the keep-away jump, which
  are separate routines.
- `Jump_Air_Guard` doesn't wait for the AI's `Combo_Speed` delay before jumping.
- The guard check holds the lever back (and down) in the air. Few attacks can be guarded in the air
  in 3rd Strike, so the guarding may not show.

## Each fighter's movement moves the other fighter

**Source diff:** `patches/fighters-move-each-other.diff`
**BPS:** `sf3_ggpatch/fighters-move-each-other/` (simm1.0-.3)
**Changes:** 178 bytes. 06700000-067000AF: the new `Player_move`. 06117989, 06117AB9: its address in the
literal pools of `move_P1_move_P2` and `move_P2_move_P1` (3 bytes each).
**Recorded:** 2026-11-15 21:57:44

Tags: `interesting` `demo-ready` `play-start` `video-ready`

**Mechanism:** Each frame `move_player_work` (`src/plcntset_2.c`) runs `Player_move` (`src/PLMAIN.c`)
for each fighter. That runs the fighter's input and current move, which change its own position
`wu.xyz[0].disp.pos` (X) and `wu.xyz[1].disp.pos` (height).

This is a hook: `Player_move` is renamed `Player_move_orig`, and the new `Player_move` in the CHEAT
section runs it, then:

- **X:** the fighter's change in X this frame is undone and added to the other fighter's X.
- **Height:** this can't be done with changes per frame. A jump checks its own height to land, so if
  its height were undone each frame, it would land at the top of the jump and the other fighter would
  stay in the air. So each fighter keeps its "own" height in `pt_free` (20 unused bytes at the end of
  `PLW`, `include/structs.h`, used nowhere in the code). Its move runs at that height, and the other
  fighter is put at that height. So when player 1 jumps, player 2 goes up and comes down along the same
  arc, and player 1 stays where player 2's own height is.

```c
x = wk->wu.xyz[0].disp.pos;
y = wk->wu.xyz[1].disp.pos;
wk->wu.xyz[1].disp.pos = *own_y;
Player_move_orig(wk, lv_data);
em->wu.xyz[0].disp.pos += wk->wu.xyz[0].disp.pos - x;
*own_y = wk->wu.xyz[1].disp.pos;
em->wu.xyz[1].disp.pos = *own_y;
wk->wu.xyz[0].disp.pos = x;
wk->wu.xyz[1].disp.pos = y;
```

While either fighter is throwing or being thrown (`tsukami_f`, `tsukamare_f`), nothing is swapped and
each fighter's own height is set to its real height, because the thrower places the thrown fighter
itself.

**Evidence:** `Player_move` is only called from `move_P1_move_P2` and `move_P2_move_P1`
(`src/plcntset_2.c`), for `plw[0]` and `plw[1]`. `Player_move_orig` already saves `old_pos` before the
move, as before. `pt_free` follows the `s16 reserv_add_y`, so it is 2-byte aligned. `pli_0000` clears
both `PLW`s at the start of each round, so the own heights start at 0 (the floor). The screen-edge
check (`set_field_hosei_flag`) and the push between fighters still run on the positions you see.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- Screen X, not "forward": pushing right on player 1's side moves player 2 right. Walking toward the
  opponent moves the opponent the same way, so it walks away from you.
- Everything a fighter's own move does moves the other one: dashes, the forward motion of attacks,
  knockback and knock-downs. A fighter who gets hit sends the attacker flying back.
- Your own move still runs where you appear to stand, so hits, throws and facing use where you appear.
  The height your own move thinks it is at is not the one shown, so a jumping fighter's air attacks
  come out at the other fighter's height.
- A fighter can end up off the ground (standing in the air) or float for a moment after a throw ends,
  when the swapped heights jump to new values.
- Also runs in the round intro and win poses. The bonus stages use `Player_move_bonus` and are not
  changed.
- Can't be built together with "The floor is a conveyor belt", which hooks `Player_move` too.

## Ibuki's light Hien does her unused hop jump and medium Hien her bound jump

**Source diff:** `patches/ibuki-bound-and-hop-jumps.diff`
**BPS:** `sf3_ggpatch/ibuki-bound-and-hop-jumps/` (simm1.0-.3)
**Changes:** 716 bytes. 06700000-06700927: the four new animation scripts (`cheat_bound_jump`,
`cheat_bound_land`, `cheat_hop_jump`, `cheat_hop_land`). 22 bytes outside: `p7_cmd_30` (Hien's
routine numbers for LK and MK), `ibuki_saca` entries 74, 75, 77 and 78, `pl07_exatt_table` entries
11 and 12, and Ibuki's Hien row in `asstbl_sa_ground`.
**Recorded:** 2026-11-15 22:16:59

Tags: `demo-ready` `play-start`

**Mechanism:** `Att_PL07_BOUND_JUMP` and `Att_PL07_HOP_JUMP` (`src/PLPAT07.c`) are in the ROM but
not in Ibuki's move table, and no animation was made for them. They step on animation cues:

```c
case BOUND_JUMP_CUE:                    /* cue 1: take off with jump row r_no */
    char_move(&wk->wu);
    if (wk->wu.cg_type == 1) {
        setup_mvxy_data(&wk->wu, wk->wu.mvxy.index);
...
case BOUND_JUMP_MOVE:                   /* after landing and cue 10 */
    ...
    case 20: setup_mvxy_data(&wk->wu, 97);   /* bounce up */
    case 30: setup_mvxy_data(&wk->wu, 98);   /* float down */
```

The bound jump: a hop (cue 1), cue 8 in the air, land, cue 10, then a high bounce with Ibuki's jump
rows 97 (16 pixels a frame up, slowing to a stop at the top) and 98 (slow fall), and land again. The
hop jump: a hop (cue 1); on landing it waits for cue 1 again and hops with the next row; cue 8 in
the air makes the next landing the last.

None of Ibuki's animations sends cues 1, 8 or 10. A donor animation can't be used as it is: Hien's
(`ibuki_saca_028`, the best fit, with cue 20 at takeoff and cue 30 in the air) moves her itself with
`CM_MVIX` commands and lands into a lever-branch script, so the routines would only replay Hien.
So the cheat adds four new animation scripts in the CHEAT section of `data/ibuki_char.c`, made from
her own frames: the jump crouch (`ibuki_nmca_012`), the front jump (`ibuki_nmca_014`) and the
landing (`ibuki_exca_038`), with the cues where the routines wait for them. Each starts with a copy
of Hien's header. A `CM_RJA` at the start of each script picks the next landing animation:

- `cheat_bound_jump` (saca 74): crouch, take off with cue 1, cue 8 two frames later. Lands into 75.
- `cheat_bound_land` (saca 75): land with cue 10, crouch, cue 20 (bounce), cue 30 18 frames later
  (at the top), so she hangs and floats down. Lands into the normal landing (exca 38), which ends
  the move.
- `cheat_hop_jump` (saca 77): crouch, take off with cue 1, no cue 8. Lands into 78.
- `cheat_hop_land` (saca 78): land, crouch, take off with cue 1, cue 8 on the next frame. Lands into
  exca 38.

The routines go into the empty slots 11 and 12 of `pl07_exatt_table` (routines 27 and 28, were
`Att_DUMMY`). Hien's command (`p7_cmd_30`, 421+K) now starts routine 28 with LK and 27 with MK
(HK and EX are unchanged). Its rows in `asstbl_sa_ground` give them the new animations and their
first jump rows: LK `{ 124, 77, 0 }` (rows 124
then 125: a small hop, then a longer one), MK `{ 76, 74, 0 }` (row 76: Hien LK's own hop). All in place; the routines themselves are not changed.

**Evidence:** cue lists of all of Ibuki's `saca` scripts (from `data/ibuki_char.c`): only 20, 21,
30, 31, 40, 64, 88 and 255. `saca` slots 74 and 75 (scripts that only return) and 77 and 78 (copies of 76)
are not started by any table, script (`CM_JSR`/`CM_JMP`/`CM_RJA` with 5, 74-78) or code.
`jumping_union_process` (`src/PLS01.c`) lands by setting `routine_no[3]` and starting the
`CM_RJA` animation (`char_move_cmja`). `exca_038` ends with cue 255, which is how Hien's own landing
ends. `cal_mvxy_speed` mode 1 stops a speed at 0, so row 97 stops at the top of the bounce after 16
frames. The new scripts are at 8-byte-aligned addresses (the game reads them as 32-bit words).
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works (LK hop jump, MK bound jump).
- Light and medium Hien are gone; HK and EX Hien still work. The CPU's Ibuki gets the new moves too
  when it picks light or medium Hien.
- Neither jump attacks: no attack boxes, as the routines have no attack step. Hurt boxes are the ones
  from her normal jump frames.
- The animation is made up from her jump and landing frames, not art made for these moves. The
  timing (frame lengths, where the cues fall) is a guess.
- The bounce hangs at the top for a moment and then falls slowly (row 98 only has a small
  gravity), so the bound jump is long and easy to punish.
- If the first bound-jump hop lands before cue 8 (it shouldn't: cue 8 comes 2 frames after takeoff),
  the routine waits for cue 1 in the landing script, which has none, and the move ends after it.

## Ibuki's Kazekiri flies forward instead of up (farther with stronger kicks)

**Source diff:** `patches/kazekiri-flies-forward.diff`
**BPS:** `sf3_ggpatch/kazekiri-flies-forward/` (simm1.0-.3)
**Changes:** 47 bytes, all in `ibuki_movexy_table` rows 43-50 (06463028-06463085).
**Recorded:** 2026-11-15 22:43:32

Tags: `demo-ready` `curated` `play-start`

**Mechanism:** Kazekiri (623+K) is `Att_SHOURYUUKEN` (`src/PLPATUNI.c`). Its row in
`asstbl_sa_ground` gives each strength a rising row (`r_no`: 43 LK, 44 MK, 45 HK, 46 EX) and a
falling row (`data_ix`: 47-50):

```c
case 20:    /* takeoff */
    setup_mvxy_data(&wk->wu, wk->wu.mvxy.index);        /* rows 43-46 */
...
case 30:    /* top of the kick */
    setup_mvxy_data(&wk->wu, wk->as->data_ix);           /* rows 47-50, then fall until landing */
```

The rising rows were a fast climb (y speed 2048-3168, gravity -256) with a small forward drift
(416-480, slowing down). The cheat changes the 8 rows in place (`data/ibuki_move.c`):

| Row | Was (x spd, x acc, mode, y spd, y acc, mode) | Now |
| --- | --- | --- |
| 43 LK rise | 416, -8, 1, 2048, -256, 1 | 1024, 0, 1, 1024, -128, 1 |
| 44 MK rise | 416, -16, 1, 2624, -256, 1 | 1536, 0, 1, 1024, -128, 1 |
| 45 HK rise | 480, -20, 1, 3168, -256, 1 | 2048, 0, 1, 1024, -128, 1 |
| 46 EX rise | 480, -20, 1, 3168, -256, 0 | 2560, 0, 1, 1024, -128, 1 |
| 47 LK fall | 128, -6, 1, 0, -128, 0 | 1024, 0, 1, 0, -128, 0 |
| 48 MK fall | 128, -6, 1, 0, -112, 0 | 1536, 0, 1, 0, -128, 0 |
| 49 HK fall | 128, -6, 1, 0, -112, 0 | 2048, 0, 1, 0, -128, 0 |
| 50 EX fall | 288, -6, 1, 0, -120, 0 | 2560, 0, 1, 0, -128, 0 |

Every strength now rises only about 18 pixels (8 frames, then the y speed stops at 0 because of
mode 1), flies flat until cue 30, and drops for about 9 frames. The forward speed stays the same the
whole time: 4, 6, 8 and 10 pixels a frame. With about 19-20 frames in the air that is about 75, 115,
160 and 200 pixels (the original went about 20-30 pixels forward).

**Evidence:** rows 43-50 are only named by Ibuki's Kazekiri row in `asstbl_sa_ground` (`{ 43, 24, 47 }`
... `{ 46, 27, 50 }`), no other Ibuki row in `data/asstbl.c`, and no `CM_MVIX` in
`data/ibuki_char.c`. Cue 20 to cue 30 is 10 frames for LK and MK (`ibuki_saca_024`, `025`) and 11
for HK and EX (`026`, `027`). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-15): works.
- The animation and hit boxes are still the uppercut's: an upward kick that now travels sideways. It
  hits less high, so it is a worse anti-air.
- The flight distances are worked out from the rows, not measured.
- The EX version's follow-up after a hit (`CM_HJMP` in `ibuki_saca_027`) is not changed.
- The CPU's Ibuki uses the new Kazekiri too.

## Ground special moves work in the air

**Source diff:** `patches/ground-specials-in-the-air.diff`
**BPS:** `sf3_ggpatch/ground-specials-in-the-air/` (simm1.0-.3)
**Changes:** 386 bytes. 326 in the cheat area (new `check_special_attack`, `Player_attack` and
`process_attack`). 60 outside, all literal-pool addresses of those three functions: the callers in
`src/PLS00.c` (`nm_02000` ... `check_cg_cancel_data`), `plmain_lv_02` and `process_ndcca`.
**Recorded:** 2026-11-15 23:37:47

**Mechanism:** `check_special_attack` (`src/PLS03.c`) checks only the air specials (slots 46-55)
when the fighter is above the ground:

```c
} else if (wk->wu.xyz[1].disp.pos > 0) {
    goto air;
}
```

Two more things keep a ground special on the ground. Each special's first step calls
`hoken_muriyari_chakuchi` (`src/PLPAT.c`), which sets the height to 0. And `process_attack`
(`src/PLS00.c`) only ends a move on its end cue (255, or 64) at height 0:

```c
if (wk->wu.xyz[1].disp.pos == 0 || wk->bs2_on_car != 0) {
    jumping_cg_type_check(wk);
```

The cheat hooks all three (renamed to `_orig`, new versions in the CHEAT section):

- `check_special_attack`: in the air, the original runs first (air specials still win). If nothing
  matched, it runs again with the height set to 0, so the ground specials are checked, and the
  height is put back. When a ground special starts, it sets `pt_free[4]` (an unused byte of the
  player work).
- `Player_attack`: when `pt_free[4]` is set, it clears it and puts the height back after the
  move's first step, so the forced landing does nothing. (The check and the first step run in the
  same frame.)
- `process_attack`: after the original, if the move has reached its end cue in the air, the
  fighter falls 8 pixels a frame. At height 0 the original ends the move as usual.

It still respects the "no air specials" flag (`spmv_ng_flag` 0x20000000) and the "no ground
specials" flag (0x10000000), and leaves the bonus-stage car alone.

**Evidence:** `check_special_attack` is called only from `src/PLS00.c` (literal pools).
`Player_attack` and `process_attack` are only called through `plmain_lv_02` and
`process_ndcca`. In `player_mv_4000` (`src/PLMAIN.c`), `check_lever_data` (the input checks)
runs before `plmain_lv_02` (`Player_attack`) in the same frame. `hoken_muriyari_chakuchi` is
called from the first step of the specials (`PLPATxx.c`, `plpatNN.c`, `PLPATUNI.c`) and the
command normals in `src/PLPAT.c`. No source uses `pt_free`. `sf3_cheat.py` found no moved code
or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only special moves, not super arts. Supers use their own checks (`check_super_arts_attack`) and
  are not changed.
- Most ground specials don't move the fighter up or down, so the fighter hangs in the air for the
  whole move (a fireball thrown in mid-jump) and then drops straight down at 8 pixels a frame, with
  no landing animation. Moves that jump on their own (uppercuts like Shoryuken, which use
  `jumping_union_process`) take off from the height they started at and land normally.
- Moves with their own ground checks, throws (command grabs) and moves that dash along the ground
  may look wrong or end early. Command grabs in the air were not checked.
- A move whose animation ends with neither cue 255 nor 64 would hang until its script runs out.
- The CPU can use it too, when its inputs match in the air.
- No conflict with "Each fighter's movement moves the other fighter": that cheat uses `pt_free`
  bytes 0-1, and this one uses byte 4. They can be built together with `--name`.

## Special moves travel twice as far sideways

**Source diff:** `patches/specials-travel-twice-as-far.diff`
**BPS:** `sf3_ggpatch/specials-travel-twice-as-far/` (simm1.0-.3)
**Changes:** 228 bytes. 06700000-067000E7: the new `Player_attack`. 065EAF95: its entry in the
`routine_no[1]` jump table `plmain_lv_02` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-16 01:14:56

Tags: `demo-ready` `play-start` `video-ready`

**Mechanism:** Every special move and super art runs through `Player_attack` (`src/PLPAT.c`), which
calls the fighter's own move routine (`plxx_extra_attack_table`, `routine_no[2]` 16 and up). The
routine moves the fighter with `char_move` (animation steps, `cg_add_xy`) and the `mvxy` speeds
(`add_mvxy_speed`), all inside that call. This is a hook: the new `Player_attack` notes the
fighter's x position (`xyz[0].cal`, 16.16), runs the original, and adds the sideways movement of
that frame a second time. Each frame moves twice as far, and the move lasts as long as before, so it
is twice as fast and goes twice as far. Height is not changed.

Only special moves: `check_special_attack` (`src/PLS03.c`) points `wk->as` at rows 8-17 of
`asstbl_sa_ground` or `asstbl_sa_air` (command slots 28-37 and 46-55). Super arts use rows 0-7
(`check_super_arts_attack`), leap attacks use `asstbl_lv_D010`, and command normals use routines
below 16, so none of them change.

**Evidence:** `Player_attack` is only called through `plmain_lv_02`. It isn't run during hit stop
(`check_hit_stop` in `player_mv_4000`, `src/PLMAIN.c`). The screen-edge and push checks in
`move_player_work` (`src/plcntset_2.c`) run after, so walls still stop a fighter. Not while throwing
or being thrown (`tsukami_f`, `tsukamare_f`; the thrown fighter is placed from the thrower), and not
in bonus stages. `sf3_cheat.py` found no moved code or data. `git apply --check` against main:
applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Moves that don't travel (most fireballs, Shoryuken's mostly upward path) change little. The
  projectiles themselves are not changed (see "Projectiles fly twice as fast").
- A move's hit boxes don't change, so a fast-moving move may pass the opponent between its active
  frames and miss, or cross through them.
- Moves that place the fighter at a set spot (teleports, follow-ups that move to the opponent) also
  go twice as far from where they started, which may put them past the target.
- Both fighters, player or CPU.
- Can't be built together with "Ground special moves work in the air", which also hooks
  `Player_attack`, without merging the diffs by hand.

## Special moves travel 1.5 times as far sideways

**Source diff:** `patches/specials-travel-1-5x-as-far.diff`
**BPS:** `sf3_ggpatch/specials-travel-1-5x-as-far/` (simm1.0-.3)
**Changes:** 235 bytes. 06700000-067000EF: the new `Player_attack`. 065EAF95: its entry in the
`routine_no[1]` jump table `plmain_lv_02` (`data/PLMAIN_tbl.c`).
**Recorded:** 2026-11-16 01:17:18

Tags: `demo-ready` `curated` `play-start` `video-ready`

**Mechanism:** The same hook as "Special moves travel twice as far sideways", with half the extra
movement. The new `Player_attack` (`src/PLPAT.c`) notes the fighter's x position (`xyz[0].cal`,
16.16), runs the original, and adds half of that frame's sideways movement again:

```c
wk->wu.xyz[0].cal += (wk->wu.xyz[0].cal - x0) / 2;
```

The move lasts as long as before, so it is 1.5 times as fast and goes 1.5 times as far. Only special
moves (`wk->as` in rows 8-17 of `asstbl_sa_ground` or `asstbl_sa_air`), not super arts, command
normals or leap attacks. Height is not changed.

**Evidence:** As for the twice-as-far version: `Player_attack` is only called through
`plmain_lv_02`, not during hit stop; walls and pushing are checked after it in `move_player_work`.
Not while throwing or being thrown, and not in bonus stages. The division rounds toward 0, so a
leftward move gets the same extra as a rightward one. `sf3_cheat.py` found no moved code or data.
`git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Tested by the user in MAME (2026-11-16): works.
- Moves that don't travel (most fireballs) change little. Projectiles are not changed.
- Fast moves may pass the opponent between their active frames, less often than at 2 times.
- Teleports and follow-ups that move to the opponent go 1.5 times as far from where they started.
- Both fighters, player or CPU.
- Can't be built together with "Special moves travel twice as far sideways" or "Ground special moves
  work in the air" (all three hook `Player_attack`) without merging the diffs by hand.

## Blocked special moves do full damage

**Source diff:** `patches/blocked-specials-full-damage.diff`
**BPS:** `sf3_ggpatch/blocked-specials-full-damage/` (simm1.1 and simm1.3 only; the other two chips
are not changed)
**Changes:** 3 bytes. 0618A9CB, 0618A9CD, 0618A9CF: `kezuri_pow_table` entries 1-3 (in place).
**Recorded:** 2026-11-17 20:18:11

**Mechanism:** When a hit is blocked, `check_dm_att_guard` (`src/HITCHECK.c`) divides its damage by
the attack's chip divisor (`kezuri_pow`):

```c
ds->dm_vital = ds->dm_vital / as->kezuri_pow;
if (ds->dm_vital == 0) ds->dm_vital = 1;
```

`set_new_attnum` (`src/CHARMOVE.c`) picks the divisor from `kezuri_pow_table`
(`data/CHARSET_tbl.c`) with the 2-bit `kez` column of the attack's row in `data/<name>_attr.c`:
`{ 0, 4, 8, 16 }`, where 0 means no chip damage. The cheat changes the table in place to
`{ 0, 1, 1, 1 }`, so a blocked attack that did 1/4, 1/8 or 1/16 damage now does all of it. Attacks
with `kez` 0 (all normal attacks and throws) still do none.

**Evidence:** Of the attack rows in all `data/*_attr.c` files, 912 have `kez` 1-3 (149, 315 and 448).
Every one that a script uses belongs to a special move, an EX move or a super art. Fireballs use the
same check. `kezuri_pow_table` is read only in `set_new_attnum` and in `setup_metamor_kezuri`
(Twelve's X.C.O.P.Y., entry 3). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Super arts too: their attack rows use the same table, so blocked supers do full damage as well.
- The damage is the full hit's damage after the usual multipliers (difficulty, power-ups, combo
  scaling). The blocker still blocks: block stun, no knockdown, no stun gauge.
- If the damage is more than the blocker's health left, the block becomes a hit and KOs them (the
  game's chip KO), as before. Moves marked `no_death_attack` leave them at 0 health instead.
- Parried hits still do no damage.
- Both fighters, player or CPU.
