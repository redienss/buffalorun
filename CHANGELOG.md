# Changelog

All notable changes to BuffaloRun since the .NET 8 / MonoGame 3.8.4 port.

## 0.5.6-dev – 2026-08-13 – 2026-08-16

The release that gave the world a sky. Shadows now reach every model, not just the ground; the sun and moon cross it on a day-night cycle; and night and the villages both have music of their own.

### Day & night
- The sun and moon move across the sky by the world's own latitude — sun direction and lighting
  are shader uniforms now, not a fixed constant, and `usgs_world.py` writes
  `TerrainLatitude`/`TerrainLongitude` into `world.cfg` for it to read.
- The sky changes colour with the time of day — blue at noon, red/orange at sunrise and sunset,
  black at night — one gradient shared between the sky sphere, the fog the ground fades into, and
  the screen's own clear colour.
- Night is actually playable now: moonlight raised so the ground reads by it, and the moon sprite
  itself brightened so it looks lit rather than a dim grey disc.

### Shadows
- Every model now casts and receives shadows, not just the ground — a new shared `SceneModel.fx`
  replaces `BasicEffect` across the board, so a rock standing in a mesa's shadow is finally dark.
  A windmill's blades cast as the blade fan they are, not the quad they're painted on.
- Cascaded Shadow Maps: the view range cut into three maps sharing one 2048 atlas, sharp underfoot
  and reaching 600 m, filtered with a jittered PCF grid so the filter's own regularity doesn't
  show along an edge.
- The sun's shadow direction is quantised and held on a 4-second clock rather than following the
  day-night cycle live — what the eye catches is a shadow edge changing, not how far, and a live
  direction was turning the very texel grid the snapping rounds onto.
- The far cascades — which cover almost the whole screen — got a cheaper filter tap count of their
  own: 2.8 ms and 13 FPS back on `groom_lake`'s western village.

### Torches
- A new placeable, throwable item: right mouse button lights or extinguishes the one in hand,
  burning as a spotlight independent of which belt slot it's in.
- Middle mouse button stands any toolbelt item — torches included — upright on the ground it's
  aimed at.
- Torches are scattered into containers and stocked by `world-add-loot`, the same as grass bales,
  TNT and whiskey.

### Buffs
- The buff HUD redesigned: stackable and quieter, tiles stacked soonest-to-end nearest the belt.
- A TNT fuse buff shows how long is left before a lit stick in hand goes off.
- A whiskey buff wobbles the first-person view — a fading sine roll, pitch and yaw — tuned down
  after playtesting so it stays short of seasickness.

### Music
- Village music: 20 pan-flute tracks take over from the soundtrack when the player is near a
  goal.
- Night music: the soundtrack and mixed sources play only the Night set after sunset; a player's
  own custom music always plays regardless.

### The herd
- A buffalo gives up on a destination after three consecutive stalls with no ground covered, so a
  bale thrown somewhere genuinely unreachable stops burning a route search every 6 seconds
  forever — the herd grazes instead.

### Fixed

- The level behind the main menu stopped simulating and drawing once the menu covers it — an
  18 FPS stall.
- A level's terrain build is deferred until it's actually played or edited, so opening one
  without `--start-game` no longer builds a second full-resolution mesh nothing uses
  (menu-idle: 903.7 → 412.0 MB of LOH, 1,105.1 → 636.4 MB of working set).
- A Release build no longer ships the maintainer's home directory path in plaintext —
  `LevelsSourceDir`'s assembly metadata is Debug-only now.
- `release.sh` clears stale publish output before each build, so a file left over from testing
  can no longer ride silently into a release ZIP.

### Changed

- The repository is now split: this game's source stays private, with a public half
  (`redienss/buffalorun`) holding the README, screenshots and releases.

## 0.5.5-dev – 2026-08-06 – 2026-08-12

The release that filled the streamed worlds in. Villages, wild herds, loot and scenery now dress a world tile by tile, and the view itself grows at runtime to match a fast machine's headroom.

### Added

**Adaptive view range**
- The terrain load/unload radii, far plane and fog end all grow at runtime while FPS and system
  RAM have headroom, so a fast machine sees further without every machine paying a wide ring's
  cost up front.
