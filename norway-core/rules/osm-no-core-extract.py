#!/usr/bin/env python3
"""OSM Norway core-type extract (KAN-1516, Sprint 101). Builds the ODbL extract that the loader
`data/nordic-sync/datasets/osm-no-core.ts` reads, and that is published in the public extract repo
(counsel condition O5) before any row is visible.

Scope: four classes only, as agreed for Sprint 101 (docs/research/2026-11-18-norway-osm-core-gap-yield.md):
  tourism=viewpoint
  leisure=bathing_place, leisure=swimming_area
  leisure=firepit, amenity=bbq
  tourism=camp_site, tourism=camp_pitch
Nothing else leaves the PBF. Only whitelisted tags are kept (counsel O7): no contact:*, phone, email, website,
operator, note or description. No official-source column or row can appear here: the input is one OSM PBF.

Input : a Norway OSM PBF (Geofabrik europe/norway-latest.osm.pbf or the download.openstreetmap.fr mirror).
Output: GeoJSON FeatureCollection of Points. Ways get the bounding-box centre of their nodes (the same rule as
        data/osm-poi-extract/, i.e. Overpass `out center`); relations are not read (the count of skipped relations is
        printed so the loss is visible). Each feature carries osm_type, osm_id, osm_version, osm_timestamp,
        class_tag, geom_method, fylke_code (the `ref` of the OSM admin_level=4 area that contains the point; the
        2024 county numbers, the same two digits as the first two of a Kartverket municipality number) and `tags`.

Run (needs `pip install osmium shapely`; reads the whole country, about 8 minutes, 4 GB RAM):
  python3 data/nordic-sync/tools/osm-no-core-extract.py norway-latest.osm.pbf polkuopas-osm-no-core.geojson
"""
import json
import sys

import osmium
import shapely.wkt
from shapely.geometry import Point
from shapely.prepared import prep

CLASSES = {
    ("tourism", "viewpoint"),
    ("leisure", "bathing_place"),
    ("leisure", "swimming_area"),
    ("leisure", "firepit"),
    ("amenity", "bbq"),
    ("tourism", "camp_site"),
    ("tourism", "camp_pitch"),
}
# Counsel O7 whitelist. `name` is the OSM name verbatim. supervised/lit/operator are NOT kept (safety-ish or person data).
TAG_WHITELIST = ["name", "access", "fee", "tents", "caravans", "backcountry", "capacity"]


def main(pbf: str, out: str) -> None:
    counties = []
    areas = osmium.FileProcessor(pbf).with_areas(osmium.filter.TagFilter(("boundary", "administrative"))).with_filter(
        osmium.filter.EntityFilter(osmium.osm.AREA)
    )
    for a in areas:
        t = a.tags
        if t.get("boundary") == "administrative" and t.get("admin_level") == "4" and not a.from_way():
            geom = shapely.wkt.loads(osmium.geom.WKTFactory().create_multipolygon(a))
            counties.append((t.get("ref"), prep(geom)))
    if len(counties) < 15:
        raise SystemExit(f"only {len(counties)} county polygons found; refusing to write an extract without fylke codes")

    features = []
    relations_skipped = 0
    fp = osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.NODE | osmium.osm.WAY))
    for o in fp:
        cls = None
        for k in ("tourism", "leisure", "amenity"):
            v = o.tags.get(k)
            if v is not None and (k, v) in CLASSES:
                cls = f"{k}={v}"
                break
        if cls is None:
            continue
        if o.is_node():
            lon, lat, method, otype = o.lon, o.lat, "native", "node"
        else:
            try:
                xs = [n.lon for n in o.nodes]
                ys = [n.lat for n in o.nodes]
            except Exception:  # a way whose nodes are not in the extract
                continue
            if not xs:
                continue
            lon, lat, method, otype = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, "bbox_center", "way"
        p = Point(lon, lat)
        code = next((ref for ref, pg in counties if pg.contains(p)), None)
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
                "properties": {
                    "osm_type": otype,
                    "osm_id": o.id,
                    "osm_version": o.version,
                    "osm_timestamp": o.timestamp.isoformat() if o.timestamp else None,
                    "class_tag": cls,
                    "geom_method": method,
                    "fylke_code": code,
                    "tags": {k: o.tags.get(k) for k in TAG_WHITELIST if o.tags.get(k) is not None},
                },
            }
        )
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    print(f"{len(features)} features, {len(counties)} county polygons, {relations_skipped} relations read (relations are not read)", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
