#!/usr/bin/env python3
"""Counsel O7 check for the OSM Norway core-type extract (KAN-1678). Run before the file is published or loaded:

  python3 -I data/nordic-sync/tools/osm-no-core-o7-check.py polkuopas-osm-no-core.geojson

Exit 0 when the file holds none of: phone, contact:*, email, website, operator, note, description, supervised (as tag keys or anywhere as a
quoted key), no property outside the allowed set, no tag outside the whitelist, no '@' or 'http' in the file, and no name with a 7-digit run
or a +NN prefix. Exit 1 and a list of violations otherwise.
"""
import collections
import json
import re
import sys

BANNED = ["phone", "contact:", "email", "website", "operator", "note", "description", "supervised"]
WHITELIST = {"name", "access", "fee", "tents", "caravans", "backcountry", "capacity"}
PROPS = {"osm_type", "osm_id", "osm_version", "osm_timestamp", "class_tag", "geom_method", "fylke_code", "tags"}


def check(path: str) -> list[str]:
    raw = open(path, encoding="utf-8").read()
    d = json.loads(raw)
    bad: list[str] = []
    if d.get("type") != "FeatureCollection":
        bad.append("not a FeatureCollection")
    for f in d["features"]:
        extra = set(f["properties"]) - PROPS
        if extra:
            bad.append(f"{f['properties'].get('osm_type')}/{f['properties'].get('osm_id')}: property outside the allowed set: {sorted(extra)}")
        for k in f["properties"]["tags"]:
            if k not in WHITELIST:
                bad.append(f"{f['properties']['osm_type']}/{f['properties']['osm_id']}: tag outside the whitelist: {k}")
    for b in BANNED:
        n = raw.count('"' + b)
        if n:
            bad.append(f"quoted key starting with {b}: {n} occurrence(s)")
    for needle in ("@", "http"):
        if needle in raw:
            bad.append(f"'{needle}' appears in the file ({raw.count(needle)} times)")
    for f in d["features"]:
        name = f["properties"]["tags"].get("name", "")
        if re.search(r"\d{7}", name) or re.search(r"\+\d{2}", name):
            bad.append(f"{f['properties']['osm_type']}/{f['properties']['osm_id']}: name looks like a phone number")
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