- An FPS breach shrinks the delta back at five times the speed it grew — a low frame rate is felt
  at once, where growing slowly is invisible; a RAM breach only freezes it, since the game's own
  resident set stops growing on its own.
- Two FPS thresholds (65/75 by default) with a dead band between them, so the delta doesn't
  oscillate right at a single line.
- Gated on actually being in a run, so it no longer grows quietly behind the main menu.
- `debug-adaptive-view-range` watches the live delta, FPS and RAM against their thresholds.

**Populating a world**
- `world-add-villages` sites fenced Native American villages on a world's flattest ground, each
  with its own goal, ringed with a tight circle of stones sealed until breached with TNT.
- `world-add-herds` sites wild buffalo herds on flattest dry ground, kept apart from every village
  and from each other.
- `world-add-loot` sets a world's container pool from the console and splits it tile by tile, so
  loot fills correctly as a streamed world's tiles arrive.
- `world-add-tornadoes` adds wandering, randomly-sized tornadoes.
- `world-scatter-groups` dresses a world from named sets of models (stones, plants, cacti, small
  containers, scenery) instead of a list that goes stale as models are added.
- `world-clear` clears a named world's objects on every tile, without it having to be the one
  open.
- Idle wild-herd and tornado tiles now unload like everything else, instead of pinning ground
  resident for the rest of the run.
- The herd bar, the HUD and the completion threshold count the whole world's buffalo now, not
  just the nearest herd.

**Terrain streaming**
- Each tile's step is chosen by measuring its own ground error against the load budget — took
  `groom_lake`'s peak RSS from 7.38 GB to 2.53 GB.
- A tile publishes its edge bands as a file of their own, so a neighbour reads one line instead
  of decoding the whole tile (-20% a tile build).
- Flow fields are windowed to a radius around their goal, so a bale thrown on a big world no
  longer freezes the game, or — with the flow-field debug view on — crashes it out of memory.
- A re-mipped tile rebuilds in place instead of blinking out, and a fresh world opened at a wide
  view radius no longer reads itself in whole.
- Ring-plus-timer streaming replaced with distance-band load/unload; concurrent tile builds are
  capped so an outrun streaming ring can't queue more work than there are cores.
- A cache of each tile's built mesh was tried, measured not to pay for itself on
  `barringer_crater`, and reverted.

**Recording & debug tools**
- `typewriter` types a message letter by letter with a keypress sound and a blinking caret.
- `message` shows a standard fading on-screen message from a script.
- `MouseSmoothing`, an off-by-default first-person look smoothing option for steadier recordings.
- Debug panel font zoom (`[` / `]`) and minimap zoom (numpad `+`/`-`).
- `debug-ram`: system memory used against the machine's total, and how much of that this process
  holds.

**Also**
- `CameraFar` is now derived from the unload radius plus a tile's own diagonal, rather than the
  load radius, so a mountain no longer clips through the far plane as the camera turns to look
  along it.
- Fog now reaches the models as well as the ground, so a distant rock fades into the haze instead
  of reading as a black speck painted on it.
- A bale sensed by any one buffalo now draws the whole herd, not just the animals already within
  smelling range of it.

### Fixed

- Diagonal camera movement (W+A etc.) is no longer √2 faster than a single direction.
- `release.sh`'s previous-tag picker took the second-newest tag instead of the newest, so every
  release's "changes since" notes went back one release too far.
- `usgs_world.py` was writing its heightmaps north-south flipped.

Streamed worlds ship separately from the game — they are far larger than it is, and only the
tiles near the player are ever held in memory; install one by unzipping it into `Content/Levels/`
beside the game.

## 0.5.4-dev – 2026-08-03 – 2026-08-06

The release that let a level outgrow memory. A world is now a grid of heightmap tiles streamed in around the player, so ground that used to run out of memory just runs.

### Added

**Terrain streaming**
- A level can be a grid of heightmap tiles, of which only those near the player are held in
  memory — an 8×8 km world runs where the same ground held whole used to run out of it.
