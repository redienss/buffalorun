# Source code

BuffaloRun's source lives in a **private** repository:
**<https://github.com/redienss/buffalorun-src>**

It holds the parts of the project that are not published:

| | |
|---|---|
| `BuffaloRun.Engine` | The game-agnostic engine library — bounding volumes, quadtree and spatial grid, body collision, view culling, shadow matrices, render targets, input |
| `BuffaloRun.Terrain` | Heightmap terrain: meshing, the adaptive LOD quadtree, the splat map, sculpting, and the streamed world of tiles |
| `BuffaloRun.Game` | The game itself (MonoGame DesktopGL) — the layer pipeline, the player, the herd AI and routing, the editor, the console |
| `blender_models` | The `.blend` sources and the scripts that build and export them |
| `console_scripts` | Saved console-command scripts, for repeatable tests and recorded walkthroughs |
| `knowledge` | The project's knowledge base: architecture write-ups, AI and gameplay reasoning, performance measurements, and full reference tables for every setting and console command |

## Why it is private

The engine, the created assets and the design notes are the work; the game
itself is meant to be played rather than lifted. What is public is the part
that is worth showing: what the game is, what it looks like, and where to get
it.

## Getting the game

Built for Linux and Windows on the
[Releases page](https://github.com/redienss/buffalorun/releases). One script
from the source tree ships here too — `scripts/usgs_world.py` builds a
playable world from real USGS elevation data, given a latitude, a longitude
and a size.

## Getting in touch

For access, a commercial licence, or anything else:
<redienss@gmail.com>.
