# Polkuopas OSM extract: Norway core types

This directory is part of the repository `polkuopas-osm-extract`. The Finnish utility overlay method (toilets, parking, drinking water) is described in the repository root `README.md` and is unchanged. This directory covers only the Norway core types. The derived database file sits at the repository root, one level up.

OpenStreetMap objects in Norway that Polkuopas (a Finnish outdoor navigation web app) shows as four outdoor place types, with the rules that
produced them. Published under the Open Database License 1.0 (ODbL) because Polkuopas uses and adapts OpenStreetMap data
(counsel condition O5, ticket KAN-1678).

Contains information from OpenStreetMap, which is made available under the Open Database License (ODbL).
© OpenStreetMap contributors, https://www.openstreetmap.org/copyright. Licence text: [LICENSE](LICENSE) (ODbL 1.0, from
https://opendatacommons.org/licenses/odbl/odbl-10.txt) and https://opendatacommons.org/licenses/odbl/1-0/.

## What is in this repository

| Path | What |
|---|---|
| `../polkuopas-osm-no-core.geojson` (repository root) | The derived database: 9 154 OSM objects as GeoJSON points (see "Columns"). ODbL. |
| `LICENSE` | ODbL 1.0 text (this directory). |
| (`.ts.txt` files are TypeScript sources, renamed so they are read as documentation here) | |
| `rules/osm-no-core-extract.py` | The extractor that builds the file from an OSM PBF. |
| `rules/classify.ts.txt` | Tag whitelist, class to type map, the access rule, the tent-site rule, the name screen, the dedupe radii. |
| `rules/dedupe.ts.txt`, `rules/persist.ts.txt` | The duplicate test against rows from other sources (display and load time) and the load mapping. |

## Source and date

- Source: OpenStreetMap Norway extract `https://download.openstreetmap.fr/extracts/europe/norway.osm.pbf` (1 433 166 159 bytes,
  sha256 `2cd3d317b9ff9d68690d5cdbf02b1893dc279848e3cabc106fe3d27d8be138e5`), replication timestamp in the file header
  `2026-11-19T01:57:18Z`, downloaded 2026-11-19. The newest object in the extract was edited 2026-11-16T15:54:19Z.
- Published file: `polkuopas-osm-no-core.geojson`, sha256 `bb277a8985b119677a3f2e7cfc513585f1ad7944dda874394cfd6e111c1e3476`. This is the file the hidden
  load read and the file the publish tool compares against the registry `source_url` (`sha256sum polkuopas-osm-no-core.geojson` at the repository root). Built from the PBF above
  (OSM.fr, replication timestamp `2026-11-19T01:57:18Z`), extract date 2026-11-19.
- The extract was built from this file and not from Geofabrik `norway-latest.osm.pbf`: Geofabrik was not reachable from the build
  environment on 2026-11-19. The OSM.fr file is a daily country extract of the same OpenStreetMap planet data. The refresh job must use one
  documented source; the source of each published file is recorded here.

## Transform rules

1. Seven OSM class tags only: `tourism=viewpoint`; `leisure=bathing_place`, `leisure=swimming_area`; `leisure=firepit`, `amenity=bbq`;
   `tourism=camp_site`, `tourism=camp_pitch`. Nodes and ways are read. Relations are not read.
2. A way becomes one point: the centre of the bounding box of its nodes (`geom_method = bbox_center`). A node keeps its position
   (`geom_method = native`), rounded to 6 decimals.
3. `fylke_code` is the `ref` of the OSM `boundary=administrative`, `admin_level=4` area that contains the point (two-digit county number),
   or null (42 objects lie outside every county polygon).
4. Tags: only `name`, `access`, `fee`, `tents`, `caravans`, `backcountry`, `capacity` are kept, verbatim. Everything else is dropped, in particular
   `phone`, `contact:*`, `email`, `website`, `operator`, `note`, `description` and `supervised`.
   The script `osm-no-core-o7-check.py` (in `rules/`) confirms none of them is in the file: `python3 -I rules/osm-no-core-o7-check.py ../polkuopas-osm-no-core.geojson`.
5. The loader (`rules/classify.ts.txt`) then keeps 7 252 of the 9 154 objects and drops: objects with `access` of private, no, customers, residents or permit
   (70); tent sites and pitches that are not primitive, i.e. neither `backcountry=yes` nor (`fee=no` and not `caravans=yes`) (1 817); `tents=no` (13); two objects
   outside the expected area (Jan Mayen). A name with an e-mail, a phone-like digit run or `c/o` is withheld (0 in this file).
6. Classes map to Finnish place types: viewpoint to `nakoalapaikka`, bathing place and swimming area to `uimapaikka`, firepit to `tulipaikka`,
   bbq to `grillipaikka`, camp site and pitch (kept ones) to `telttailupaikka`.
7. Duplicates with other sources are never stored as a link. An OSM row within 50 m (100 m for tent sites) of an existing row of the
   same type from another source is left out of the Polkuopas load; only counts are kept.

The Polkuopas database changes the OpenStreetMap data in the ways listed above: tags were whitelisted, ways were reduced to a centre point, rows were
filtered and reclassified.

## Columns of the GeoJSON

`geometry`: Point `[lon, lat]`, WGS 84. `properties`: `osm_type` (node or way), `osm_id`, `osm_version`, `osm_timestamp`, `class_tag`,
`geom_method`, `fylke_code`, `tags` (the whitelisted tags). No column from any other source.

## Counts (9 154 objects)

tourism=viewpoint 3 935 (3 874 nodes, 61 ways); leisure=bathing_place 177; leisure=swimming_area 222; leisure=firepit 2 039; amenity=bbq 775;
tourism=camp_site 1 445; tourism=camp_pitch 561. After the rules above, 7 252 rows: nakoalapaikka 3 931, tulipaikka 2 008, grillipaikka 769,
uimapaikka 395, telttailupaikka 149.

## How to rebuild

```
pip install osmium shapely
python3 -I rules/osm-no-core-extract.py norway.osm.pbf ../polkuopas-osm-no-core.geojson   # about 10 minutes, 6 GB RAM
```

The commands above run from this directory. A refresh replaces `../polkuopas-osm-no-core.geojson` and updates the source, date and sha256 above in the same commit.
