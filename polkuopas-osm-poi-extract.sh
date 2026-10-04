#!/usr/bin/env bash
#
# polkuopas-osm-poi-extract.sh
#
# ODbL Section 4.6(b) compliance artifact for Polkuopas (https://polkuopas.fi),
# published at https://github.com/Simopee/polkuopas-osm-extract. It is also
# the pipeline Polkuopas runs to produce the precomputed toilet / parking /
# drinking-water extract behind its map overlay. These are deliberately the
# SAME file: publishing the literal production script means there is no
# separate "compliance copy" that can drift from what actually runs.
#
# This script documents "the method of making the alterations to the
# Database" (the ODbL Section 4.6(b) wording) for the first stage of the
# Derivative Database. A second stage, a selection applied after this script
# (parking proximity filter, de-duplication against Metsahallitus points and
# a groundwater-monitoring-well name filter), is described in README.md
# ("Selection applied before use"). Read both.
#
# Publication status: see LICENCE-NOTICE.md beside this file.
#
# Source dataset: Geofabrik's Finland OSM extract
#   https://download.geofabrik.de/europe/finland-latest.osm.pbf
# Licence of the source data: Open Database License (ODbL) v1.0
#   https://opendatacommons.org/licenses/odbl/1.0/
# Running this script produces a Derivative Database within the meaning of ODbL
# Section 1. See LICENCE-NOTICE.md in this same directory for the full
# attribution and licence statement.
#
# Never calls the Overpass API: the extract is derived from Geofabrik's full
# Finland extract locally with osmium + GDAL, so there is no runtime
# third-party dependency.
#
# Dependencies: bash, curl, osmium (osmium-tool), ogr2ogr (gdal-bin), jq.
# All available via `apt-get install osmium-tool gdal-bin jq` on a standard
# Ubuntu / GitHub Actions ubuntu-latest runner.
#
# ---------------------------------------------------------------------------
# WHY THE CENTROID METHOD IS "BOUNDING-BOX CENTER", NOT A TRUE AREA CENTROID
# ---------------------------------------------------------------------------
# 63 835 of Finland's 68 083 `amenity=parking` OSM objects (verified 2026-08-12
# against the 2026-08-11 Geofabrik snapshot) are WAYS, not point nodes, and need a
# representative point computed from their polygon geometry. The live route
# this pipeline replaces gets that point from Overpass's `out center;` — and
# Overpass's own documentation (wiki.openstreetmap.org/wiki/Overpass_API/
# Overpass_QL, "Latitude and Longitude" section, fetched 2026-08-12) states
# plainly: "For ways and relations it refers to the coordinate derived from
# the center of the bounding box." NOT the area-weighted polygon centroid a
# GIS tool would compute by default. This pipeline reproduces that same
# bounding-box-center algorithm deliberately, via
# `ST_Centroid(ST_Envelope(geometry))` below, specifically so that cutting
# over from the live Overpass call to this static extract does not silently
# move any icon on the map — a true area centroid would visibly disagree
# with today's behaviour for any non-convex/L-shaped parking lot.
#
# ---------------------------------------------------------------------------
# TAG SCOPE — matches the LIVE route's query, not an earlier draft's
# ---------------------------------------------------------------------------
# An earlier draft of this script filtered
# `n/amenity=toilets` and `n/amenity=drinking_water` — nodes only — while
# using `nwr/amenity=parking` for the areas. Toilets and
# drinking_water mapped as ways or relations are rare but real, so that was
# too narrow. This script uses `nwr` for all three tags.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/osmconf-polkuopas.ini"

FINLAND_PBF_URL="https://download.geofabrik.de/europe/finland-latest.osm.pbf"
WORKDIR="$(mktemp -d)"
OUTPUT="${OUTPUT:-polkuopas-osm-poi-extract-fi.geojson}"

# Finland bbox sanity bounds. Every feature this script produces is checked
# against these before being written to $OUTPUT; anything outside is
# reported and dropped rather than silently shipped, on the theory that
# Geofabrik's own Finland extract should never produce an out-of-bounds
# point, so an occurrence here is a signal something upstream (bad geometry,
# a coordinate-axis bug in this script) needs investigating, not routine
# filtering.
FINLAND_LAT_MIN=59
FINLAND_LAT_MAX=71
FINLAND_LNG_MIN=19
FINLAND_LNG_MAX=32

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

