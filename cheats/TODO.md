# Street Fighter III 3rd Strike cheat to-do list

Proposed 3rd Strike versions of the cheats tagged `demo-ready` in the other games
(`~/vhstrace/disassemblies/*/*/cheats/*.md`, 2026-11-15). The source cheats are in parentheses. Source
pointers are starting points, not checked fixes; `functions.tsv` and `docs/HOW_THE_GAME_WORKS.md` have
more. Checked items have an entry in `sf3_patches.md`.

Left out because a fighting game has nothing like them: items, chests, shops, gil, experience and
inventories; Yoshi, power-up suits and Kuribo's Shoe; bushes, pots, blocks, doors, warp pipes, vines
and pits; swimming and walking on water; party members and spells; level and map loading; enemy
spawning and copies; and the Tetris piece cheats.

## Setup

- [ ] Find free RAM for cheat variables (`DCHEAT`/`BCHEAT`), so hooks can keep state.
- [ ] Give each cheat its own code address, so single-cheat patches can be stacked.

## Dead code

Allow players and/or the CPU to use these:

- [x] Att_PL07_BOUND_JUMP, Att_PL10_MACH_SLIDE and Att_RESURRECTION2.
  - [x] Att_RESURRECTION2: "Urien's super art II is his unused Resurrection move".
  - [x] Att_PL07_BOUND_JUMP (and Att_PL07_HOP_JUMP): "Ibuki's light Hien does the hop jump and medium Hien the bound jump, her two
        unused jumps". None of her animations has cues 1, 8 and 10, so the cheat adds new animation
        scripts made from her jump and landing frames.
- [x] Normal_air_paring, a separate air-parry state.
- [ ] check_paring_attack and check_lever_up_attack. No clean cheat (2026-11-15): their tables
      (`asstbl_paring_att`, `asstbl_lever_up_att`) start animations 0-5 ("UP P GUARD") and 18-23
      ("OKIAGARI", attacks while getting up). For every fighter these are placeholders: a single
      2-frame image (script 2, or 18 for Twelve and Shin Gouki), or a few frames of a
      non-attack animation (scripts 0 and 1). Shin Gouki's script 0 is also his Raging Demon
      (25252+PP). Calling the checks would start a move with no attack that ends at once.
- [x] The CMD_MAIN.c debug menu: its top-level entry, debug_scene_outer_dispatch, is never called. So the menu's setup, player setup, the catch and hit-box viewers and the record screens can't be reached either.

## Damage and health

