#!/usr/bin/env python3
"""OSM Norway huts and shelters extract (KAN-1684, Sprint 103). Builds the ODbL extract that the loader
`data/nordic-sync/datasets/osm-no-huts/transform.ts` reads. Sibling of osm-no-core-extract.py with the same method: nodes and ways,
ways reduced to the bounding-box centre of their nodes, fylke code from the OSM admin_level=4 area that contains the point,
whitelisted tags only, relations not read.

Scope: three classes only (docs/research/2026-11-20-kan1684-osm-gap-types.md):
  tourism=alpine_hut
  tourism=wilderness_hut
  amenity=shelter   (whether a shelter counts as a hut is decided in datasets/osm-no-huts/classify.ts from shelter_type; the
                     extractor keeps shelter_type so the rule is applied once, in the loader, and is published with the rules)
Only whitelisted tags are kept (counsel O7): no contact:*, phone, email, website, operator, owner, note, description, fixme.
access, shelter_type and building are classification inputs and are never shown on a card. `reservation` is NOT kept (counsel 2026-11-21,
section 7: no rule uses it, and a published reservation=yes next to a hut point invites the booking reading the card must avoid).

Two rules are applied HERE, before the whitelist drops the tags they read, and are published with this file (counsel 2026-11-21 condition 7, O5):
  1. weather_shelter_excluded: an amenity=shelter + shelter_type=weather_shelter that is also tagged public_transport=*, highway=bus_stop,
     amenity=bus_station or building=* is a bus stop or a building, not a hiking shelter, and is dropped.
  2. svalbard_or_jan_mayen: no point on Svalbard (fylke 21), Bjornoya or Jan Mayen (fylke 22) survives (founder 2026-11-21). Two independent tests:
     the fylke code, and a coordinate guard (latitude 74 N or higher; above 70 N and west of longitude 0; plus the boxes of osm-no-core/classify.ts).
3. name_withheld: the O7 name screen (e-mail, URL, phone-like, c/o); the point is kept, only the name is left out.
The loader (datasets/osm-no-huts/classify.ts) applies the same Svalbard test again. Dropped objects are counted per reason on stderr.

Run (needs `pip install osmium shapely`; reads the whole country, about 8 minutes):
  python3 -I data/nordic-sync/tools/osm-no-huts-extract.py norway.osm.pbf polkuopas-osm-no-huts.geojson
"""
import collections
import json
import re
import sys

CLASSES = {
    ("tourism", "alpine_hut"),
    ("tourism", "wilderness_hut"),
    ("amenity", "shelter"),
}
TAG_WHITELIST = ["name", "access", "shelter_type", "building"]

# Same boxes as data/nordic-sync/datasets/osm-no-core/classify.ts (SVALBARD_BOX, JAN_MAYEN_BOX): south, north, west, east.
SVALBARD_BOX = (72.0, 82.0, 9.0, 34.0)
JAN_MAYEN_BOX = (70.8, 71.2, -9.3, -7.9)


def weather_shelter_excluded(tags) -> bool:
    """True for a weather shelter that is really a bus stop or a building (decided before the whitelist drops these tags)."""
    if tags.get("shelter_type") != "weather_shelter":
        return False
    return (
        tags.get("public_transport") is not None
        or tags.get("highway") == "bus_stop"
        or tags.get("amenity") == "bus_station"
        or tags.get("building") is not None
    )


def name_withheld(name) -> bool:
    """Counsel O7 name screen, applied here as well so the published file holds no contact-like name: e-mail, URL, phone-like digit run (7 digits or a +NN prefix), c/o."""
    if not name:
        return False
    return bool(
        "@" in name
        or re.search(r"https?:|www\.", name, re.I)
        or len(re.findall(r"\d", name)) >= 7
        or re.search(r"\+\d{2}", name)
        or re.search(r"\bc/o\b", name, re.I)
    )


def svalbard_or_jan_mayen(lat: float, lon: float, fylke_code) -> bool:
    """No Svalbard (21), Bjornoya or Jan Mayen (22) row survives. Mainland Norway lies east of 4 E and south of 71.2 N."""
    if fylke_code in ("21", "22"):
        return True
    if lat >= 74 or (lat > 70 and lon < 0):
        return True
    for south, north, west, east in (SVALBARD_BOX, JAN_MAYEN_BOX):
        if south <= lat <= north and west <= lon <= east:
            return True
    return False


def main(pbf: str, out: str) -> None:
    import osmium  # imported here so the pure rules above can be tested without pyosmium
    import shapely.wkt
    from shapely.geometry import Point
    from shapely.prepared import prep

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
    dropped = collections.Counter()
    fp = osmium.FileProcessor(pbf).with_locations().with_filter(osmium.filter.EntityFilter(osmium.osm.NODE | osmium.osm.WAY))
    for o in fp:
        cls = None
        for k in ("tourism", "amenity"):
            v = o.tags.get(k)
            if v is not None and (k, v) in CLASSES:
                cls = f"{k}={v}"
                break
        if cls is None:
            continue
        if cls == "amenity=shelter" and weather_shelter_excluded(o.tags):
            dropped["excluded-weather-shelter-bus-stop-or-building"] += 1
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
        if svalbard_or_jan_mayen(lat, lon, code):
            dropped["excluded-svalbard-jan-mayen"] += 1
            continue
        if name_withheld(o.tags.get("name")):
            dropped["name-withheld-kept-point"] += 1
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
                    "tags": {k: o.tags.get(k) for k in TAG_WHITELIST if o.tags.get(k) is not None and not (k == "name" and name_withheld(o.tags.get(k)))},
                },
            }
        )
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False)
    print(f"{len(features)} features, {len(counties)} county polygons (relations are not read)", file=sys.stderr)
    print(f"dropped before writing: {dict(dropped)}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
