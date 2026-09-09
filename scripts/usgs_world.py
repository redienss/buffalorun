#!/usr/bin/env python3
"""Build a BuffaloRun streamed world from real elevation data, around a latitude and longitude.

    scripts/usgs_world.py <lat> <lon> <name> <tilesX> <tilesY> [options]
    scripts/usgs_world.py 36.044096 -111.8262494 grand_canyon 8 8 --offset -2600,3400

Writes Content/Levels/<name>/ - a directory per tile holding its heightmap_1.png, plus the
overview, an empty object list and a world.cfg - which the game then loads like any other level.

WHY A SCRIPT AND NOT A CONSOLE COMMAND
    world-new and world-import are console commands because they only transform data the install
    already has. This needs an HTTP client, Web Mercator projection maths and a live tile service,
    and none of that belongs in a game process: a level editor that fails because a CDN is down is a
    bad trade. The game's side of the job is unchanged - it loads a world folder.

THE DATA
    AWS Open Data's "terrarium" elevation tiles (Tilezen/Mapzen heritage), which are a blend of
    national datasets: largely USGS 3DEP over the United States, SRTM and GMTED elsewhere. Elevation
    is packed per pixel as (R * 256 + G + B / 256) - 32768 metres. Public domain to permissive
    depending on the source; see https://github.com/tilezen/joerd for the attribution each carries.

HEIGHTS
    A BuffaloRun heightmap pixel holds 0..255 m and no more, and real ground is taller - the Grand
    Canyon is 1500 m river to rim. So the window's relief is stored normalised onto 0..255 and the
    world.cfg carries TerrainHeightScale, which the game applies as it reads the heights (see
    Terrain.ScaleHeights). Everything in the cfg below it - the water line, the splat bands - is
    therefore in real metres.

NEEDS numpy and pillow, which are not project dependencies and are not installed system-wide - a
modern distribution refuses that anyway (PEP 668), and breaking the system Python to build a level
would be a poor trade. Instead the script keeps its own virtualenv in .venv at the repo root and
re-runs itself inside it, making it on first use. So it is simply run:

    scripts/usgs_world.py 36.044096 -111.8262494 grand_canyon 8 8
"""
import argparse
import concurrent.futures
import math
import os
import subprocess
import sys
import time
import urllib.request

VENV = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, ".venv"))


def venv_python(venv):
    """Where the interpreter lives inside a virtualenv, on this platform."""
    return (os.path.join(venv, "Scripts", "python.exe") if os.name == "nt"
            else os.path.join(venv, "bin", "python"))


def bootstrap():
    """
    Hand over to the project's own virtualenv, building it the first time. Guarded by an environment
    variable so that a venv which somehow still lacks the packages fails with a message rather than
    re-running itself for ever.
    """
    if os.environ.get("BUFFALORUN_DEM_ENV"):
        sys.exit(f"numpy and pillow are still missing from {VENV} - delete it and run again")

    python = venv_python(VENV)
    if not os.path.exists(python):
        print(f"first run: building a virtualenv for numpy and pillow in {VENV}", flush=True)
        try:
            subprocess.check_call([sys.executable, "-m", "venv", VENV])
            subprocess.check_call([python, "-m", "pip", "install", "--quiet", "numpy", "pillow"])
        except (subprocess.CalledProcessError, OSError) as e:
            sys.exit(f"could not build the virtualenv ({e}).\n"
                     f"On Debian and Ubuntu this usually wants: sudo apt install python3-venv")

    os.environ["BUFFALORUN_DEM_ENV"] = "1"
    os.execv(python, [python, os.path.abspath(__file__)] + sys.argv[1:])


try:
    import numpy as np
    from PIL import Image
except ImportError:
    bootstrap()

TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
HEIGHTMAP_MAX = 255.0          # GrayBitmap.MaxHeight
OVERVIEW_MAX = 2048            # Settings.WorldOverviewMax
FINEST_SOURCE_M = 4.0          # stop zooming in once the source is this fine; below it is invented
ELEV_MIN_PLAUSIBLE = -500.0    # Dead Sea shore with margin; below this a terrarium pixel is a void
ELEV_MAX_PLAUSIBLE = 9000.0    # above Everest; above this a terrarium pixel is a void