- `TerrainHeightScale` lets a heightmap describe ground taller than the 255 m a single pixel
  value holds — the Grand Canyon is 1500 m from its river to its rim.
- `scripts/usgs_world.py` builds a streamed world from real elevation data around a latitude and
  longitude, keeping its own virtualenv and re-running itself inside it.
- Streamed worlds are never committed. They're gitignored and travel as release assets of their
  own, or are rebuilt from the one command that made them; the hand-authored levels stay in git
  as they were.
- Levels copy to the build recursively, so a world's folder of tiles deploys along with the
  numbered levels.

**Also**
- The built-in soundtrack replaced with six new, more cinematic tracks.
- New cowboy-glove cursor sprites, at 48px and 64px.
- `release.sh` can overwrite an existing release, for when something slipped into the ZIPs by
  mistake.

### Fixed

- `usgs_world.py`'s water-level heuristic no longer floods the Grand Canyon window into a lake.
- `CameraFar` overrides the level's own view distance live now, read every frame instead of once
  as the level opens — `set CameraFar` used to go dead after load.
- Custom MP3s with a short Xing header (written by a variable-bitrate encoder) now play, and a
  track that decodes to nothing is skipped rather than restarting every frame.
- The whiskey buff HUD panel is registered in the layer pipeline, so it actually draws.
- `TntFuseSoundVolumeMax` cut by half — the fuse hiss was too loud.

## 0.5.3-dev – 2026-07-27 – 2026-08-03

The release that gave a run an ending, and TNT to make one happen faster. Before this a level just kept going until you stopped playing it; now the herd is tracked home or lost, and a stick of dynamite pulled from a barrel can clear a way the long route around wouldn't.

### Added

**TNT**
- Fuse, throw and blast: hold to wind up, release to throw a lit stick; it tumbles end over end
  in the air and settles flat where it lands instead of standing bolt upright. The fuse hisses
  and smokes in hand and in flight.
- A growing fireball kills rocks, scenery and buffalo in its area — and the player too, if
  they're standing in it when it goes off. A full-screen flash scales with distance and stacks
  across close blasts.
- The A\* board rebuilds only the region a blast actually touched instead of the whole map
  (~500 ms down to ~1 ms on level 001), deferred until the fireball has finished growing so the
  rebuild's own hitch doesn't land on the same frame as the explosion.

**Containers & the toolbelt**
- Barrels, crates and wigwams hold a 5×5 grid of items — click to take one, shift-click or R to
  take all.
- The toolbelt starts empty. Everything comes from a container now, and a slot carries a quantity
  instead of an infinite supply.
- Whiskey: pick it up, store it, throw and tumble it like TNT, and drink it with the right mouse
  button.
- Levels scatter a configurable number of grass bales and TNT sticks across their containers.

**The herd**
- Routes are answered by a flow field once enough buffalo want the same place, one sweep serving
  the whole crowd instead of a search per animal; a bale still in the air draws nobody, so one
  throw costs one field.
- A stuck or stalled buffalo is freed or re-routed. Wedged against terrain or between obstacles,
  it's put down somewhere it can carry on from; moving but getting nowhere, its route is worked
  out again from where it stands.
- A\* escapes a walled destination as well as a walled start — a bale thrown into a cactus no
  longer drains the whole board every frame.
- Water is a wall to the herd, on the board and underfoot, with a climbable band along the shore
  so an animal that slid down isn't walled in by the very rule that keeps it off canyon walls.
- A waypoint the herd has been shoved past is dropped instead of walked back to.
- A bale is eaten at the pace of ten mouths, however few are actually at it.
- The player can walk through the herd.

**Ending a run**
- The herd bar, above the tool belt, shows what's become of the herd — lost, airborne, in water,
  still out there, saved.
- A level completes at a share of the herd, not all of it, and completing one now asks rather
  than ending the run outright.
- A run that can no longer be completed says so, offering to keep herding anyway.
- A run's summary — where every buffalo ended up, how long the level took — once the player is
  done.

**Also**
- The player has a slope limit of their own, sliding off ground too steep to stand on.
- The herd's A\* board and its flow fields can be drawn in the ground's place, a quad or an arrow
  per cell.