echo "== Step 1/5: downloading ${FINLAND_PBF_URL}"
curl -L --fail -o "${WORKDIR}/finland-latest.osm.pbf" "$FINLAND_PBF_URL"
echo "   $(du -h "${WORKDIR}/finland-latest.osm.pbf" | cut -f1) downloaded."

echo "== Step 2/5: filtering to amenity in (toilets, parking, drinking_water)"
# nwr = node + way + relation, for all three tags — see the header comment
# above ("TAG SCOPE") for why this differs from an earlier narrower draft.
osmium tags-filter \
  "${WORKDIR}/finland-latest.osm.pbf" \
  nwr/amenity=toilets \
  nwr/amenity=parking \
  nwr/amenity=drinking_water \
  -o "${WORKDIR}/osm-poi-filtered.osm.pbf" --overwrite

echo "== Step 3/5: extracting geometry per OSM element type"
# GDAL's OSM driver default osmconf.ini does not expose `amenity` as a direct
# column on the points/lines layers (only on multipolygons) — osmconf-
# polkuopas.ini alongside this script adds it, so every query below can
# filter on `amenity` directly instead of parsing the `other_tags` HSTORE
# blob. Point features without a "significant" tag (bare way-geometry nodes)
# are still dropped by GDAL's own unrelated defaults, so this does not turn
# ordinary geometry nodes into spurious POI features.

# --- Nodes: geometry is already a point, used verbatim (geom_method=native).
ogr2ogr -f GeoJSON "${WORKDIR}/points.geojson" \
  -oo CONFIG_FILE="$CONFIG_FILE" \
  "${WORKDIR}/osm-poi-filtered.osm.pbf" \
  -dialect sqlite -sql "
    SELECT osm_id, amenity, name, 'node' AS osm_type, 'native' AS geom_method, geometry
    FROM points
    WHERE amenity IN ('toilets','parking','drinking_water')
  "

# --- Closed ways treated as polygons, and type=multipolygon/boundary
# relations. `osm_way_id` is set for the former, `osm_id` for the latter —
# mutually exclusive, per GDAL's own osmconf.ini contract for this layer.
# When a way is itself the outer member of a multipolygon relation that
# carries the SAME amenity tag (a real, if uncommon, OSM tagging pattern —
# verified against two live examples), GDAL emits only
# the relation-level assembled polygon, not a duplicate for the member way
# too. That is correct: it is one physical parking area, and this pipeline
# must not double-count it.
ogr2ogr -f GeoJSON "${WORKDIR}/polygons.geojson" \
  -oo CONFIG_FILE="$CONFIG_FILE" \
  "${WORKDIR}/osm-poi-filtered.osm.pbf" \
  -dialect sqlite -sql "
    SELECT
      COALESCE(osm_way_id, osm_id) AS osm_id,
      amenity, name,
      CASE WHEN osm_way_id IS NOT NULL THEN 'way' ELSE 'relation' END AS osm_type,
      'bbox_center' AS geom_method,
      ST_Centroid(ST_Envelope(geometry)) AS geometry
    FROM multipolygons
    WHERE amenity IN ('toilets','parking','drinking_water')
  "

# --- Ways tagged with one of the three amenities but NOT a closed ring —
# a genuine upstream OSM data-quality condition (e.g. way 1240958985,
# amenity=parking, unclosed as of the 2026-08-11 extract used for
# verification), not a defect in this pipeline. GDAL's closed-way-as-polygon
# logic puts these in `lines` instead of `multipolygons`. Same bbox-center
# method, for the same drop-in-compatibility reason as above.
ogr2ogr -f GeoJSON "${WORKDIR}/lines.geojson" \
  -oo CONFIG_FILE="$CONFIG_FILE" \
  "${WORKDIR}/osm-poi-filtered.osm.pbf" \
  -dialect sqlite -sql "
    SELECT osm_id, amenity, name, 'way' AS osm_type, 'bbox_center' AS geom_method,
      ST_Centroid(ST_Envelope(geometry)) AS geometry
    FROM lines
    WHERE amenity IN ('toilets','parking','drinking_water')
  "

