# Polkuopas OSM POI extract (ODbL Section 4.6(b) method)

This repository publishes the method Polkuopas (https://polkuopas.fi, a Finnish
outdoor navigation web app) uses to build a Derivative Database from
OpenStreetMap data. The database feeds a map overlay showing public toilets,
parking areas and drinking-water points in Finland. It is published to satisfy
Section 4.6(b) of the Open Database Licence (ODbL) v1.0: "the method of making
the alterations to the Database".

Source data: (c) OpenStreetMap contributors, ODbL v1.0,
https://www.openstreetmap.org/copyright. See `LICENCE-NOTICE.md` for the
licence and attribution statement and the publication status.

The method has two stages. Both are part of it:

1. **Extraction** - `polkuopas-osm-poi-extract.sh` (this repository).
2. **Selection applied before use** - described below in prose, because the
   code that applies it lives in Polkuopas's private application repository.

## Files

- `polkuopas-osm-poi-extract.sh` - the extraction pipeline. Downloads
  Geofabrik's Finland PBF, filters to `amenity` in
  `(toilets, parking, drinking_water)` with `osmium` (nodes, ways and
  relations), computes a representative point for way and relation geometry
  with GDAL/`ogr2ogr`, and writes one GeoJSON `FeatureCollection`. Each
  feature carries `osm_type` (`node`/`way`/`relation`), `osm_id`, `amenity`,
  `name` and `geom_method` (`native` for nodes, `bbox_center` for ways and
  relations).
- `osmconf-polkuopas.ini` - GDAL OSM-driver configuration the script needs
  (stock GDAL 3.8 config plus `amenity` as a direct column on the `points`
  and `lines` layers). It must sit beside the script.
- `LICENCE-NOTICE.md` - licence, attribution and publication status.
- `README.md` - this file.

Run it with `bash polkuopas-osm-poi-extract.sh`. It needs `osmium-tool`,
`gdal-bin`, `jq` and `curl` on the PATH, and writes
`polkuopas-osm-poi-extract-fi.geojson` to the current directory. It never
calls the Overpass API.

## Representative points for ways and relations

About 94 % of Finland's `amenity=parking` objects are ways, so they need a
single point. The script uses the centre of the object's bounding box
(`ST_Centroid(ST_Envelope(geometry))`), which is the same convention as
Overpass's `out center`, and not the area-weighted centroid. Every produced
coordinate is checked against a Finland bounding box (latitude 59 to 71,
longitude 19 to 32); anything outside is reported and dropped.

## Selection applied before use

The GeoJSON file written by the script is not shown to users as-is. Before the
features are loaded into the database that powers the public map, the three
rules below are applied. Processing order per feature is: rule 1, then rule 2,
then rule 3. Distances are great-circle (haversine) distances in metres on a
sphere of radius 6,371,008.8 m between the feature's point and the other point.

**Rule 1 - groundwater monitoring wells (drinking water only).** A
`drinking_water` feature is dropped if its `name` contains, case-insensitively,
any of the strings `pohjavesi`, `havaintoputki` or `tarkkailuputki`. These are
groundwater observation wells that are tagged `amenity=drinking_water` in
OpenStreetMap but are not drinkable.

**Rule 2 - de-duplication against Metsahallitus points.** The map also shows
points of interest published by Metsahallitus (the Finnish state forest and
nature-services agency). An OpenStreetMap feature is dropped if a
Metsahallitus point of the same kind lies within **40 m** of it:

| OSM feature          | Same-kind Metsahallitus point type |
| -------------------- | ---------------------------------- |
| `amenity=toilets`        | dry toilet (`kuivakaymala`)        |
| `amenity=drinking_water` | water point (`vesipiste`)          |
| `amenity=parking`        | parking area (`pysakointialue`)    |

The purpose is to avoid two icons for one real-world facility. A feature is
never dropped because of a Metsahallitus point of a different kind. Only OSM
features are ever removed by this rule; no Metsahallitus data is added to,
or mixed into, any OSM feature.

**Rule 3 - parking proximity filter (parking only).** All `toilets` and all
`drinking_water` features that survive rules 1 and 2 are kept. A `parking`
feature that survives rule 2 is kept only if its point lies within **500 m** of
at least one anchor point, otherwise it is dropped. Anchor points are:

- the start point of every hiking or outdoor route in Polkuopas's route data
  (the first coordinate of the route line); and
- the location of every Polkuopas point of interest of a destination type that
  people drive to: wilderness hut, reservable hut, day hut, outdoor-recreation
  lodge, lean-to shelter, fire shelter, fire site, firewood shelter, tent site,
  campground, viewpoint, nature tower, trailhead information board and
  canoeing place.

  Urban sport and leisure sites (disc-golf courses, local sports places,
  outdoor gyms, jogging tracks, playgrounds, beaches, swimming spots), service
  facilities (toilets, water points, parking areas, waste points, sauna and
  service buildings) and infrastructure or catch-all types are deliberately
  not anchors.

Why 500 m: Finland has roughly 68,000 OSM parking features, nearly all urban or
roadside. Keeping only those near a trailhead or outdoor destination keeps the
dataset to the parking relevant to an outdoor app. The 500 m and 40 m values
are tunable constants chosen by judgement, not measured values, and may be
adjusted; if they change, this section is updated in the same change.

Notes on how the selection behaves:

- The selection is a snapshot taken when the load runs. Routes and points of
  interest added later widen the parking set the next time the load runs.
- The load only inserts and updates records, keyed on `(osm_type, osm_id)`
  (OSM ids are unique only within one element type). It does not remove
  records that fall out of scope on a later run, so the published database can
  temporarily hold features that a fresh run of rules 1 to 3 would now drop.
  This does not add any OSM feature outside the three tags above.
- The Metsahallitus and Polkuopas route and point-of-interest data used as
  inputs to rules 2 and 3 are not part of the OpenStreetMap-derived database
  and are not covered by this repository.
- The stored database keeps only these attributes per feature: OSM element
  type, OSM id, amenity kind, name, point coordinates, the point method
  (`native` or `bbox_center`), a source label and the extract date. Everything
  else in the OSM data is discarded.

## Attribution

Wherever the overlay is shown, the map displays "Map data (c) OpenStreetMap
contributors" in its attribution control.

## Norway core types (2026-11)

This repository also publishes a second, separate Derivative Database: OpenStreetMap
objects in Norway of four outdoor place types (viewpoint, swimming place, fire
place, tent site). The database file is `polkuopas-osm-no-core.geojson` at the
repository root. Its method (extractor, tag whitelist, classification and
duplicate rules, rebuild steps) and the ODbL 1.0 text are in `norway-core/`
(`norway-core/README.md`, `norway-core/rules/`, `norway-core/LICENSE`). The
Finnish method described above is not changed by this addition. See
`LICENCE-NOTICE.md` for scope and publication status.