- Level 001 is a maze among the mountains now, dressed with scenery its own terrain chose, with
  choke points opened up and stone walls to clear with TNT.
- New textures for the goal, the grass bale and the wigwam; fixed bottom faces on stone_1–3; a
  new whiskey bottle model; UV fixes on the TNT and the cacti.
- `release.sh`, the script that cuts a release with `gh`, including the ability to overwrite one
  if something slipped into the ZIPs by mistake.
- An Obsidian knowledge vault, with every source file's comments trimmed to how-only and the
  what/why moved into it.

## 0.5.2-dev – 2026-07-23 – 2026-07-27

The release that made the world solid. Nothing was walked through before this one, and nothing
you can see is walked through now — a rock stops you, its overhang does not, and its top can be
jumped onto and stood on.

### Added

**Collision**
- Nothing solid is walked through. `Engine/Maths/BodyCollision.cs` is the object half of what
  `TerrainSlope` does for terrain: a body is a circle on the ground with a height span, and the
  resolution is the shortest way out of a contact. Sliding is not a special case — only the
  normal part of a step is undone, so the part running along an obstacle survives. Steps are
  swept in pieces no longer than the body, and a move too long to be a walk is taken as a
  teleport. The player meets everything; a buffalo meets scenery only, since it has to reach the
  goal it is driven to and walk onto the bales it eats.
- What is solid is declared on the class as `WorldObject.CollisionShape` (`None`/`Box`/`Sphere`)
  rather than tested for by type wherever collision is resolved.
- A model is met by its separate pieces, not by one box around the lot, so a rock built as a
  pillar with a slab over it can be walked under. The whole box is still asked first as the cheap
  rejection. `Settings.PerMeshCollision` turns it off; `B` draws the piece boxes in cyan inside
  the green one.
- A piece is not a mesh: `Engine/Maths/ModelBounds.cs` follows the triangles from vertex to
  vertex, so a model exported as one joined mesh is still met as the several lumps it is drawn
  as. Everything a model measures is measured once and shared by every object built on it.
- The player stands on tops as well as on the terrain. `BodyCollision.SupportHeight` finds the
  highest blocker the footprint is over whose top is within a step of the feet, so a rock, a
  fence or a buffalo can be landed on and stood on instead of being shoved off it. The step
  allowance (`Settings.PlayerStepHeight`, 0.5 m) tells a kerb from a wall, and is zero while
  airborne so an arc is not plucked out of the sky by what it is rising past.
- Thrown things are met by the same shapes and rest on what they land on, so dynamite can be
  thrown into the mine instead of through it (`Settings.ThrownCollisionEnabled`).
- `Engine/Maths/SpatialGrid` is the broad phase, at `Settings.CollisionGridCellSize` (16 m), kept
  in step by every path an object takes in or out of a level; `set ShowCollisionGrid true` draws
  it.
- Picking goes through the same shapes: an object is selected only where a piece box is clicked,
  so a click into the gap under an overhang goes past the rock to the ground.
- The A\* board is marked from a model's pieces too, and only where a piece comes down within
  `Settings.HerdHeadroom` (2.5 m) of the ground under that cell — the herd runs under the slab of
  a table-shaped rock and round its pillar alone.

**The player's body**
- Crouch on left control: the eye slides to 1 m at `CameraCrouchSpeed`, the walk halves, and the
  body shortens with the eye, so a crouched player passes under what an upright one is stopped
  by.
- A jump is forgiving — `JumpGrace` (0.12 s of coyote time) and `JumpBuffer` (0.15 s) — because
  at a run the body is airborne for a frame or two over an edge without the player knowing.
- Two ways round a keyboard that cannot report shift, a letter and the space bar at once: Caps
  Lock latches running on and off in first person, and the right mouse button jumps there too.
- `debug-speed` puts the speed actually being covered on the F7 panel in m/s and km/h;
  `debug-input` shows the movement keys as the game receives them.