PROGRESS = False              # --progress: print machine-readable "PROGRESS <percent>" lines


def emit_progress(fraction):
    """With --progress, print a lone 'PROGRESS <percent>' line for the in-game World Creator's bar
    to parse (T100). Silent otherwise, so a hand run's output is unchanged. The fractions below add
    up to a rough but monotonic 0 -> 1: most of a run is the tile fetch, so it gets most of the bar.
    """
    if PROGRESS:
        print(f"PROGRESS {max(0, min(100, int(fraction * 100)))}", flush=True)


# ---- Web Mercator ----------------------------------------------------------------------------

def lonlat_to_pixel(lon, lat, zoom):
    n = 256 * 2 ** zoom
    s = math.sin(math.radians(lat))
    return ((lon + 180.0) / 360.0 * n,
            (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n)


def metres_per_pixel(lat, zoom):
    """Ground metres one pixel covers. Web Mercator is conformal, so a square of pixels is a square
    on the ground locally - which is what lets a window be cropped and scaled without reprojecting."""
    return 156543.03392804097 * math.cos(math.radians(lat)) / (2 ** zoom)


def choose_zoom(lat, side_m):
    """The coarsest zoom whose pixels are finer than FINEST_SOURCE_M. Going finer than the source
    data only interpolates it, and costs four times the requests for every extra level."""
    for zoom in range(8, 16):
        if metres_per_pixel(lat, zoom) <= FINEST_SOURCE_M:
            return zoom
    return 15


# ---- Fetching --------------------------------------------------------------------------------

def fetch_tile(zoom, tx, ty, cache):
    """One tile, cached on disk so a re-run costs nothing and a failed run resumes where it stopped."""
    path = os.path.join(cache, f"{zoom}_{tx}_{ty}.png")
    for attempt in range(6):
        if os.path.exists(path) and os.path.getsize(path) > 0:
            break
        try:
            request = urllib.request.Request(
                TILE_URL.format(z=zoom, x=tx, y=ty),
                headers={"User-Agent": "buffalorun-usgs-world/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
            with open(path, "wb") as handle:
                handle.write(data)
        except Exception:
            if attempt == 5:
                raise
            time.sleep(1.5 * (attempt + 1))

    return tx, ty, np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)


def read_window(lat, lon, side_m, zoom, offset_e, offset_n, cache):
    """The elevation of a square window of ground, in metres, as a [row, col] array with row 0 north."""
    mpp = metres_per_pixel(lat, zoom)
    side_px = side_m / mpp

    cx, cy = lonlat_to_pixel(lon, lat, zoom)
    cx += offset_e / mpp
    cy -= offset_n / mpp                       # pixel Y grows southward

    x0, y0 = cx - side_px / 2.0, cy - side_px / 2.0
    tx0, ty0 = int(math.floor(x0 / 256)), int(math.floor(y0 / 256))
    tx1 = int(math.floor((x0 + side_px - 1e-6) / 256))
    ty1 = int(math.floor((y0 + side_px - 1e-6) / 256))
    wanted = [(tx, ty) for ty in range(ty0, ty1 + 1) for tx in range(tx0, tx1 + 1)]

    print(f"zoom {zoom}: {mpp:.2f} m per source pixel, {len(wanted)} tiles "
          f"({tx1 - tx0 + 1} x {ty1 - ty0 + 1})", flush=True)

    os.makedirs(cache, exist_ok=True)
    mosaic = np.zeros(((ty1 - ty0 + 1) * 256, (tx1 - tx0 + 1) * 256), dtype=np.float64)
    done = 0
    emit_progress(0.05)
    # Three at a time: the service resets connections under heavier parallelism.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for tx, ty, rgb in pool.map(lambda t: fetch_tile(zoom, t[0], t[1], cache), wanted):
            metres = rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0
            mosaic[(ty - ty0) * 256:(ty - ty0 + 1) * 256,
                   (tx - tx0) * 256:(tx - tx0 + 1) * 256] = metres
            done += 1
            emit_progress(0.05 + 0.60 * done / len(wanted))
            if done % 25 == 0 or done == len(wanted):
                print(f"  {done}/{len(wanted)} tiles", flush=True)

    n = int(round(side_px))
    oy, ox = int(round(y0 - ty0 * 256)), int(round(x0 - tx0 * 256))
    window = mosaic[oy:oy + n, ox:ox + n]

    # Where the requested point ended up, in world metres from the window's north-west corner.
    px, py = lonlat_to_pixel(lon, lat, zoom)
    return window, ((px - x0) * mpp, (py - y0) * mpp)


def grow_into_nan(filled, passes, fallback):
    """Fill the NaN cells of an array by iterated four-neighbour averaging, in place.

    Each pass sets a still-empty cell to the mean of whichever of its four neighbours already hold
    a value, so valid ground grows into a gap a ring at a time - a thin seam closes in a pass or
    two, and a lone one-cell hole in one. The slices never wrap, so a bad edge column fills inward
    rather than from the far side of the window. Anything still open after `passes` - the middle of
    a large hole, with no real data to reach for - is set to `fallback`.
    """
    for _ in range(passes):
        holes = np.isnan(filled)
        if not holes.any():
            break
        total = np.zeros_like(filled)
        count = np.zeros_like(filled)
        have = (~holes).astype(np.float64)
        val = np.where(holes, 0.0, filled)
        total[1:, :] += val[:-1, :]
        count[1:, :] += have[:-1, :]
        total[:-1, :] += val[1:, :]
        count[:-1, :] += have[1:, :]
        total[:, 1:] += val[:, :-1]
        count[:, 1:] += have[:, :-1]
        total[:, :-1] += val[:, 1:]
        count[:, :-1] += have[:, 1:]
        fillable = holes & (count > 0)
        filled[fillable] = total[fillable] / count[fillable]
    filled[np.isnan(filled)] = fallback
    return filled


def repair_voids(window):
    """Fill gaps in the source elevation before anything measures the window.

    Terrarium tiles carry voids - a seam between two national DEMs, a missing or error tile, a
    black or white edge column - and a void pixel decodes to a wild elevation: -32768 m for RGB
    (0, 0, 0), ~+32767 m for (255, 255, 255). Left in, one poisons the whole world: window.min() /
    max() take it, so relief and the derived TerrainHeightScale balloon to tens of thousands of
    metres, the real landscape is crushed into a handful of the 0..255 heightmap levels (a near
    flat minimap), and the void itself pins to 0 or 255 - a full-height wall with a matching slot
    once the bicubic resize smears the hairline gap into a band. The splat bands and water line,
    also derived from relief, come out meaningless too.

    Every pixel outside a plausible Earth-elevation band is flagged and filled from the nearest
    valid ground by iterated four-neighbour averaging (no scipy on the target machines); whatever
    is still open after the pass cap - the middle of a large hole, which has no real data to reach
    for anyway - is set to the median real elevation. Returns (repaired_window, pixels_repaired).
    """
    bad = ~np.isfinite(window) | (window < ELEV_MIN_PLAUSIBLE) | (window > ELEV_MAX_PLAUSIBLE)
    repaired = int(bad.sum())
    if repaired == 0:
        return window, 0
    if repaired > window.size // 2:
        sys.exit(f"{repaired} of {window.size} source pixels are outside a plausible elevation "
                 f"range - the download looks broken, not gappy; retry, or pass an explicit --zoom")

    good_median = float(np.median(window[~bad]))
    filled = grow_into_nan(np.where(bad, np.nan, window).astype(np.float64), 96, good_median)
    return filled, repaired


def _wall_distance(pad, window, reach, axis, sign, threshold):
    """For each cell, the fewest cells (1..reach) you step in one direction before the ground has
    climbed `threshold` above the cell - or reach + 1 if it never does within reach. `axis` 0 is
    north/south, 1 is east/west; `sign` -1 looks toward row/col 0, +1 the other way."""
    h, w = window.shape
    out = np.full((h, w), reach + 1, dtype=np.int16)
    for d in range(1, reach + 1):
        off = reach + sign * d
        if axis == 0:
            neighbour = pad[off:off + h, reach:reach + w]
        else:
            neighbour = pad[reach:reach + h, off:off + w]
        found = (out > reach) & (neighbour - window >= threshold)
        out[found] = d
    return out


def repair_pits(window, drop_m=100.0, despike_m=0.0, max_width=6, reach=8, max_passes=2):
    """Fill the seam artefacts T104's void mask lets through - cells holding a *plausible* elevation
    but sitting hundreds of metres below (or, with --despike, above) the real ground around them,
    left on the boundary between two national DEMs of different resolution and vintage.

    T105 found these as *isolated* one-cell pits and cleared them with a 3x3 median plus a "six of
    eight neighbours agree" test. T109 is the same error drawn out into a *contiguous trench* a
    cell or two wide running along the seam: a cell mid-trench has neither six good neighbours nor
    an honest 3x3 median, so that test walked straight past it and the trench floor still set
    window.min() and inflated relief, TerrainHeightScale, WaterLevel and the splat bands for the
    whole world.

    A cell is flagged when it sits in a *narrow ditch*: stepping outward until the ground has
    climbed the full `drop_m` above it, the walls on two opposite sides - north and south, or east
    and west - are together no more than `max_width` cells apart. That catches a pit (a wall one
    cell off on every side) and a trench of any orientation up to `max_width` wide, while by
    construction leaving alone the things that must survive: a canyon rim or an escarpment climbs
    on one side only; a broad basin or valley has its far wall more than `max_width` cells away;
    and asking for the whole of `drop_m` on *both* sides within that span keeps ordinary steep
    ground - a mountainside, a V-drainage - well clear, since real ground that falls a hundred
    metres into a gap only a few cells wide and climbs it straight back is not ground the terrarium
    source resolves. A trench wider than `max_width`, or one pinned hard against the window edge, is
    left to the low/high guard in main(), which keeps the height scale honest even if a shallow
    notch survives in the geometry (it clips to zero there). Flagged cells are inpainted by the
    four-neighbour averaging repair_voids uses. `--despike` turns on the mirror image for upward
    spikes, off by default because a real spire or mesa lip can be a genuine one- or two-cell
    feature. Returns (repaired_window, pits_filled, spikes_filled).
    """
    wall = drop_m
    crest = despike_m
    pits_filled = spikes_filled = 0

    for _ in range(max_passes):
        pad = np.pad(window, reach, mode="reflect")
        dn = _wall_distance(pad, window, reach, 0, -1, wall)
        ds = _wall_distance(pad, window, reach, 0, +1, wall)
        dw = _wall_distance(pad, window, reach, 1, -1, wall)
        de = _wall_distance(pad, window, reach, 1, +1, wall)
        pit = (((dn <= reach) & (ds <= reach) & (dn + ds - 1 <= max_width))
               | ((dw <= reach) & (de <= reach) & (dw + de - 1 <= max_width)))

        if despike_m > 0:
            npad, nwin = -pad, -window
            un = _wall_distance(npad, nwin, reach, 0, -1, crest)
            us = _wall_distance(npad, nwin, reach, 0, +1, crest)
            uw = _wall_distance(npad, nwin, reach, 1, -1, crest)
            ue = _wall_distance(npad, nwin, reach, 1, +1, crest)
            spike = (((un <= reach) & (us <= reach) & (un + us - 1 <= max_width))
                     | ((uw <= reach) & (ue <= reach) & (uw + ue - 1 <= max_width)))
        else:
            spike = np.zeros(window.shape, dtype=bool)

        flagged = pit | spike
        if not flagged.any():
            break
        pits_filled += int(pit.sum())
        spikes_filled += int(spike.sum())
        fallback = float(np.median(window[~flagged]))
        window = grow_into_nan(np.where(flagged, np.nan, window).astype(np.float64), 12, fallback)

    return window, pits_filled, spikes_filled


# ---- Writing the world -----------------------------------------------------------------------

def encode(metres):
    """metres -> (h, w, 3) uint8, the way GrayBitmap writes a heightmap: value = metres * 0x010101."""
    value = np.clip(np.round(metres * 0x010101), 0, 0xFFFFFF).astype(np.uint32)
    rgb = np.empty(value.shape + (3,), dtype=np.uint8)
    rgb[..., 0] = (value >> 16) & 0xFF
    rgb[..., 1] = (value >> 8) & 0xFF
    rgb[..., 2] = value & 0xFF
    return rgb


def write_world(out_dir, normalised, tiles_x, tiles_y, tile_size):
    os.makedirs(out_dir, exist_ok=True)

    for ty in range(tiles_y):
        for tx in range(tiles_x):
            block = normalised[ty * tile_size:(ty + 1) * tile_size,
                               tx * tile_size:(tx + 1) * tile_size]
            # Each tile is a directory of its own, holding its authored heightmap as heightmap_1.png
            # (see WorldFiles). Everything else a tile directory ends up with - the coarse
            # heightmap_2/4/8.png, edges.png, mips.bin, errors_N.bin - is derived from this one and
            # written by the game the first time it reads the tile, so nothing here makes them.
            tile_dir = os.path.join(out_dir, f"{tx:04d}_{ty:04d}")
            os.makedirs(tile_dir, exist_ok=True)
            # Rows are world Y and columns world X, which is how the game reads a heightmap PNG.
            Image.fromarray(encode(block), mode="RGB").save(
                os.path.join(tile_dir, "heightmap_1.png"))
        print(f"  tile row {ty + 1}/{tiles_y}", flush=True)
        emit_progress(0.70 + 0.25 * (ty + 1) / tiles_y)

    # The overview, by the rule WorldBuilder.WriteOverview uses: a power-of-two step so it divides
    # the tile size exactly, each cell the highest of its block so ground never reads low.
    width, height = normalised.shape[1], normalised.shape[0]
    step = 1
    while max(width, height) // step > OVERVIEW_MAX:
        step *= 2
    coarse = normalised[:height // step * step, :width // step * step].reshape(
        height // step, step, width // step, step).max(axis=(1, 3))
    Image.fromarray(encode(coarse), mode="RGB").save(os.path.join(out_dir, "overview.png"))

    open(os.path.join(out_dir, "objects.txt"), "w").close()
    return coarse.shape[1], step


def default_out_dir(here, name):
    """Where a world goes when --out is not given: the source tree's Levels folder if this script
    is sitting in one, and otherwise Content/Levels beside the game it was shipped with. The script
    travels with the release as well as the repository, and a player has no BuffaloRunContent."""
    source_levels = os.path.join(here, os.pardir, "BuffaloRun.Game", "BuffaloRun",
                                 "BuffaloRunContent", "Levels")
    if os.path.isdir(source_levels):
        return os.path.abspath(os.path.join(source_levels, name))
    return os.path.abspath(os.path.join(here, os.pardir, "Content", "Levels", name))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("lat", type=float)
    parser.add_argument("lon", type=float)
    parser.add_argument("name")
    parser.add_argument("tiles_x", type=int)
    parser.add_argument("tiles_y", type=int)
    parser.add_argument("--tile-size", type=int, default=1024, help="tile edge in metres (default 1024)")
    parser.add_argument("--zoom", type=int, default=0, help="source zoom; 0 picks it from the size")
    parser.add_argument("--pit-depth", type=float, default=100.0,
                        help="fill any cell sitting more than this many metres below its local "
                             "level and ditched in on two opposite sides - a pit or a narrow "
                             "trench left on a source-DEM seam that would otherwise drag down the "
                             "whole world's height scale (default 100)")
    parser.add_argument("--despike", type=float, default=0.0,
                        help="also fill a cell this many metres ABOVE the ground on two opposite "
                             "sides - an upward seam spike (0 = off, the default, since a real "
                             "spire can be a genuine one-cell feature); set it for a location "
                             "whose seam artefacts point up")
    parser.add_argument("--offset", default="0,0",
                        help="metres east,north from the point to the window's centre, so a "
                             "landmark can sit off to one side (default centred)")
    parser.add_argument("--out", default=None,
                        help="where to write the world folder (default: the Levels folder of the "
                             "source tree or game install this script sits beside)")
    parser.add_argument("--cache", default=None, help="where to keep downloaded source tiles")
    parser.add_argument("--progress", action="store_true",
                        help="print machine-readable 'PROGRESS <percent>' lines on stdout, for the "
                             "in-game World Creator's progress bar")
    args = parser.parse_args()

    global PROGRESS
    PROGRESS = args.progress

    if args.tiles_x < 1 or args.tiles_y < 1 or args.tile_size < 2:
        sys.exit("a world must be at least one tile, and a tile at least 2 m across")
    if args.tiles_x != args.tiles_y:
        sys.exit("only square worlds for now: the window is cropped square before it is resampled")

    side_m = args.tile_size * args.tiles_x
    zoom = args.zoom or choose_zoom(args.lat, side_m)
    offset_e, offset_n = (float(v) for v in args.offset.split(","))

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(args.out) if args.out else default_out_dir(here, args.name)
    cache = os.path.abspath(args.cache or os.path.join(here, os.pardir, ".dem-cache"))

    if os.path.exists(os.path.join(out_dir, "world.cfg")):
        sys.exit(f"a world already exists at {out_dir} - remove it first")

    print(f"{args.name}: {side_m} x {side_m} m around {args.lat}, {args.lon}")
    emit_progress(0.0)
    window, (point_x, point_y) = read_window(args.lat, args.lon, side_m, zoom,
                                             offset_e, offset_n, cache)
    emit_progress(0.66)

    raw_low, raw_high = float(window.min()), float(window.max())
    window, repaired = repair_voids(window)
    if repaired:
        print(f"repaired {repaired} void pixel(s) "
              f"({100.0 * repaired / window.size:.3f}% of the window); raw source range "
              f"{raw_low:.0f} - {raw_high:.0f} m had values outside "
              f"[{ELEV_MIN_PLAUSIBLE:.0f}, {ELEV_MAX_PLAUSIBLE:.0f}] m", flush=True)

    window, pits, spikes = repair_pits(window, args.pit_depth, args.despike)
    if pits or spikes:
        note = f"filled {pits} seam pit / trench cell(s) > {args.pit_depth:.0f} m below the local level"
        if args.despike > 0:
            note += f" and {spikes} spike cell(s) > {args.despike:.0f} m above it"
        print(note + " (source-DEM seam artefacts)", flush=True)
    emit_progress(0.67)

    # low/high set every derived cfg value, so a stubborn artefact repair_pits could not reach - a
    # trench several cells thick pinned hard against the window's own edge - must not be allowed to
    # define them. Take the range from a low/high percentile of the window's *interior* (a border
    # ring wider than any trench repair_pits can see is dropped, so an edge-hugging artefact can't
    # reach it), and only override the raw min/max when they sit an implausible distance past that
    # - a clean window keeps its exact extremes (T109).
    ring = 8
    core = window[ring:-ring, ring:-ring] if min(window.shape) > 3 * ring else window
    w_min, w_max = float(window.min()), float(window.max())
    filt_min, filt_max = float(np.percentile(core, 0.1)), float(np.percentile(core, 99.9))
    low = w_min if w_min >= filt_min - args.pit_depth else filt_min
    high = w_max if w_max <= filt_max + args.pit_depth else filt_max
    if low != w_min or high != w_max:
        print(f"robust height range: raw {w_min:.0f} - {w_max:.0f} m carried a residual seam "
              f"artefact; using {low:.0f} - {high:.0f} m from the window interior", flush=True)
    relief = max(high - low, 1e-3)
    height_scale = relief / HEIGHTMAP_MAX

    print(f"elevation {low:.0f} - {high:.0f} m, relief {relief:.0f} m "
          f"-> TerrainHeightScale {height_scale:.4f}")

    # One cell per metre, bicubic. The source is coarser than a metre, so this interpolates real
    # data rather than inventing it: the shape is the survey's, only smoother between its samples.
    field = np.asarray(Image.fromarray(window.astype(np.float32), mode="F")
                       .resize((side_m, side_m), Image.BICUBIC), dtype=np.float32)
    normalised = np.clip((field - low) / height_scale, 0.0, HEIGHTMAP_MAX)
    emit_progress(0.70)

    # read_window's row 0 is north (DEM rows run south with the source pixel grid), but a
    # heightmap's row 0 is world Y 0, which the minimap draws at its bottom - so written straight
    # through, north landed at world Y's high end and the minimap showed it at the top and south
    # at the bottom, both backwards. Flipping here once puts north at the high-Y end, matching
    # how the game already draws +Y up the panel.
    normalised = normalised[::-1, :]
    point_y = side_m - point_y

    overview_px, overview_step = write_world(out_dir, normalised, args.tiles_x, args.tiles_y,
                                             args.tile_size)
    emit_progress(0.97)

    # A load radius of one tile reaches to the player's own edge, which is not far enough to see
    # across deep ground - the far wall of a canyon is simply beyond the far plane. Relief buys a
    # wider one. The unload radius trails it by half a tile - the gap a player pacing back and
    # forth at the load line never crosses in one step, so nothing reloads there. Kept to whole
    # tiles rather than the 1.5/2.5 this once was: on a 20x20 world a ring wide enough to see a
    # canyon by, held in RAM at once, crashed a machine already tight on memory even with the
    # streaming builds themselves capped - see Settings.TerrainLoadRadius.
    load_radius = args.tile_size * (2.0 if relief > 400 else 1.0)
    unload_radius = load_radius + args.tile_size * 0.5

    # A river or lake bed sits close to the window's own floor, not at a fixed fraction of its
    # relief - a canyon whose walls run to 1500 m does not have a lake a thirtieth of that deep.
    # Measured against the Grand Canyon window (785-2286 m, the Colorado at the floor):
    # relief * 0.02 capped at 30 gave a water line of 30 m, which reads as a wall-to-wall lake
    # rather than a river, because most of the canyon floor's own relief is well under 30 m of
    # the window's lowest point. relief * 0.008 gives 12 m for that window - confirmed by eye to
    # read as a river, the value this was hand-tuned to before the heuristic existed.
    water = round(min(relief * 0.008, 20.0), 1)

    with open(os.path.join(out_dir, "world.cfg"), "w") as handle:
        handle.write(f"""\
# {args.name}: real ground around {args.lat}, {args.lon}, an {side_m} x {side_m} m window at one
# cell per metre. Built by scripts/usgs_world.py from AWS Open Data terrarium elevation tiles
# (USGS 3DEP over the United States, SRTM and others elsewhere) at zoom {zoom},
# {metres_per_pixel(args.lat, zoom):.2f} m per source pixel.
#
# Real elevation {low:.0f} - {high:.0f} m ({relief:.0f} m of relief) is stored normalised onto the
# 0 - 255 m a heightmap pixel can hold; TerrainHeightScale reads it back at its true size, so
# {low:.0f} m of real elevation is 0 in game and everything below is in real metres.
#
# The point asked for is at world ({point_x:.0f}, {point_y:.0f}).

TileSize = {args.tile_size}
TilesX = {args.tiles_x}
TilesY = {args.tiles_y}

TerrainLatitude = {args.lat}
TerrainLongitude = {args.lon}

TerrainHeightScale = {height_scale:.4f}
TerrainLoadRadius = {load_radius:.0f}
TerrainUnloadRadius = {unload_radius:.0f}

WaterLevel = {water}
SplatMappingEnabled = true
SplatGrassTop = {round(relief * 0.04, 1)}
SplatGravelTop = {round(relief * 0.15, 1)}
SplatBlend = {round(relief * 0.017, 1)}
SplatNoiseAmplitude = {round(relief * 0.008, 1)}
SplatNoiseMeters = 30.0
""")

    emit_progress(1.0)
    print(f"overview {overview_px} px at {overview_step} m per cell")
    print(f"wrote {out_dir}")
    print(f"the point asked for is at world ({point_x:.0f}, {point_y:.0f}); "
          f"load it with  level-load {args.name}")


if __name__ == "__main__":
    main()
