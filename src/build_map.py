#!/usr/bin/env python3
"""Build a compatible, public-domain China province layer for future edits.

Not the same geometry as the previously rendered v4 video; do not claim a
bit-identical re-render. Input: Natural Earth 50m admin-1 archive v5.1.1 and
project's Natural Earth 50m admin-0 world50.json. pyshp required.
"""
import argparse
import json
import zipfile
from pathlib import Path

import shapefile

# The existing animation looks up these four GB/T-style two-digit IDs.
HIGHLIGHTS = {"CN-GZ": "52", "CN-GX": "45", "CN-YN": "53", "CN-CQ": "50"}
EXTRA = {"Taiwan": ("71", "台湾省"), "Hong Kong": ("81", "香港特别行政区"),
         "Macao": ("82", "澳门特别行政区")}


def make_map(admin1_zip, world_json):
    with zipfile.ZipFile(admin1_zip) as archive:
        prefix = "ne_50m_admin_1_states_provinces"
        # Open only the named Natural Earth files; zipfile is never extracted.
        reader = shapefile.Reader(shp=archive.open(prefix + ".shp"),
                                  shx=archive.open(prefix + ".shx"),
                                  dbf=archive.open(prefix + ".dbf"), encoding="utf-8")
        features = []
        for row in reader.iterShapeRecords():
            rec = row.record.as_dict()
            if rec.get("adm0_a3") != "CHN":
                continue
            iso = rec.get("iso_3166_2")
            features.append({"type": "Feature", "properties": {
                "id": HIGHLIGHTS.get(iso, iso), "name": rec.get("name_zh") or rec["name"],
                "source": "Natural Earth 50m admin-1 5.1.1",
            }, "geometry": row.shape.__geo_interface__})
    world = json.loads(Path(world_json).read_text(encoding="utf-8"))
    for item in world["features"]:
        name = item["properties"].get("NAME")
        if name in EXTRA:
            pid, zh = EXTRA[name]
            features.append({"type": "Feature", "properties": {
                "id": pid, "name": zh, "source": "Natural Earth 50m admin-0",
            }, "geometry": item["geometry"]})
    ids = {f["properties"]["id"] for f in features}
    if len(features) < 34 or not set(HIGHLIGHTS.values()).issubset(ids):
        raise ValueError("Natural Earth dataset unexpected: province highlights missing")
    return {"type": "FeatureCollection", "features": features}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admin1-zip", required=True, type=Path)
    parser.add_argument("--world", default="world50.json", type=Path)
    parser.add_argument("--out", default="c.json", type=Path)
    args = parser.parse_args()
    args.out.write_text(json.dumps(make_map(args.admin1_zip, args.world), ensure_ascii=False,
                                   separators=(",", ":")), encoding="utf-8")
    print("wrote", args.out)