- Scriptable walking: `player-walk` walks the player for real over the frames to come and
  `player-walk-sim` runs the same walk to its end on the spot, both reporting
  `arrived`/`blocked`/`ran out of time` with the ground actually covered; `player-jump` presses
  the jump key once and `player-crouch` holds the crouch key down. `PlayerCollisionLog` writes a
  line each time the body meets something new, and `PlayerStatsInterval` traces a walk.

**Music**
- Seven tracks rather than one, with names of their own, and a fresh one drawn at random whenever
  the game changes what it is doing — the menu, a run, the editor — never the track just heard.
- The player's own MP3s play from a `CustomMusic` folder made on the first run with a note inside
  saying what it is for. `Settings.MusicSource` (`soundtrack`/`custom`/`mixed`) and a Music row on
  the options screen choose between the two sets. These do not go through `MediaPlayer`, which
  wants Ogg on DesktopGL: `Mp3Player` decodes with NLayer and streams into a
  `DynamicSoundEffectInstance`.
- F9 and F10 turn the music down and up, F11 skips to another track, and `music` lists the set and
  puts one on. `debug-music` puts the track, its file, its length, how far in it is and the volume
  on the F7 panel.

**The herd**
- An idle herd grazes rather than standing still: each animal ambles to a spot within
  `HerdGrazeRadius` of where the herd came to rest, stands about, and picks another. They wander
  round the point the herd stopped at, not round their own centre, so a herd cannot drift across
  the map chasing itself.
- A buffalo turns at the pace an animal turns — `Settings.BuffaloTurnSpeed`, 180 degrees a second
  — and one place decides which way it faces. An animal shoved about between two rocks used to
  snap round with a velocity that reverses several times a second, and looked like it was having
  a fit.
- `herd-goto <x>,<y>` sends the whole herd somewhere past every bale on the level, and
  `set MouseHerdControl 1` puts the same order on the left mouse button.

**The tool belt**
- Ten slots along the bottom of the screen during a run, taken with the number keys, each holding
  a model whose thumbnail is its tile. What is in hand gates what the player can do: a throwable
  tool is wound up by holding the left button and launched along the aim, with a power ring on
  the cursor. `E` picks a thrown thing back up — the one being *looked at*, not the nearest.
- A stick of dynamite to go with the grass bale, modelled, textured from a painted atlas, and
  built procedurally by `blender_models/tnt_build.py`.
- The mouse wheel walks the belt only in first person; whenever the orbit camera is the one
  looking, the wheel is its zoom.

**Content and levels**
- Levels are PNG rather than BMP — lossless, the same height bytes, about a tenth of the size on
  smooth terrain (18 MB of heightmap down to 8.9 MB).
- A level can override any setting in its own `<name>.cfg`, applied as the level opens and undone
  when the next one opens, which is where a water line and the splat bands belong.
  `level-cfg-save` and `level-save-with-cfg` author it from in-game.
- Objects stand on the bottom of their bounding box rather than on their origin, so a model built
  around its centre of gravity rests on the ground instead of sinking to its middle. `B` draws
  the boxes, `O` the spheres.
- The mine was stood on the ground, split into its pieces, its rock cut into walls so it can be
  walked into, and its door frame closed up; `stone_3` was split by hand.
  `blender_models/ground_and_split.py` does both jobs headless to any model.
- `scripts/texture-pad.py` pads a texture outward into its background, so a UV that lands off its
  island finds the colour beside it rather than black — the black band round `cactus_3`'s trunk
  is gone.

### Fixed

- `set CameraWalkSpeed 10` reported the new number while changing nothing: everything about the
  player is now pushed to the camera every frame by `WorldLayer.ApplyPlayerSettings` rather than
  copied once at start-up.
- Standing up on a rock dropped the player off it — the feet were derived from the eye, so a
  change of eye height moved them.
- The near clip plane is held inside the body's radius, or the eye clips away the very surface it
  has stopped against; each camera has its own near plane now.
- Dynamite and grass bales placed in the level editor could not be picked up and stood in the way
  like rocks. `Objects/Spawn.cs` is the one place that decides what a model's name means, so a
  stick is a stick wherever it comes from.
- An object taken out of a level is taken out of everything that has a record of it —
  `Level.DeleteObject` is the only door out. Dropping one from the list alone left an invisible
  rock standing where a bale had been picked up.
