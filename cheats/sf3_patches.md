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
**Changes:** 92 bytes. 06700000-0670005B: the new `setup_catch_atthit`, `Player_damage` and
`subtract_dm_vital_aiuchi`. 065EAF89: the `Player_damage` entry of the `routine_no[1]` jump table
(`data/PLMAIN_tbl.c`). 06125A01: the address of `setup_catch_atthit` in the literal pool of
`catch_cg_type_check`. 06116F05, 06118CF1: the address of `subtract_dm_vital_aiuchi` in the literal pools
of `plcnt_move` and `plcnt_b_move` (3 bytes each).
**Recorded:** 2026-11-15 19:58:07

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

- Not tested.
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

- Not tested.
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

- Not tested.
- Player 2 still can't parry where the game forbids it: while dizzy (`py->flag`), in moves that set the
  `spmv_ng_flag` parry bits, when `guard_flag & 2`, or against attacks whose `att.guard` has no parry
  bits (such as throws).
- Throws: `check_blocking_flag` also reads `waza_flag[3]` and `[4]`, so player 2 counts as "parrying"
  when a throw lands and can't tech it (`hazusenai_flag`).
- Player 2 gets the parry score, Super Art gauge and grade points for every parry.
- Works for player 2 whether human or CPU, including the attract-mode demo.
- Can't be built together with "Every attack hits the opponent no matter where they are" (both hook
  `hit_check_main_process`).

## The Super Art gauge is always full

**Source diff:** `patches/super-art-gauge-always-full.diff`
**BPS:** `sf3_ggpatch/super-art-gauge-always-full/` (simm1.0-.3)
**Changes:** 101 bytes. 06700000-06700053: the new `Player_control`. 21 bytes outside: its address in the literal
pools of `Game2_1` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:01:48

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

- Not tested.
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

- Not tested.
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

- Not tested.
- Both fighters, player or CPU. Nobody can be dizzied, and the stun gauge stays empty.
- This uses the same hooks as "Player 1 never takes damage" and "Every hit stuns at once", so it can't be
  built together with them as is.

## The game runs at half speed

**Source diff:** `patches/half-speed.diff`
**BPS:** `sf3_ggpatch/half-speed/` (simm1.0-.3)
**Changes:** 92 bytes. 06700000-06700047: the new `set_EXE_flag`. 27 bytes outside: its address in the
literal pools of `Game2_1`, `Game08`, `Title` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:05:21

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

- Not tested.
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

- Not tested.
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

- Not tested.
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

- Not tested.
- Each hit restarts the 95-frame slow-down, so a long combo plays in slow motion all the way.
- The round clock also slows while it plays.
- Throws don't go through `Player_damage`, so they don't slow the game (unless they KO).

## The round timer never runs out

**Source diff:** `patches/round-timer-stops-at-1.diff`
**BPS:** `sf3_ggpatch/round-timer-stops-at-1/` (simm1.0-.3)
**Changes:** 28 bytes. 06700000-0670001B: the new `count_cont_main`. 06096D85: its address in the literal
pool of `Time_Control`.
**Recorded:** 2026-11-15 20:08:52

**Mechanism:** The 3rd Strike version of SMB3 "Time running out doesn't kill the Player". The round clock
is `Counter_hi` (99 down to 0), counted down by `counter_control` through `count_cont_main`
(`src/count.c`), which `Time_Control` (`src/Game_Main.c`) calls each fight frame. `counter_control`
copies it to `round_timer`, and the round ends by time over when that reaches 0 (`src/plcntset_2.c`):

```c
if ((will_die() != 0) && (round_timer.size.full == 0)) {
    ...
    Conclusion_Type = CONCLUSION_TIME_OVER;
```

This is a hook: the new `count_cont_main` only runs the original while `Counter_hi > 1`, so the clock
counts down as usual and then stays at 01.

