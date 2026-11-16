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