- The far edge of a level stands on its own ground rather than at zero.
- A model measured its bounds by reading vertex buffers back off the GPU, once per object; it is
  measured once per model now.

### Changed

- The Z-buffer dump moved from F11 to `Z`, which F11 took for skipping a track.
- `herd-stats` reports a standing herd as idle rather than as fifty of them running, and counts
  the grazers.
- Levels 005 and 012 are in the tree; 006–011 are scratch heightmaps and are not packaged.

## 0.5.1-dev – 2026-07-20 – 2026-07-23

### Added

**Terrain at one metre**
- A level's heightmap BMP is now the map itself: one pixel is one square metre, pixel `(x, y)` is the height at world `(x, y)`, and levels carry their own size (a 1024×512 BMP is a 1024×512 m level). `MapSizeX/Y` and the ×5 map scales are gone, and the bitmap is no longer read transposed.
- Heights are 24-bit fixed point, `(R<<16 | G<<8 | B) / 0x010101` metres, so gentle slopes no longer come out as a staircase of metre-high steps. A plain grey pixel still reads back as its byte value.
- The mesh moved into vertex/index buffers with 32-bit indices (the old 32k-vertex ceiling is gone), and the A\* board got its own 5 m grid (`Settings.BoardCellSize`) so search cost no longer follows terrain detail.
- The stock levels were converted with `scripts/level-upscale-to-1m.py`; `level-new` takes an optional size, `level-new 1024,512`.

**Terrain sculpting**
- A sculpt brush in the level editor: raise and lower the ground with a circular plateau falloff, the direction latched with Caps Lock, drawn as a filled band on top of the terrain.
- Three shaping tools beside it, each usable with the mouse and from the console — **flatten** (levels a circle to one height), **smooth** (eases a circle toward its local average, rounding off hard bitmap edges), and **ramp** (grades a straight slope between two points, click-dragged with a band drawn along the ground).
- `sculpt <x>,<y>,<radius>,<amount> [<hardness>]` runs the brush from the console, so shaping a level can be scripted; it reports the height the centre ended at.
- The palette's sculpt tile is now four, each a drawn glyph in its own brush colour, and the brush ring takes the same colour.

**Ground texturing and water**
- The terrain is textured by height with a four-material splat map — canyon rock, gravel, grass and river-bed sand — generated from the heightmap and never authored. It follows the brush region by region, and `level-save` writes it out as `<level>_splat.png`.
- Materials are projected from all three axes rather than straight down, so a near-vertical canyon wall is no longer a smear; texture reads below an 8-bit channel's weight are skipped to keep the cost down. Band edges fade over a couple of metres and are moved by seeded Perlin noise.
- A translucent, textured water surface at the water line: one flat plane across the level, depth-tested against the terrain, so the same sheet is a river in a delta and a lake in a hollow. It follows `splat-water-level`.
- The surface has its own shader (`WaterSurface.fx`) — two layers of the ripple texture at different offsets, scales and drift directions, averaged, so no single direction of travel or texture repeat dominates. The shader carries the tint, the opacity and the terrain-matched planar fog.

**Console**
- A file inbox: the console watches `console.in` next to the executable, runs what is written there, empties it, and appends the output to `console.out` — so one running game can be driven and read for as long as it stays up.
- Level and object commands: `object-add`, `object-list`, `object-move`, `object-delete` (nearest-within-ten-metres, refusing rather than reaching across the level), `model-list`, `level-info`.
- Camera commands split by camera: `camera-position` for the first-person eye, `camera-target`/radius for the orbit camera, each refused while the other is active.
- `set`, `get` and `settings` reach any setting by name through the settings file's own parsing (vectors included), `settings-save`/`settings-load` write and re-read the file, and `tool-select`/`tool-list` pick from the editor palette — so a test no longer needs a rebuild to try a setting or a tool.
- `wait` holds back the rest of a script, making a script a queue rather than a single frame's loop; `screenshot [file] [scale]`, `console-show`/`console-hide`, `water-toggle`, and every splat-mapping knob got a command.
- `perf-sample` times frames from a stopwatch over a few seconds and reports best, worst and average — the fixed time step made the old figures read 60 however long a frame took.
- Console editing: a caret with Left/Right/Home/End/Delete and auto-repeat on every editing key, wheel scrolling of the output three lines a notch, PageUp/PageDown by the screenful, and a hidden-line count on the prompt while scrolled back.
- `help <command>` answers for one command, with Tab completion; the help text and the completion list now come from one table.
- Every console command is logged with its source (`console`, `--console-script`, `console.in`).

