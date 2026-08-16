# BuffaloRun

A 3D buffalo-herding game written in 2011 in C# on Microsoft XNA 4.0 — and brought back to life in 2026 as a cross-platform **.NET 8 + MonoGame (DesktopGL)** game that runs on Linux and Windows.

![BuffaloRun's main menu — a chief pointing a startled young hunter towards a herd of buffalo in the canyon](screenshots/menu.jpg)

Herd the buffalo across a desert canyon, past cacti, wigwams, windmills and tornadoes, into the goal. Lead them with grass bales thrown from your own hand, and keep them off the rocks and out of the funnels.

Under it: heightmap terrain at one metre a pixel, textured by height with a four-material splat map and simplified where the ground is flat; a flocking AI for the herd with A\* routing that goes *under* the overhang of a rock rather than around it; solid-body collision for the player, the herd and anything thrown, met by a model's separate pieces rather than by one box around the lot; a skinned, animated buffalo; a seven-track soundtrack that also plays your own MP3s; and an in-game level editor with terrain sculpting — all of it drivable from a console, a command line, or a file the game watches.

## Credits (2011)

- **Tomasz Szneider** — engine, game, audio
- **Weronika Bałaban** — terrain generation (`BuffaloRun.Terrain`)
- **Bartłomiej Szneider** — 3D models (Blender)

## Playing it

Built for Linux and Windows on the [Releases page](https://github.com/redienss/buffalorun/releases) — download the ZIP for your system, unpack it and run `BuffaloRun` (`BuffaloRun.exe` on Windows). Nothing else is needed — the build is self-contained, so there is no runtime to install.

Worlds ship as separate downloads beside the game, because one is 150–800 MB against the game's 110. Unzip a world into `Content/Levels/` next to the levels that came with it, and it turns up in the level list. `scripts/usgs_world.py` in this repository builds a world of your own from real USGS elevation data — give it a latitude, a longitude and a size, and it fetches the ground and cuts it into the tiles the game streams.

## Source code

The engine, the game, the terrain library, the 3D models and the level authoring live in a **private** repository: [redienss/buffalorun-src](https://github.com/redienss/buffalorun-src). See [`src/`](src/) for what is in it. This repository is the game's public face — what it is, what it looks like, and where to get it.

## Controls

Press `F1` in game for the help screen, which lists every binding and stays current with them. The essentials: `WASD` moves the camera and `C` switches between third and first person (`Space` jumps, `Shift` runs, `L-Ctrl` crouches — which lowers the whole body, not just the eye, so a crouched player passes under what an upright one walks into — and `CapsLock` latches running on so a jump at a run needs one key fewer); the right mouse button turns the camera in third person and jumps in first (where the mouse looks about on its own), and the wheel zooms it; while a level is being played in first person the wheel walks the tool belt along the bottom of the screen instead, whose ten slots are also taken with `1`–`9` and `0` — hold the left button to wind up a throw of whatever is in hand (the grass bale or a stick of dynamite) and let go to launch it, with `E` picking a thrown bale or stick back up when you are looking at one within reach, whatever is in hand; `M` toggles the level map, `P` pauses; `F7` shows the debug panel and `B` and `O` draw what is solid — the box around each model, the cyan box of each of its pieces, and the bounding spheres; `F9` and `F10` turn the music down and up and `F11` puts another track on. Drop your own `.mp3` files in the `CustomMusic` folder beside the executable (it makes itself on the first run) and the *Music* row in Options plays them instead of the soundtrack, or mixed in with it. `` ` `` (backtick) opens the console, `F12` takes a screenshot and `Z` dumps the depth map used for mouse picking, both written next to the executable (`Screenshot_20260721_104221_001.png`, `DepthMap_…`) and timestamped so one run never overwrites another's. `Esc` steps back one layer at a time — help, then the editor, then the exit confirmation, which during a run offers the main menu as well as the desktop.

The level editor is reached from the main menu. Its palette places props by click, drag moves them, the arrow keys rotate and scale, and its first four tiles are the terrain tools — a sculpt brush (hold the left button to raise the ground, `Shift` to lower it, or `CapsLock` to latch the direction, with `Up`/`Down` sizing it), and flatten, smooth and ramp beside it. Levels are saved with `End` and reloaded with `Home`.

Display settings — monitor, resolution, full screen, terrain noise and where the music comes from — live on the main menu's **Options** screen, and are kept in `buffalorun.cfg` in the user's config directory (`~/.config/buffalorun/` on Linux, `%APPDATA%\BuffaloRun\` on Windows) along with `buffalorun.log`, so they follow the player rather than the installation.

## Command line

The game normally opens on the main menu, but arguments can take it straight to any screen, override the display mode for one run, drive it through console commands and capture the result — enough to check a change without touching the window. `--help` lists everything; these are the parts worth knowing.

**Opening a screen directly:**

```bash
BuffaloRun --level-editor          # or --menu, --menu-options, --help-screen,
                                   #    --exit-dialog, --start-game, --console
BuffaloRun --level 999             # load a level first (Content/Levels/999.png)
```

**Overriding the display mode**, for this run only — the settings file is left alone (screens are numbered as the Options screen numbers them):

```bash
BuffaloRun --display-screen 2 --display-resolution 1920x1080 --display-fullscreen
BuffaloRun --display-screen auto --display-window
```

**Capturing unattended:** `--screenshot <file>` writes a PNG of the whole window — menus and modals included, unlike the `F12` screenshot — once the scene has settled, and `--exit-after <seconds>` quits on its own:

```bash
BuffaloRun --level-editor --screenshot editor.png --exit-after 2
```

### Running scripts

`--console-script` runs the same commands the in-game console takes (`` ` ``), so a run can be set up from the shell instead of typed by hand. Give it commands inline, separated by `;`, or a file holding one per line:

```bash
BuffaloRun --console-script "level-load 999"
BuffaloRun --console-script "level-load 001; screenshot; level-load 999; screenshot; exit"
BuffaloRun --console-script script-file.txt
```

```
# script-file.txt — blank lines and # comments are skipped
level-load 001
screenshot shot-001.png
level-load 999
screenshot shot-999.png
exit
```

How it behaves:

- The script runs once the scene has settled — about a second in — so what it acts on and captures is a fully built world, and it runs after any screen argument, so its commands have the last word.
- Console output goes to **stdout**, so the shell sees the transcript even though the console isn't on screen.
- The first command that fails stops the script and exits with code 1; a script that runs through leaves 0.
- `--console-script` can be repeated, and the commands run in the order given.
- `--screenshot` fires at a fixed moment after start-up, which is **before** a script that holds itself back with `wait` has done anything. A shot of a scene that needs a moment to happen — a bale in flight, a herd that has to graze first, an eye placed after the level's opening banner — should end its script with the console's own `screenshot <file>` instead, which takes the picture exactly where the commands have got to. `scripts/screenshots.sh` does it that way.
- `object-add` takes the same fields, in the same order, as a row of the level's `.txt` — but separated by commas or spaces, since the file's semicolons separate one command from the next in a script. As when a level file is read, the object is stood on the terrain, so the `z` given is reported back as whatever the ground there allows.
- The `camera-*` commands frame a shot without flying the camera there by hand, so a script can capture the same view of several levels. Switch camera first (`camera-tpp` / `camera-fpp`): a command belonging to the other one is refused rather than quietly setting a camera nobody is looking through. In first person, place the eye before aiming at a target — the angles are worked out from where it stands, and a target at eye height (`camera-target 0,0,2`) looks level at the horizon. Values outside the camera's limits are clamped, and each command reports what the camera actually ended up with. Decimals use `.`, whatever the machine's locale.

### Driving a game that is already running

`--console-script` is fixed at start-up, so trying another camera angle means another launch. The console also watches a file next to the executable — **`console.in`** — and runs whatever is written to it, empties it, and appends the output to **`console.out`**. One game can therefore be driven and read for as long as it stays up:

```bash
echo "level-load 999; camera-target 250,250,0; camera-radius 120" > console.in
sleep 1 && cat console.out          # what the commands said, errors included

echo "screenshot /tmp/shot.png" > console.in     # look, adjust, look again
echo "exit" > console.in                         # and close it when done
```

The file is read every half second (`ConsoleInputPollSeconds`), left alone until the scene has settled, and emptied before its commands run, so a command that quits the game cannot leave them to run again on the next start-up. A failed command stops the rest of that batch, as in a script. Both names are settings — `ConsoleInputFile` and `ConsoleOutputFile` — and setting either empty turns that half off.

Every command the console runs is logged with where it came from — typed at the prompt, from `--console-script`, or from the inbox — so a session can be followed as it happens with `tail -f ~/.config/buffalorun/buffalorun.log`:

```
13:21:02  --console-script: camera-info
13:21:04  console.in: level-load 999
13:21:04  console.in: bogus
13:21:04  console.in: bogus -> failed
```

Commands worth knowing in a script — `BuffaloRun --console-script "help; exit"` prints the full list, so it stays current as commands are added:

| Command | What it does |
|---|---|
| `level-load <name>` / `level-list` | load a level, or list the available ones |
| `level-start [name]` / `level-edit` | play a level, or edit it |
| `level-new [<sizeX>,<sizeY>]` / `level-save [name]` / `level-clear` | create a flat level (sized in metres, 512×512 by default), save one, empty one |
| `sculpt <x>,<y>,<radius>,<amount> [<hardness>]` | raise or lower the terrain in a circle, in metres — the editor's brush, from a script |
| `object-add <model> <sclX>,<sclY>,<sclZ>,<rotV>,<rotH>,<posX>,<posY>,<posZ>` | add an object, taking the fields a level file's row holds |
| `model-list` | list the model names `object-add` takes |
| `screenshot [file] [scale]` | save a PNG of the window; numbered and timestamped if no file is given. `scale` resizes the image with a Lanczos filter, e.g. `screenshot shot.png 0.5` on a 1920x1080 window writes 960x540 |
| `camera-tpp` / `camera-fpp` / `map-toggle` | switch camera, show or hide the level map |
| `camera-target <x>,<y>,<z>` | look at a place: the third-person camera orbits it, the first-person one turns to it (both angles worked out from the point) |
| `camera-radius <units>` | third person: how far out the camera sits |
| `camera-position <x>,<y>,<z>` | first person: where the eye stands (its height follows the ground) |
| `camera-angle <h>,<v>` / `camera-angle-h <deg>` / `camera-angle-v <deg>` | turn and pitch, on whichever camera is active |
| `camera-info` | print the active camera's placement, to find values worth scripting |
| `console-show` / `console-hide` | show or hide the console itself, so a script can capture a screen with or without it |
| `player-walk [<from>] <to>` / `player-walk-sim` | walk the first-person player there through the same keys a played frame uses — for real over the frames to come, or run to its end on the spot. Reports `arrived` / `blocked` / `ran out of time` with the ground actually covered, so sliding past a rock shows as a walk longer than the straight line |
| `player-jump` / `player-crouch [0\|1]` | press the jump key once; hold the crouch key down |
| `herd-goto <x>,<y>` / `herd-stats` | send the whole herd somewhere past every bale on the level (`-` gives it back its nose), and report what it is doing |
| `tool [<slot>] [<name>]` / `throw [<power>]` / `pick-up` | the player's tool belt: what is on it, what is in hand, and using it |
| `sculpt` / `sculpt-flatten` / `sculpt-smooth` / `sculpt-ramp` | the editor's terrain tools, from a script |
| `terrain-debug [<mode>]` / `terrain-simplify [<m>]` | draw the terrain as wireframe, chunks, merged blocks, slope or the pathfinding board; merge the mesh to within so many metres of the heightmap |
| `music [<n>\|next\|scan]` | what is playing, and what else there is |
| `exit` | quit the game |

## Screenshots

The shots below are taken by `scripts/screenshots.sh`, which drives the game from the command line — opening each screen, loading a level, sculpting a hill or throwing a bale to make the scene, framing the camera and capturing the window — so the whole set can be retaken after a visual change and compared like for like. Nothing it does is saved: the hills it digs and the tornado it drags across the map live in that one launch.

### Screens

| | |
|---|---|
| ![The options screen: monitor, resolution, full screen, terrain noise and the music source, over the dimmed main menu](screenshots/options.jpg) | ![The help screen: mouse actions, the sculpt tools and every key binding, in three columns](screenshots/help.jpg) |
| ![The drop-down console listing its commands over a level](screenshots/console.jpg) | ![The exit confirmation dialog, NO selected](screenshots/exit-dialog.jpg) |

### The terrain

One pixel of a level's heightmap is one square metre, and four ground materials are blended over it by height above the water line — sand at the water, then grass, gravel and bare canyon rock, each laid on from all three axes so a vertical wall is not a smear.

| | |
|---|---|
| ![A kilometre of mesas with water running in the channels between them, the ground shading from rock through gravel and grass to sand at the water](screenshots/terrain.jpg) | ![A river through the canyon at close range: sand along the banks, grass above it, then gravel and rock](screenshots/water.jpg) |

The mesh under it is simplified where the ground is nearly flat, and cut into chunks for culling. Here the same view is drawn as its triangulation and as the blocks the simplifier merged the ground into — 2.09 M triangles down to 108 k, a 94.8% reduction, counted on the panel beside them.

| | |
|---|---|
| ![The same landscape as a wireframe: dense triangles over the ridges, coarse ones across the flats](screenshots/terrain-mesh.jpg) | ![The same landscape with every merged block in its own colour, a patchwork that is coarse on the flats and fine on the ridges](screenshots/terrain-blocks.jpg) |

### The level editor

A level is a heightmap and a list of objects. The palette on the left places the objects; its first four tiles are the terrain tools — a sculpt brush that raises and lowers the ground, and flatten, smooth and ramp beside it.

| | |
|---|---|
| ![The editor over the goal: the model palette on the left, and a village of tipis, a windmill, crates, barrels and fences around the target-shaped goal](screenshots/editor.jpg) | ![A hill raised out of the plain with the sculpt brush, its ring drawn on the ground, and a hollow dug beside it that has filled with water](screenshots/sculpt.jpg) |
| ![Standing beside the dug hollow: it is below the water line, so it is a pond, with the river beyond it](screenshots/sculpt-water.jpg) | ![Inside the gold mine, looking back out of its doorway at the village](screenshots/mine.jpg) |

### What is solid

A model is met by its separate pieces rather than by one box around the whole of it — so a rock built as a pillar with a slab over it can be walked under, and the herd's pathfinding board walls off the pillar alone.

| | |
|---|---|
| ![A giant mushroom-shaped rock with the green box around the whole model, mostly fresh air, and cyan boxes hugging the pillar and the slab separately](screenshots/collision-boxes.jpg) | ![The same rocks under the pathfinding board: green where a buffalo may walk, red squares only under the pillars](screenshots/astar-board.jpg) |
| ![A forest of the same rocks seen from the ground, each slab standing well clear of head height](screenshots/under-the-rock.jpg) | ![The debug panel with the frame rate, the update and draw times, the player's real speed, the music and the terrain's own numbers](screenshots/debug-panel.jpg) |

### The herd

| | |
|---|---|
| ![Fifty buffalo grazing, spread across a pocket of the canyon](screenshots/herd.jpg) | ![Eye level among the buffalo, faces and horns filling the frame](screenshots/first-person.jpg) |
| ![First person in the village, a grass bale in flight from the tool belt along the bottom of the screen](screenshots/toolbelt.jpg) | ![A tornado bearing down on the grazing herd, one buffalo already inside the funnel](screenshots/tornado.jpg) |

## Concept art

Ideas for future additions to the game.

### Grass Bale
A bundle of fresh grass used to lure buffalo away from threats.
![Grass Bale](concept_arts/grass_bale.png)

### TNT

A throwable explosive for clearing rocks and opening a path through them — and a danger to whoever throws it. The stick, the belt slot and the wind-up throw are in the game already; the rest of the sheet is what it is meant to become.

Take it from belt slot `2`, set the fuse with `Page Up` / `Page Down` (5–30 seconds), light it with the right mouse button, then hold the left button to charge the throw — the ring around the crosshair fills as it winds up. The stick flies in a ballistic arc, spinning and trailing smoke, and when the fuse runs out it goes up in a fireball: rocks inside the blast are destroyed, and their fragments are thrown off along ballistic paths of their own, each drawing a smoke trail so you can see where it is going. Shrapnel takes health off the player and the buffalo without necessarily killing either outright — and a stick thrown at the herd launches the animals into the air, which does kill them when they land.

![TNT concept sheet — the tool belt, the fuse timer, lighting the fuse, the charged throw and its ring, the ballistic arc, the explosion, destroyed rocks, shrapnel and smoke trails, and the damage zones](concept_arts/tnt.png)

### H.A.A.R.B. — Highly Active Auroral Reinforcer for Buffalos

A machine used to eliminate tornadoes by shooting and deflecting energy beams from the ionosphere. It consists of an array of five satellite dishes — laid out `(H)(A)(A)` over `(R)(B)`, each dish marked with its letter of the acronym — standing on a horizontally rotating base, with each antenna able to tilt vertically.

![H.A.A.R.B. concept art — a five-dish array firing an energy beam that neutralizes a tornado](concept_arts/haarb.png)

### Revolver

A six-shooter for the tool belt, handled two ways. **Classic mode** is the one every shooter has: left button fires, `R` reloads the lot. **Simulation mode** makes you account for every round — the middle button swings the cylinder out and back, `R` feeds it one cartridge at a time (hold it to go on loading), the right button brings the iron sights up, and there is no crosshair to aim by without them. A chamber you never got round to filling answers the trigger with a click and nothing else.

The cylinder sits in the corner of the screen as its own dial: gold for a loaded chamber, dark for an empty one, red for the one under the hammer. The mouse wheel spins it left or right — worth nothing at all in a fight, and there for the same reason a cowboy does it. Which corner the dial and the gun occupy follows a handedness setting, and the whole of simulation mode is optional, chosen from the game's settings; taking the harder handling is meant to pay, in experience, loot, money, achievements and a leaderboard of its own.

What it is aimed at is not the herd. A tornado is not the only thing that will threaten the buffalo — bandits who cut animals out and drive them off are the gun's real quarry — and a bullet is also a way past a lock or a rope rather than only a way to hurt something.

![Revolver concept sheet — the belt slot and cylinder-status dial, the open-cylinder / insert-rounds / close-cylinder / aim-and-fire sequence, the classic and simulation control sets, the cylinder spin, and the rewards and settings for simulation mode](concept_arts/revolver.png)

## New since the port

Beyond the 1:1 restoration, the 2026 version adds — newest first, and [CHANGELOG.md](CHANGELOG.md) has the full account:

**A world you cannot walk through**
- **Solid-body collision** for the player, the herd and anything thrown. A body is a circle on the ground with a height span, and a step is resolved as the shortest way out of a contact — so sliding along an obstacle falls out of the maths rather than being a special case.
- **A model is met by its pieces**, not by one box around the lot: you can walk under a rock built as a pillar with a slab over it, and into a mine whose doorway a single box would have walled off. The pieces are found by following the model's triangles, so a model exported as one joined mesh behaves the same.
- **Tops are floors** — a rock, a fence or a buffalo can be jumped onto and stood on, with half a metre of step allowance telling a kerb from a wall.
- **Crouch** on `L-Ctrl` shortens the whole body, not just the eye. Jumping is forgiving: coyote time, a buffered press, a `CapsLock` run latch and a right-mouse jump.
- The herd's **A\* board is marked from the same pieces**, and only where one comes down within a buffalo's headroom.

**The world itself**
- **Terrain at one metre a pixel**, sized by the level's own heightmap (24-bit fixed point, so gentle slopes are not a staircase), with the mesh **simplified** where the ground is flat and cut into chunks for culling — a kilometre of canyon draws about 5% of the triangles its grid holds.
- **Splat-mapped ground**: four materials blended by height above the water line, projected from all three axes, with the band edges frayed by noise — and a **translucent water surface** with its own shader at the water line.
- **A level can carry its own settings** in a `.cfg` beside its heightmap: the water line and the splat bands describe the level, not the player.
- **Terrain sculpting** in the editor — a falloff brush that raises and lowers, plus flatten, smooth and ramp, all scriptable from the console.

**Playing it**
- **A tool belt** of ten slots, thrown with a wind-up and a power ring, holding a grass bale to lead the herd with and a stick of dynamite; `E` picks back up whatever you are looking at.
- **An idle herd grazes** round the place it came to rest, and a buffalo **turns at the pace an animal turns** rather than snapping round with its velocity.
- **Music**: seven tracks with a fresh one whenever the game changes what it is doing, volume and skip on `F9`/`F10`/`F11`, and a `CustomMusic` folder that plays the player's own MP3s (decoded and streamed, since DesktopGL's `Song` is Ogg-only).

**Driving it from outside**
- **Quake-style console** (`` ` ``) — tab-completion, history, and commands for levels, objects, cameras, the terrain, the herd, the tool belt, the music, screenshots and any setting by name.
- **Command-line arguments and scripting** — open any screen directly, override the display mode for one run, run console scripts and capture the window unattended (see [Command line](#command-line)).
- **A file the game watches** (`console.in`/`console.out`), so one running game can be driven and read for as long as it stays up.
- **Scriptable play**: `player-walk` walks the player for real over the frames to come and `player-walk-sim` runs the same walk to its end on the spot, both reporting what they ran into; `player-jump`, `player-crouch` and `herd-goto` press the rest of it.
- **Debug tooling** — a panel on `F7` (frame rate, update and draw times, real speed, music, terrain), `B` and `O` for what is solid, the pathfinding board, the terrain's mesh and blocks, and depth-map dumps of the picking buffer.

**The screens**
- **Options screen** on the main menu — monitor, resolution, full screen, terrain noise and the music source, persisted to the user's config directory.
- **Help screen as a modal** on `F1`, generated from the bindings themselves; an **exit confirmation** that `Esc` steps back into.
- **RTS-style edge scrolling** with the cursor confined to the window in full screen, and camera fixes — clamped to the map, kept above the terrain, a near plane per camera held inside the body's radius.

## Project structure

What the game is built from. The projects themselves live in the private [source repository](https://github.com/redienss/buffalorun-src).

| Project | What it is |
|---|---|
| `BuffaloRun.Game/BuffaloRun` | The game itself (MonoGame DesktopGL) |
| `BuffaloRun.Engine` | Reusable engine library: math, collision, primitives, render buffers + MSTest tests |
| `BuffaloRun.Terrain` | Perlin-noise heightmap terrain, weighted by per-level heightmaps |
| `BuffaloRun.Game/SkinnedModel(+Pipeline)` | Skinned animation runtime and content processor for the buffalo |
| `BuffaloRun.Audio` | Unported 2011 XNA 3D-audio prototype (kept for history) |

## The 2026 restoration

The original was Windows-only Visual Studio 2010 + XNA Game Studio 4.0. The port replaced the project system with SDK-style projects on MonoGame 3.8.4, converted the Blender FBX 6.1 models to FBX 7.3 (with a hand-fix to the buffalo's vertex-color data that modern importers reject), moved the content build to MGCB, and fixed the handful of path and API differences. The original 2011 code is preserved in the source repository's git history.