**Evidence:** `count_cont_main` is only called from `Time_Control`. The bonus stages use their own
clock (`bcount_cont_main`), which is not changed. `sf3_cheat.py` found no moved code or data.
`git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- A round only ends by KO.
- The clock may stay in its last flash colour, since the flashing is also done by `counter_control`.
- The time bonus after a win is 1 x 300 (`Time_Bonus += round_timer * 300`).
- The CPU's "the clock is low" behaviour (`Counter_hi < 0xF` in `src/Com_Sub.c`) stays on once the clock
  is under 15.

## Hold Start to pause, press a button to step one frame

**Source diff:** `patches/start-pauses-buttons-step.diff`
**BPS:** `sf3_ggpatch/start-pauses-buttons-step/` (simm1.0-.3)
**Changes:** 111 bytes. 06700000-06700053: the new `set_EXE_flag`. 27 bytes outside: its address in the
literal pools of `Game2_1`, `Game08`, `Title` and the `debug_play*_move` routines.
**Recorded:** 2026-11-15 20:09:40

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

- Not tested.
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

- Not tested.
- The walk animation plays at its normal rate, so fighters slide a little.
- Both fighters, player or CPU. Dashes, jumps and the steps of moves are not changed.
- Characters whose walk is not states 3 and 4 (if any) are not changed.
- Can't be built together with "Low gravity: jumps go twice as high" (both diffs add to the end of
  `src/PLNORMAL.c`).

## Jump again in mid-air

**Source diff:** `patches/jump-again-in-mid-air.diff`
**BPS:** `sf3_ggpatch/jump-again-in-mid-air/` (simm1.0-.3)
**Changes:** 149 bytes. 06700000-0670009B: the new `check_air_jump`. 0611B5A9: its address in the
literal pool of `nm_18000`.
**Recorded:** 2026-11-15 20:12:08

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

- Not tested.
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

- Not tested.
- Both fighters. Normal, high and super jumps; not air jumps, wall jumps, jumping specials or being
  knocked into the air.
- The jump animation may reach its end before landing and hold its last frame.
- An attack in the air keeps the low gravity unless the move sets its own speeds.
- Jumps may go above the top of the screen.
- Can't be built together with "Fighters walk twice as fast" (both diffs add to the end of
  `src/PLNORMAL.c`).

## Fighters face away from each other

**Source diff:** `patches/fighters-face-away.diff`
**BPS:** `sf3_ggpatch/fighters-face-away/` (simm1.0-.3)
**Changes:** 47 bytes. 06700000-0670002B: the new `set_rl_waza`. 0611788D, 06118FE1: its address in the
literal pools of `move_player_work` and `move_player_work_bonus`.
**Recorded:** 2026-11-15 20:13:35

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

**Evidence:** `set_rl_waza` is only called from `src/PLCNT2.c` and `src/plcntset_2.c`, for both
fighters each frame. Not in bonus stages (`Bonus_Game_Flag`), where it also handles the car.
`sf3_cheat.py` found no moved code or data. `git apply --check` against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- "Forward" is away from the opponent, so walking, dashing, blocking and motion inputs are mirrored.
  Projectiles fly away from the opponent. Back-facing attacks and crossed-up jumps can still hit.
- Both fighters, player or CPU. The CPU may play badly.
- Moves that set the facing themselves (some throws, intros and win poses) may face the usual way for
  a moment.

## Fighters walk through each other

**Source diff:** `patches/fighters-walk-through-each-other.diff`
**BPS:** `sf3_ggpatch/fighters-walk-through-each-other/` (simm1.0-.3)
**Changes:** 26 bytes. 06700000-06700017: the new `check_body_touch`. 0611684D, 06118939: its address in
the literal pools of `Player_control` and `Player_control_bonus`.
**Recorded:** 2026-11-15 20:14:16

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

- Not tested.
- Fighters can stand in the same place and walk past each other; they then turn round as after a jump
  over.
- Hits still push the fighters apart (`check_damage_hosei`, not changed).
- A fighter in the corner can't be pushed out by the other's body, and the other can walk into the
  corner past them.

## Slippery floors: fighters slide after walking, dashing and jumping

**Source diff:** `patches/slippery-floors.diff`
**BPS:** `sf3_ggpatch/slippery-floors/` (simm1.0-.3)
**Changes:** 86 bytes. 06700000-06700053: the new `Normal_01000`. 065EBB39: its entry in the
`routine_no[2]` jump table `plpnm_lv_00` (`data/PLPNM_tbl.c`).
**Recorded:** 2026-11-15 20:15:30

**Mechanism:** The 3rd Strike version of the SMB2, SMB3, ALTTP and OoT "slippery floors" cheats. Standing
is `Normal_01000` (`src/PLPNM.c`), which only runs the standing animation:

```c
case N01_RUN:
    char_move((WORK*)wk);