**Command line and display**
- CLI arguments for the display mode (`--display-screen`, `--display-resolution`, `--display-fullscreen`, `--display-window`) and for launching into a specific screen, plus `--console-script` for running console commands at start-up (semicolon-separated or from a file, run once the scene has settled).
- A display options screen on the main menu — resolution, full screen, and monitor choice, with clickable arrows — and player settings that persist across runs in the user's config directory.
- A framed debug panel under the level map, in the console's font, with a switch per entry: `debug-fps`, `debug-update`, `debug-draw`, `debug-load`, `debug-cursor`, `debug-pause`.
- The help screen is a modal on F1; the first-person camera jumps with Space; each buffalo has its own top speed.

**Content**
- Level 002, a canyon route with a start pen, a corridor past a tornado, a rock plaza, a climb and a village around the goal (25 buffalo, 76 objects) — built entirely through the console, with `scripts/level-002-*.py` kept as the worked example.
- Level 003, a 1024 m level reworked with the new tools into flat-topped mesas between water channels.
- The README's screenshots are retaken by `scripts/screenshots.sh`, which drives the game through the CLI; Grass Bale concept art; a release skill capturing the GitHub Releases workflow.

### Fixed

- The editor cursor is picked by walking the ray across the heightmap instead of reading the depth buffer, so the brush lands under the cursor at any range — and the whole-terrain redraw and readback stall behind it are gone.
- Camera turning was jerky on long frames: the mouse is read once at the top of the frame, and re-centring records where the cursor was put rather than asking the window system where it landed.
- `CameraNear`/`CameraFar` were never applied to anything. The frustum is now set from the settings and the far plane worked out per level, so a 1024 m level is no longer cut off at a kilometre and fog ends where the view does.
- The map panel is drawn as a map — world X across, world Y up — rather than as the level bitmap, which mirrored the level and turned the heading arrow the wrong way. It also updates from the live terrain instead of the saved BMP.
- A big brush costs one mesh rebuild per frame rather than one per stroke, and only the brush's rectangle is re-meshed and re-uploaded (1.5 ms rather than 51–204 ms), so sculpting cost no longer follows the level's size. The map panel stopped rebuilding itself every frame of a stroke.
- Cursor picking is skipped while the camera is being swung, where the answer was never used.
- A buffalo with no goal stays where it was put.
- Snapshots are named after the time they were taken, so a new session no longer overwrites the last one's screenshots and depth dumps.
- Ground textures are scaled to what is in them — sand, gravel and grass several times finer than canyon rock.
- Two latent `Board` bugs that only bite on non-square grids.

### Changed

- `FogEnd` is retired as a setting; `FogStart` goes back to a fixed 500 m.
- A new level starts at a height you can dig down from rather than at the floor.
- The console backdrop is darker (0.7, and a setting) so its text reads over the editor palette; the editor palette defaults to two columns.
- The log file moved to the user's config directory beside the settings.
- Editor model previews are drawn double-sided; the menu backdrop stretches to the viewport; full screen fills the screen at lower resolutions.
- `InactiveSleepEnabled` is a setting — the idle between frames while unfocused caps the frame rate at about 50, which made every measurement taken on a second screen a measurement of that idle.
- The four ground textures are photographs and are not tileable; the seam shows on flat ground (noted, not fixed).

## 0.5.0-dev – 2026-07-15 – 2026-07-20

### Added