# --- Relations whose `type` tag is not `multipolygon`/`boundary` (e.g.
# `type=site`, `type=building`) — GDAL only assembles those two relation
# types into polygons by design, since a `site` relation groups unrelated
# objects rather than describing one area. These land in `other_relations`
# as a GeometryCollection with no direct `amenity` column, so the tag is
# read from `other_tags` (OSM's HSTORE tag blob) via a LIKE match — safe
# here because the match set is a closed, known list of three literal tag
# values, not free text. `ST_Centroid(ST_Envelope(...))` still works on a
# GeometryCollection: it computes the envelope of every component geometry
# combined, which is exactly the "bounding box of everything in this
# relation" this pipeline wants.
ogr2ogr -f GeoJSON "${WORKDIR}/other_relations.geojson" \
  -oo CONFIG_FILE="$CONFIG_FILE" \
  "${WORKDIR}/osm-poi-filtered.osm.pbf" \
  -dialect sqlite -sql "
    SELECT
      osm_id, name,
      CASE
        WHEN other_tags LIKE '%\"amenity\"=>\"toilets\"%' THEN 'toilets'
        WHEN other_tags LIKE '%\"amenity\"=>\"parking\"%' THEN 'parking'
        WHEN other_tags LIKE '%\"amenity\"=>\"drinking_water\"%' THEN 'drinking_water'
      END AS amenity,
      'relation' AS osm_type, 'bbox_center' AS geom_method,
      ST_Centroid(ST_Envelope(geometry)) AS geometry
    FROM other_relations
    WHERE other_tags LIKE '%\"amenity\"=>\"toilets\"%'
       OR other_tags LIKE '%\"amenity\"=>\"parking\"%'
       OR other_tags LIKE '%\"amenity\"=>\"drinking_water\"%'
  "

echo "== Step 4/5: merging layers, applying Finland bbox sanity filter"
# osm_id arrives from ogr2ogr as a string (GDAL's own OSM driver convention,
# not a choice made here) — cast to a number so downstream consumers (e.g. a
# bigint database column) get the right type.
# NOTE for any consumer that stores this: osm_id is only unique WITHIN one
# osm_type (a node #123, a way #123, and a relation #123 can all exist
# independently in OSM) — (osm_type, osm_id), not osm_id alone, must be the
# uniqueness/conflict key.
jq -s '
  {
    type: "FeatureCollection",
    features: (
      (map(.features) | add // [])
      | map(.properties.osm_id |= (tonumber? // .))
      | map(select(
          .geometry.coordinates[1] >= '"$FINLAND_LAT_MIN"' and
          .geometry.coordinates[1] <= '"$FINLAND_LAT_MAX"' and
          .geometry.coordinates[0] >= '"$FINLAND_LNG_MIN"' and
          .geometry.coordinates[0] <= '"$FINLAND_LNG_MAX"'
        ))
    )
  }
' "${WORKDIR}/points.geojson" "${WORKDIR}/polygons.geojson" "${WORKDIR}/lines.geojson" "${WORKDIR}/other_relations.geojson" \
  > "$OUTPUT"

BEFORE_BBOX_FILTER=$(jq -s '[.[].features] | add | length' "${WORKDIR}/points.geojson" "${WORKDIR}/polygons.geojson" "${WORKDIR}/lines.geojson" "${WORKDIR}/other_relations.geojson")
AFTER_BBOX_FILTER=$(jq '.features | length' "$OUTPUT")
DROPPED=$((BEFORE_BBOX_FILTER - AFTER_BBOX_FILTER))

echo "== Step 5/5: summary"
echo "Wrote ${OUTPUT}: ${AFTER_BBOX_FILTER} features."
echo "Features per amenity:"
jq -r '.features | group_by(.properties.amenity) | map("  \(.[0].properties.amenity): \(length)") | .[]' "$OUTPUT"
echo "Features per OSM element type:"
jq -r '.features | group_by(.properties.osm_type) | map("  \(.[0].properties.osm_type): \(length)") | .[]' "$OUTPUT"
echo "Dropped by Finland bbox sanity filter: ${DROPPED} (expected: 0)"
if [ "$DROPPED" -ne 0 ]; then
  echo "WARNING: non-zero drop count — investigate before trusting this extract." >&2
fi
