# Polkuopas OSM extract: Norway core types, huts and shelters

This directory is part of the repository `polkuopas-osm-extract`. The Finnish utility overlay method (toilets, parking, drinking water) is described in the repository root `README.md` and is unchanged. This directory covers the Norway core types and, in the section at the end, the Norway huts and shelters. The derived database files sit at the repository root, one level up.

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

## Huts and shelters (KAN-1684)

A second derived database, for OSM huts and shelters in Norway, with its own rules. Same licence (ODbL 1.0), same credit, same kind of change to the data.

| Path | What |
|---|---|
| `../polkuopas-osm-no-huts.geojson` (repository root) | The derived database: 6 492 OSM objects as GeoJSON points. ODbL. |
| `rules/osm-no-huts-extract.py` | The extractor that builds the file from an OSM PBF. It applies the weather-shelter rule, the Svalbard / Jan Mayen rule and the name screen before writing. |
| `rules/osm-no-huts-classify.ts.txt` | Tag whitelist, class to type map, the access and commercial-building rules, the shelter types, the Svalbard / Jan Mayen test, the dedupe radius. |
| `rules/osm-no-huts-transform.ts.txt` | How the loader turns the file into rows (name screen, counted reasons). |
| `rules/osm-no-huts-dedupe.ts.txt` | The duplicate test against official huts and shelters (documentation; the shown set applies it at read time with a 100 m radius, and stores no pairing). |
| `rules/osm-no-huts-persist.ts.txt` | The load mapping to the Polkuopas tables. |
| `rules/osm-no-huts-o7-check.py` | Confirms the file holds no contact data: `python3 -I rules/osm-no-huts-o7-check.py ../polkuopas-osm-no-huts.geojson`. |

### Source and date (huts and shelters)

- Source: the same OpenStreetMap Norway extract as above, `https://download.openstreetmap.fr/extracts/europe/norway.osm.pbf` (sha256
  `2cd3d317b9ff9d68690d5cdbf02b1893dc279848e3cabc106fe3d27d8be138e5`), replication timestamp `2026-11-19T01:57:18Z`, downloaded 2026-11-19; extract date 2026-11-19.
  Geofabrik was not reachable from the build environment. A refresh must use one documented source; the source of each published file is recorded here.
- Published file: `polkuopas-osm-no-huts.geojson`, sha256 `a06a183baaae166a83d33bfea0dbbd07f8d183b5d8b52d3fcd49fc822f3f546a`.

### Transform rules (huts and shelters)

1. Three OSM class tags only: `tourism=alpine_hut`, `tourism=wilderness_hut`, `amenity=shelter`. Nodes and ways are read; relations are not. A way becomes one point, the centre of the
   bounding box of its nodes (`geom_method = bbox_center`); a node keeps its position (`native`), rounded to 6 decimals.
2. `fylke_code` is the `ref` of the OSM `boundary=administrative`, `admin_level=4` area that contains the point, or null (78 objects).
3. Tags kept, verbatim: `name`, `access`, `shelter_type`, `building`. Everything else is dropped, in particular `phone`, `contact:*`, `email`, `website`, `operator`, `note`, `description`,
   `fee`, `capacity`. `reservation` is not kept. `access`, `shelter_type` and `building` are classification inputs and are never shown.
4. Before the tags are dropped: an `amenity=shelter` with `shelter_type=weather_shelter` that is also tagged `public_transport=*`, `highway=bus_stop` or `building=*` is left out (44 objects);
   a point on Svalbard (fylke 21), Bjornoya or Jan Mayen (fylke 22) is left out (55 objects): fylke code, 74 N or higher, above 70 N and west of longitude 0, and the Svalbard and Jan Mayen boxes
   of `osm-no-core`; a name with an e-mail, a URL, a phone-like digit run or `c/o` is left out of the object (1 object keeps its point without a name).
5. The loader (`rules/osm-no-huts-classify.ts.txt`) keeps 2 946 of the 6 492 objects (941 huts, 2 005 shelters of which 105 weather shelters) and drops: `access` of private, no, customers,
   residents or permit (46); `building` of hotel, kiosk, commercial, retail or apartments on a hut (9); shelters with no `shelter_type` (1 218), with `public_transport` (1 397) or any other
   type than lean_to, basic_hut, lavvu, weather_shelter (876).
6. Classes map to Finnish place types: huts to `turisthytte`, kept shelters to `laavu`. Never `autiotupa` or `varaustupa`.
7. Duplicates with other sources are never stored as a link. An OSM row within 100 m of a visible official hut or shelter point (any label) is hidden when the data is shown; only the read query
   uses the official coordinates, and nothing about a pair is stored.

The Polkuopas database changes the OpenStreetMap data in the ways listed above: tags were whitelisted, ways were reduced to a centre point, rows were filtered and reclassified.

### Counts (6 492 objects)

tourism=alpine_hut 216; tourism=wilderness_hut 753; amenity=shelter 5 523. After the rules above, 2 946 rows. The research memo (6 591 objects, 2 890 kept before the weather shelters) was
measured on the same PBF; it differs from this file by the two rules applied in the extractor (99 objects) and the weather shelters that are now in.

### How to rebuild

```
pip install osmium shapely
python3 -I rules/osm-no-huts-extract.py norway.osm.pbf ../polkuopas-osm-no-huts.geojson   # about 8 minutes
```

A refresh replaces `polkuopas-osm-no-huts.geojson` and updates the source, date and sha256 above in the same commit.