**Command console**
- Quake-style console sliding out from the top, bound to `` ` ``, taking up 75% of the screen height.
- Command history with the up/down arrows, tab-completion, and auto-repeat on held Backspace.
- Level management commands: `level-load`, `level-list`, `level-new` (creates a flat level), plus the rest of the level command set.
- Dedicated larger font so the text renders crisply.

**Level editor**
- Model palette replaced by a thumbnail grid; the hovered thumbnail rotates, and clicking a selected tile toggles it off.
- Add mode merged into edit mode, with a single translucent panel and header for both.
- Drag-and-drop for placed objects, arrow-key rotation, and scaling of the selected object (Backspace resets scale).
- Objects preview as a translucent buffalo rather than a placeholder sphere; sphere and skysphere are hidden from the palette.
- The first-person camera can now place models.
- The editor always opens on the third-person camera, reloads the level when entered after a game, and clears its selection when returning to the menu.
- In-editor saves sync back to the source tree.

**Level map (minimap)**
- New panel in the top-right corner, drawn the same way round as the source `.bmp`, coloured as desert instead of greyscale, and stretched over the level's own height range.
- Markers for the player's position, the buffalo, the goal, and the direction the camera is looking.

**First-person camera**
- New first-person camera, switchable with `C`, with a dot cursor (the hand cursor stays on the menu screens).
- Eye height raised to 2.0; holding Shift doubles movement speed.
- Levels now start in first person, inside the herd, facing the goal.

**Main menu and presentation**
- Main menu shown at startup, using the menu concept art as its background at full brightness.
- The result message now fades out before the menu appears; on-screen messages last twice as long.
- Exit confirmation dialog — Esc no longer quits directly, and instead steps back through help and editor modes first.

**Camera and controls**
- RTS-style edge scrolling.
- Cursor confined to the window in full screen.
- Full-screen on the main monitor at native resolution.

**Content**
- New barrel model (with `barrel.blend` source), placed in level 001.
- Level 001 built out into a full playable level; level 999 added as an object grid.
- Improved textures for the windmill, fence, crate, cactus_1, agave, vulture, and barrel.
- Materials now render from the `.fbx` files instead of being overridden in code; per-model base scales baked into the models themselves.
- Translucent rendering for the tornado and bottle, drawn after the opaque scene in two culling passes.
- 10 gameplay screenshots, H.A.A.R.B. concept art, and an expanded README.
- `LICENSE.md` (personal-use, source-available license).

### Fixed

- Buffalo no longer climb steep walls and get flung off; they now slide along canyon walls instead of stopping dead.
- Buffalo that wedge themselves against terrain are freed (and the event is logged); buffalo standing on ground they shouldn't be are moved off; buffalo stuck on wall cells are unstuck.
- Only genuinely falling buffalo are culled, not ones merely descending a slope.
- Object rotation is no longer lost on level save/load.
- Level file loading handles line endings and is locale-safe when parsing numbers.
- Object picking / BVH fixed by initializing `InitialBoundingSphere`.
- Camera kept above the terrain with height-scaled clearance, target clamped to the map area, and constrained to the upper hemisphere.
- The flock no longer runs to the click point while in edit mode.
- Editor preview no longer tinted by the depth buffer; editor-placed objects no longer inherit the preview's translucency.
- Converted screenshots given a proper JFIF header.

### Changed

- Polish identifiers and comments translated to English throughout the code and content.
- `Controler` misspelling corrected to `Controller` (namespace and usings).
- Levels renamed to short numeric names (`level_001` → `001`); `load-level` renamed to `level-load`.
- Audio track swapped to "Buffalo Frontier"; `ontario.mp3` removed.
- Editor HUD moved top-right, drawn in white with the console font.
- Codebase formatted to Microsoft C# style with an `.editorconfig`; line endings normalized to LF and UTF-8 BOMs stripped.
- XML doc comments added across the engine, terrain, and game projects.
- Human-readable grayscale depth-map dump added for debugging.

### Removed

- Unported `BuffaloRun.Audio` prototype, stock XNA `Graphics/Primitives` sample, abandoned `Terrain.cs`.
- Unused content: alternate level BMP, orphan model textures, built-but-unused textures.
- Stray binaries committed to the repo (`firefox.exe`, `fbxconv_win64.exe`, `fxccs.zip`).