- [x] Normal hits do double damage (Super Metroid "Samus takes double damage", FF2 "The party's weapon
      attacks do 4 times the damage")
- [x] Projectiles do double damage: the same hook on `cal_damage_vitality_eff` (`src/pow_pow.c`)
- [x] Player 1 never takes damage (EarthBound "Enemies never hurt the party", SMB3 "Enemies and spikes
      never hurt the Player"): hook the damage routines, check which side `ds` is
- [x] Health drains slowly during a round (OoT "Link loses a quarter heart every 20 seconds", the
      Metroid, Zelda 1 and ALTTP drains): the fight frame in `src/Game_Main.c`, health in `src/VITAL.c`
- [x] Player 2 automatically parries every attack

## Gauges

- [x] Can always do a super art (FF2 "Spells cost no MP in battle", EarthBound "PSI costs no
      PP", Metroid "Energy pickups refill all of Samus's energy"): `src/spgauge.c`
- [x] Every hit stuns at once (EarthBound "Every enemy starts each battle feeling strange"): the stun
      value `dm_piyo` in `set_damage_and_piyo` (`src/HITCHECK.c`)
- [x] Stun never builds up: the same place

## Speed and time

The fight frame runs objects only when `EXE_flag = Game_timer % (SLOW_flag + 1)` is 0 (the KO slow
motion; "Slow motion" in `docs/HOW_THE_GAME_WORKS.md`, `src/SLOWF.c`).

- [x] The game runs at half speed (Tetris, SMB3, Metroid, ALTTP, Super Metroid and OoT): keep
      `SLOW_flag` at 1
- [x] Time moves only while any controller input is held
- [x] Freeze the opponent while a button is held (OoT "Freeze time for enemies by holding L")
- [x] Every hit plays the KO slow motion (SMW "Bullet Time for Banzai Bill"): `set_conclusion_slow`
- [ ] The game runs 1.25 or 1.5 times as fast (OoT "The game runs 1.5 times as fast"): run the fight
      frame more than once per frame. Not done (2026-11-15): running `Game2_1` twice also pushes every
      sprite twice (`sort_push_request`, `sprite_entry_push_prio`), and the extra copies would need to
      be dropped from the sprite pool, which wasn't worked out.
- [x] L pauses, R steps one frame (ALTTP "L pauses the game, R steps one frame"): the 3rd Strike
      version would use spare buttons or player 2's inputs

## Movement

- [x] Fighters walk twice as fast (Ness, Link, Cecil, SM64 Mario "runs twice as fast", SMB2 walk and
      run faster): the walk states (`check_F_R_walk`, `src/PLS01.c`)
- [x] Jump again in mid-air (Metroid, SMB2, SMB3 and Super Metroid "Jump again in mid-air")
- [x] Low gravity: higher, floaty jumps (SMB3 "Low gravity", Super Metroid "Samus jumps much higher",
      SMW "Everything that leaves the ground keeps rising")
- [x] Fighters face away from each other (SMB2, SMB3, ALTTP, SMW and OoT "Enemies face away", OoT
      "Link always faces away from the way he walks"): the facing flag `rl_flag`
- [x] Fighters walk through each other (EarthBound "Ness walks through people", ALTTP "Enemies pass
      through Link"): the push boxes
- [x] All floors are slippery like ice (SMB2, SMB3, ALTTP and OoT): fighters keep sliding after a move
- [x] The floor is a conveyor belt (SMB2, SMB3 and ALTTP): push both fighters one way each frame

## Attacks and projectiles

- [x] Every attack hits the opponent no matter where they are (Zelda 1 "Sword hits every enemy on the screen", ALTTP and
      OoT "Sword hits enemies across most of the screen"): the attack hit boxes ("Hit boxes" in
      `docs/HOW_THE_GAME_WORKS.md`)
- [x] Every throw grabs the opponent no matter where they are
- [x] Projectiles fly twice as fast (SMB1, SMB3, SMW, ALTTP and Zelda 1 "fly twice as fast")
- [x] Projectiles crawl or stand still (ALTTP "Sword beams fly at quarter speed" and "stay where they
      appear", Zelda 1 "Sword beams and Magical Rod shots crawl")
- [x] no position change from hits
- [x] Blocking works facing either way (Zelda 1 and ALTTP "Shield blocks shots from any direction"):
      `Check_Guard_Type` and the guard checks

## Characters and start-up

- [x] Gill (and Shin Akuma) can be picked on the select screen (FF2 "New game: <character> is in the
      party"): `src/sel_pl.c`
- [x] Skip the logos and the attract mode (EarthBound "Skip the logos and the title screen", Super
      Metroid "New games skip the opening cinematic", Metroid "Skip the start jingle")
- [x] Turn on all debug features (the `DEBUG_*` switches were compiled out; the leftover debug menu is the cheat)

## Sound

- [x] No music (Metroid, SMB3, ALTTP, Super Metroid, OoT, FF2 and EarthBound)
- [x] Music and sound effects play 2 whole tones higher (FF2, ALTTP and SMW): `sound_note_to_pitch`
      (`src/sound_voice_2.c`)
- [x] Every sound effect is the next one in the list (FF2, ALTTP and OoT)
- [x] All music plays faster (SMB1 "All music plays at hurry-up speed"): `bgm_tempo_set`
      (`src/textsound_2.c`)

## To test

Cheats added on 2026-11-15, built but not tested yet. Check each one off (or remove it) after testing.