```

The sideways speed of the walk, dash, jump or move before (`mvxy.a[0].sp`) is still in the fighter's
work, since standing doesn't clear it. This is a hook: the new `Normal_01000` runs the original, then,
on the ground, moves the fighter by that speed in the facing direction (as `add_mvxy_speed` does) and
takes 1/16 off the speed, setting it to 0 when it is under 1/16 pixel per frame. So a fighter who stops
walking or lands from a jump slides on, slowing down.

**Evidence:** `Normal_01000` is reached only through `plpnm_lv_00` (state 1). `mvxy.a[0].sp` is 16.16
fixed point; `reset_mvxy_data` (`src/PLS02.c`) is only run when an animation asks for it
(`comm_mxyt` in `src/CHARMOVE.c`). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Only while standing: crouching, blocking and attacking stop at once as usual. A fighter who starts
  to walk the other way stops sliding.
- How far a fighter slides depends on the last speed, so it may be odd after some moves (a back dash
  slides backward, a move that ended with a step slides that way). If a move's last speed was cleared,
  there is no slide.
- Both fighters, player or CPU.

## The floor is a conveyor belt

**Source diff:** `patches/conveyor-belt-floor.diff`
**BPS:** `sf3_ggpatch/conveyor-belt-floor/` (simm1.0-.3)
**Changes:** 89 bytes. 06700000-06700053: the new `Player_move`. 06117989, 06117AB9: its address in the
literal pools near `move_P1_move_P2` and `check_damage_hosei` (used by the inlined `move_P1_move_P2`
and `move_P2_move_P1`).
**Recorded:** 2026-11-15 20:16:33

**Mechanism:** The 3rd Strike version of the SMB2, SMB3 and ALTTP "conveyor belt" cheats. Each fight
frame `move_player_work` (`src/plcntset_2.c`) runs `Player_move` (`src/PLMAIN.c`) for each fighter,
then keeps them inside the screen:

```c
Player_move(&plw[0], processed_lvbt(p1sw_0));
if (bg_app_stop == 0 && bg_app == 0) {
    if (set_field_hosei_flag(&plw[0], scrr, 1)) {
        set_field_hosei_flag(&plw[0], scrl, 0);
```

This is a hook: the new `Player_move` moves a fighter who is on the ground 1 pixel to the right
(`xyz[0].disp.pos++`) on every other frame, then runs the original. The screen-edge check after it
stops them at the right edge.

**Evidence:** `Player_move` is only called from `src/plcntset_2.c`. A larger `xyz[0].disp.pos` is
further right (`set_field_hosei_flag` with `ix` 1 clamps against the right edge `scrr`). Only during
a battle (`Allow_a_battle_f`), not in bonus stages, not in the air, and not while throwing or being
thrown (`tsukami_f`, `tsukamare_f`). `sf3_cheat.py` found no moved code or data. `git apply --check`
against main: applies.

**Revisions:** sfiii3nr1 (990512, Japan, no CD) only. Others not checked.

**Caveats:**

- Not tested.
- Always to the right, at 30 pixels a second. Walking right is faster, walking left slower.
- The camera follows, so both fighters drift to the right end of the stage and stay pinned there.
- Also moves fighters who are knocked down, stunned or in the KO animation, as long as they are on the
  ground.
- Can't be built together with "Player 1 freezes the opponent by holding Start" (both diffs add to the
  end of `src/PLMAIN.c`).

## Every attack hits the opponent no matter where they are

**Source diff:** `patches/every-attack-hits-anywhere.diff`
**BPS:** `sf3_ggpatch/every-attack-hits-anywhere/` (simm1.0-.3)
**Changes:** 439 bytes. 06700000-067001A7: the new `hit_check_main_process`. 30 bytes outside: its
address in the literal pools of `Loop_Demo`, `Game2_3`, `Game08` and the `debug_play*_move`
routines.
**Recorded:** 2026-11-15 20:18:01

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

- Not tested.
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

- Not tested.
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

- Not tested.
- Both fighters' projectiles. Kinds 1, 2 (Q? Oro's tengu stones), 4, 10, 11, 13 and 14 are not changed;
  which characters use which kind was not checked.
- The animation runs at its normal rate. A shell's lifetime is in frames, so slow shells that end by
  time go twice as far.
- Homing shells (kind 6) turn at their normal rate, so they may miss more.
