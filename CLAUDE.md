# Titik Temu — project map (read this first, then open only the file you need)

BAAR 3101 Architectural Design 5, Section 8, KAED IIUM — Megat Muhammad Ihsan.
"Titik Temu — Simpul Rasa Semenanjung": Esplanade Local Commercial Hub, Site C, Jalan Tok Muda Awang Ngah, Temerloh (Lot 10150, 5,370 m²). Futuristic typology.

## Units and coordinates (shared by every folder)
- Site coordinates in metres, x = east, y = north, origin = SW site corner on the road. Site polygon: `model/geom.py` `SITE`.
- Big ring "Gelung Rasa" centre `B`, small ring "Gelung Kecil" centre `S`, both on the QIBLA axis (292.3°), 26.22 m apart. Radii and levels are constants in `model/geom.py`.
- Levels: site ±0.000, plinth +0.900, L1 / roof terrace +5.400, small-ring roof +9.900 (parapet +10.5), ribbon roof +11.200 → +12.900, crown +13.500.

## Folders
| Folder | What it makes | Entry points |
|---|---|---|
| `model/` | Geometry of the design, A1 drawings (PDF/DXF), SketchUp/DAE exports, interior model | `geom.py` (all key geometry), `site_el.py` (road, trees, ribbons, plaza), `skp_build.py` (3D massing → DAE), `interior_build.py`, `draw.py` / `draw2.py` (A1 sheets) |
| `render3d/` | three.js renders of the DAE files (hero, exploded axo, masks) | `render.html` (URL params: dae, eye, tgt, fov/ortho, mode, hide…), `shot.js` (Playwright screenshot) |
| `boards/` | Crit 1 A3 presentation boards | Current set = **5 landscape sheets** `s1.py`–`s5.py` (1587×1123 px), rendered by `render_land.py` + `shotl.js`; shared helpers `content.py`; hero/axo collage scripts in `py/`; true-scale crops from the A1 PDF via `crops3.py` (`img/truescale.json` holds sizes). `p1.py`–`p4.py` = older 4-sheet portrait set; `board1.py`/`board2.py` = first 2-sheet version |
| `mockup/` | 1:500 mock-up model kit, 20 A4 pages (PDF) | `run.py` → `kit.py` (site layer pages), `kit2.py` (building pieces), `kit3.py` (cover, overview, assembly); `terrain.py` (9 contour layers), `building.py` (pieces B1–B10, crown, ribbons) |

## Key decisions (don't undo without asking)
- Boards: all text uppercase; drawings at TRUE scale on A3 (plans/sections/elevations 1:200, site plan 1:500); A3 landscape, 5 sheets.
- Mock-up: 1:500, 2 mm greyboard = 1 m contour layer, 5 mm foam for the building. Contours were traced from the user's example-model photo (`mockup/H.npy` = photo→site homography) — approximate.
- Room areas must be read from the A1 plan text, not guessed (gallery 54 m², first aid 18 m²).

## Skills in this repo
- `.claude/skills/diagram-design/` — Cathryn Lavery's diagram-design skill (MIT, copied from github.com/cathrynlavery/diagram-design, v2.6). Use it for concept, site-analysis, circulation, programme and process diagrams: one self-contained HTML + SVG file per diagram.

## Gotchas
- Scripts use absolute paths under `/home/claude/...` (the original cloud workspace). Images, fonts, renders, PDFs and DAE files are NOT in this repo (too big) — re-generate or re-upload them.
- `boards/build_dc*.py` publish to a claude.ai Design canvas; images there must be `/_blob/<id>` URLs.
