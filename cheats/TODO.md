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

## Damage and health

- [x] Normal hits do double damage (Super Metroid "Samus takes double damage", FF2 "The party's weapon
      attacks do 4 times the damage")
- [ ] Projectiles do double damage too: the same hook on `cal_damage_vitality_eff` (`src/pow_pow.c`)
- [ ] Every hit is a KO (Metroid, ALTTP, OoT and Super Metroid "Every enemy dies in one hit"): set
      `dm_vital` to the full health bar in the `cal_damage_vitality*` hooks
- [ ] Player 1 never takes damage (EarthBound "Enemies never hurt the party", SMB3 "Enemies and spikes
      never hurt the Player"): hook the damage routines, check which side `ds` is
- [ ] The opponent's attacks always miss (FF2 "Enemy weapon attacks always miss the party",
      EarthBound "Enemy attacks always miss"): hit checking in `src/HITCHECK.c`
- [ ] A fighter can't be KO'd: health stops at 1 (Metroid "Samus can't die: her energy stays at 0
      instead"): `src/VITAL.c`, or where damage is taken off
- [ ] Health drains slowly during a round (OoT "Link loses a quarter heart every 20 seconds", the
      Metroid, Zelda 1 and ALTTP drains): the fight frame in `src/Game_Main.c`, health in `src/VITAL.c`

## Gauges

- [ ] The Super Art gauge is always full (FF2 "Spells cost no MP in battle", EarthBound "PSI costs no
      PP", Metroid "Energy pickups refill all of Samus's energy"): `src/spgauge.c`
- [ ] Every hit stuns at once (EarthBound "Every enemy starts each battle feeling strange"): the stun
      value `dm_piyo` in `set_damage_and_piyo` (`src/HITCHECK.c`)
- [ ] Stun never builds up: the same place

## Speed and time

The fight frame runs objects only when `EXE_flag = Game_timer % (SLOW_flag + 1)` is 0 (the KO slow
motion; "Slow motion" in `docs/HOW_THE_GAME_WORKS.md`, `src/SLOWF.c`).

- [ ] The game runs at half speed (Tetris, SMB3, Metroid, ALTTP, Super Metroid and OoT): keep
      `SLOW_flag` at 1
- [ ] Time moves only while a button is held (Metroid, SMB3, ALTTP, SMW and SM64 "Superhot"): set
      `EXE_flag` from the inputs
- [ ] Freeze the opponent while a button is held (OoT "Freeze time for enemies by holding L")
- [ ] Every hit plays the KO slow motion (SMW "Bullet Time for Banzai Bill"): `set_conclusion_slow`
- [ ] The game runs 1.5 or 2 times as fast (OoT "The game runs 1.5 times as fast"): run the fight
      frame more than once per frame
- [ ] The round timer never runs out (SMB3 "Time running out doesn't kill the Player"):
      `Time_Control` (`src/Game_Main.c`), `Check_Time_Over` (`src/manage_2.c`)
- [ ] L pauses, R steps one frame (ALTTP "L pauses the game, R steps one frame"): the 3rd Strike
      version would use spare buttons or player 2's inputs

## Movement

- [ ] Fighters walk twice as fast (Ness, Link, Cecil, SM64 Mario "runs twice as fast", SMB2 walk and
      run faster): the walk states (`check_F_R_walk`, `src/PLS01.c`)
- [ ] Jump again in mid-air (Metroid, SMB2, SMB3 and Super Metroid "Jump again in mid-air")
- [ ] Low gravity: higher, floaty jumps (SMB3 "Low gravity", Super Metroid "Samus jumps much higher",
      SMW "Everything that leaves the ground keeps rising")
- [ ] Fighters face away from each other (SMB2, SMB3, ALTTP, SMW and OoT "Enemies face away", OoT
      "Link always faces away from the way he walks"): the facing flag `rl_flag`
- [ ] Fighters walk through each other (EarthBound "Ness walks through people", ALTTP "Enemies pass
      through Link"): the push boxes
- [ ] All floors are slippery like ice (SMB2, SMB3, ALTTP and OoT): fighters keep sliding after a move
- [ ] The floor is a conveyor belt (SMB2, SMB3 and ALTTP): push both fighters one way each frame

## Attacks and projectiles

- [ ] Every attack reaches across the screen (Zelda 1 "Sword hits every enemy on the screen", ALTTP and
      OoT "Sword hits enemies across most of the screen"): the attack hit boxes ("Hit boxes" in
      `docs/HOW_THE_GAME_WORKS.md`)
- [ ] Projectiles fly twice as fast (SMB1, SMB3, SMW, ALTTP and Zelda 1 "fly twice as fast")
- [ ] Projectiles crawl or stand still (ALTTP "Sword beams fly at quarter speed" and "stay where they
      appear", Zelda 1 "Sword beams and Magical Rod shots crawl")
- [ ] Projectiles pass through each other (SMB1, SMB3, SMW and ALTTP "fly through enemies"):
      `effect_at_vs_effect_dm` (`src/HITEFEF.c`)
- [ ] Hits don't push fighters back (ALTTP and OoT "Enemies don't knock Link back")
- [ ] Blocking works facing either way (Zelda 1 and ALTTP "Shield blocks shots from any direction"):
      `Check_Guard_Type` and the guard checks
- [ ] Throws reach across the screen (ALTTP "Thrown objects hit enemies anywhere"): `Check_Catch`
      (`src/Ck_Pass.c`)
- [ ] Every hit is a SMAAAASH (EarthBound): every hit counts as a counter hit
- [ ] The CPU opponent fires projectiles all the time (ALTTP "Fireballs continuously shot by most
      enemy types", OoT "Every enemy near Link shoots glowing balls", SMW "Bullet Bills fire
      constantly", Zelda 1 "Most walking monsters shoot fireballs"): the CPU logic in `src/Com_Pl.c`

## CPU opponent

- [ ] The CPU opponent stands still (Metroid "Enemies can't move", EarthBound "Enemies on the map
      can't move", SMW "Every Chargin' Chuck stands there and does nothing"): `src/Com_Pl.c`
- [ ] The CPU opponent keeps running away (EarthBound "Enemies on the map always run away from Ness",
      SMB2 "Enemies face and walk away")
- [ ] The CPU opponent moves twice as fast (Metroid "Most enemies move twice as fast", ALTTP "Soldiers
      chase Link at double speed")
- [ ] Every opponent is the final boss, or the next CPU opponent in the list (FF2 "Every battle is the
      one 32 places later", FF2 "rarest enemy group", SMW "Every level is populated with the next
      level's enemies"): "Your path through the CPU opponents" in the tour, `src/next_cpu.c`

## Characters and start-up

- [ ] Gill (and Shin Akuma) can be picked on the select screen (FF2 "New game: <character> is in the
      party"): `src/sel_pl.c`
- [ ] Skip the logos and the attract mode (EarthBound "Skip the logos and the title screen", Super
      Metroid "New games skip the opening cinematic", Metroid "Skip the start jingle")
- [ ] Turn on the debug menu (ALTTP "Turn on the controller 2 debug features", SMW "Free-roaming debug
      mode"): `debug_*` in `src/CMD_MAIN.c`, `src/Entry_dbg.c`
- [ ] Free play (FF2 "Shops sell everything for 0 gil"): "Coins and free play" in the tour

## Sound

- [ ] No music (Metroid, SMB3, ALTTP, Super Metroid, OoT, FF2 and EarthBound)
- [ ] Every stage plays the next song (SMB2, SMB3 and FF2 "Every song plays the next song")
- [ ] Every song plays with the next instrument (FF2, ALTTP, SMW and OoT)
- [ ] Music and sound effects play 2 whole tones higher (FF2, ALTTP and SMW): `sound_note_to_pitch`
      (`src/sound_voice_2.c`)
- [ ] Every sound effect is the next one in the list (FF2, ALTTP and OoT)
- [ ] All music plays faster (SMB1 "All music plays at hurry-up speed"): `bgm_tempo_set`
      (`src/textsound_2.c`)

## Graphics

- [ ] Fighters use colours from past the end of the colour table (Tetris "Level palettes are read from
      past the end of color table"): `Setup_PL_Color` (`src/next_cpu.c`)
- [ ] Fighters are drawn behind the stage (SMW "Ordinary levels draw sprites (and Mario) behind the
      scenery")
