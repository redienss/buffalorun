# Changelog

All notable changes to BuffaloRun since the .NET 8 / MonoGame 3.8.4 port.

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
