#!/usr/bin/env python3
"""Counsel O7 check for the OSM Norway huts and shelters extract (KAN-1684). Run before the file is published or loaded:

  python3 -I data/nordic-sync/tools/osm-no-huts-o7-check.py polkuopas-osm-no-huts.geojson

Exit 0 when the file holds none of: phone, contact:*, email, website, operator, note, description, fee, capacity, reservation (as tag keys or anywhere as a
quoted key), no property outside the allowed set, no tag outside the whitelist (name, access, shelter_type, building), no '@' or 'http' in the file, no name with a
7-digit run or a +NN prefix, no class outside the three hut classes, and no point on Svalbard, Bjornoya or Jan Mayen. Exit 1 and a list of violations otherwise.
"""
import collections
import json
import re
import sys

BANNED = ["phone", "contact:", "email", "website", "operator", "note", "description", "fee", "capacity", "reservation", "supervised"]
WHITELIST = {"name", "access", "shelter_type", "building"}
PROPS = {"osm_type", "osm_id", "osm_version", "osm_timestamp", "class_tag", "geom_method", "fylke_code", "tags"}
CLASSES = {"tourism=alpine_hut", "tourism=wilderness_hut", "amenity=shelter"}


def check(path: str) -> list[str]:
    raw = open(path, encoding="utf-8").read()
    d = json.loads(raw)
    bad: list[str] = []
    if d.get("type") != "FeatureCollection":
        bad.append("not a FeatureCollection")
    for f in d["features"]:
        p = f["properties"]
        who = f"{p.get('osm_type')}/{p.get('osm_id')}"
        extra = set(p) - PROPS
        if extra:
            bad.append(f"{who}: property outside the allowed set: {sorted(extra)}")
        if p.get("class_tag") not in CLASSES:
            bad.append(f"{who}: class outside the three hut classes: {p.get('class_tag')}")
        for k in p["tags"]:
            if k not in WHITELIST:
                bad.append(f"{who}: tag outside the whitelist: {k}")
        lon, lat = f["geometry"]["coordinates"]
        if p.get("fylke_code") in ("21", "22") or lat >= 74 or (lat > 70 and lon < 0):
            bad.append(f"{who}: Svalbard or Jan Mayen point")
        name = p["tags"].get("name", "")
        if re.search(r"\d{7}", name) or re.search(r"\+\d{2}", name):
            bad.append(f"{who}: name looks like a phone number")
    for b in BANNED:
        n = raw.count('"' + b)
        if n:
            bad.append(f"quoted key starting with {b}: {n} occurrence(s)")
    for needle in ("@", "http"):
        if needle in raw:
            bad.append(f"'{needle}' appears in the file ({raw.count(needle)} times)")
    return bad


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    problems = check(sys.argv[1])
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    keys = collections.Counter(k for f in d["features"] for k in f["properties"]["tags"])
    print(f"{len(d['features'])} features; tag keys {dict(keys)}")
    for p in problems:
        print("VIOLATION:", p)
    print("O7 check:", "FAILED" if problems else "passed")
    sys.exit(1 if problems else 0)
