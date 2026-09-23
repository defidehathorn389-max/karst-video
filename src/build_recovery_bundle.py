#!/usr/bin/env python3
"""Package explicitly allowlisted v4 inputs for safe, non-bit-exact future edits.

Run with --inputs original local project and --sources checked-out karst-video/src.
The output is a Release asset, never a Git repository blob. No MP4 final movie,
raw stock footage, credentials, private progress or unknown-licence c.json included.
"""
import argparse
import ast
import hashlib
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import quote

LIC = {
    "CC BY 2.0": "https://creativecommons.org/licenses/by/2.0/",
    "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "Public domain": "https://commons.wikimedia.org/wiki/Commons:Licensing#Material_in_the_public_domain",
}
SCRIPTS = ["render.py", "premium.py", "v4graphics.py", "restore_used.py", "music.py",
           "build_map.py", "build_recovery_bundle.py", "requirements-recovery.txt"]
STATIC = ["world50.json", "vsel.json", "audio_map.json"]


def make_credits(photo_rows, stock_rows):
    lines = ["# Attribution for files used in this recovery edition", "",
             "Recorded licence metadata from the original Wikimedia Commons inventory. This file",
             "does not replace checking the live file page before another distribution. Photographs",
             "are Commons thumbnails; in the video they were additionally cropped, moved and tinted.",
             "Retain each file's licence (including BY-SA where applicable); the project's MIT",
             "code licence does **not** apply to third-party media. Stock video is not in this ZIP;",
             "when recovered it is cut, slowed/reframed and graded by restore_used.py.", "",
             "## Photographs included", ""]
    for path, title, author, lic in photo_rows:
        url = "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_"), safe=":()'_-.")
        assert lic in LIC, lic
        lines.append(f"- `{path}` — [{title}]({url}) — {author}; [{lic}]({LIC[lic]}). ")
    lines += ["", "## Video sources NOT included (download/verify as needed)", ""]
    for path, title, author, lic in stock_rows:
        url = "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_"), safe=":()'_-.")
        assert lic in LIC, lic
        lines.append(f"- `{path}` — [{title}]({url}) — {author}; [{lic}]({LIC[lic]}).")
    lines += ["", "## Maps and original media", "",
              "- `world50.json`, generated `c.json` and `maps/ne_50m_admin_1_states_provinces.zip`: Natural Earth, public domain, https://www.naturalearthdata.com/about/ . China province geometries in this recovery pack are a compatible **substitute**, not the exact map input used to render the released v4.",
              "- `img/ai_*.jpg`: conceptual AI-generated illustrations; NOT real location photos. Project-produced narration (`audio/`) and animations (`premium.py`, `v4graphics.py`) are not Wikimedia works.",
              ""]
    return "\n".join(lines)


def make_restore_readme():
    return """# v4 recovery inputs (not a bit-identical v4 master)

This archive can be used even when the private progress repository is unavailable.
It contains original script, render code, voice segments and mixed audio, used
photographs/concept art, real-map data and licence records. It deliberately
omits the published MP4 and 14 large licensed stock-video clips. A generated
Natural Earth `c.json` **substitutes** an older province layer with unclear
redistribution provenance; old and new maps are NOT bit-identical.

## Safe recovery

1. Verify the **zip SHA256** against project repository `RECOVERY_v4.json`.
2. Inspect paths before extraction: reject absolute paths, `..`, symlinks and
   suspicious archive entries; extract to an empty dedicated directory.
3. In the extracted directory run:

```bash
python -m pip install -r requirements-recovery.txt
python /path/to/geo-documentary-video-skill/tools/verify_inputs.py --root . --manifest MANIFEST.json --strict
python render.py info
```

`render.py info` must not require stock-video clips because it only checks the
audio-derived timeline, scripts and maps; it is not proof of final render QA.
If you want to regenerate the compatible Natural Earth province layer without
using the prebuilt `c.json`, run `python build_map.py --admin1-zip
maps/ne_50m_admin_1_states_provinces.zip --world world50.json --out c.json`.
Doing that changes a manifest-listed file; re-check against the generated
expected map hash before relying on the archive manifest.

4. For a **new edit** needing footage, review `CREDITS_USED.md` / `vsel.json`
   and check each original Commons page for the location and licence. When
   network and rights permit, run `python restore_used.py` (sequential, large
   downloads); re-encode quality or transcode versions may differ over time.
   If the upstream cannot be fetched, ask for a licensed substitute rather
   than claiming exact restoration.
5. Create `parts/`, then render in **serial**. Approximate 2 GiB method:

```bash
mkdir -p parts
python render.py render 2 0
python -c "import render; render.render(5441,7400,'parts/p1a.mp4')"
python -c "import render; render.render(7400,9050,'parts/p1b.mp4')"
python -c "import render; render.render(9050,10883,'parts/p1c.mp4')"
printf "file 'p0.mp4'\\nfile 'p1a.mp4'\\nfile 'p1b.mp4'\\nfile 'p1c.mp4'\\n" > parts/list.txt
FF=$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
"$FF" -y -f concat -safe 0 -i parts/list.txt -i audio/mix.m4a \\
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a copy -movflags +faststart \\
  -shortest v4_recreated_with_substitute_map.mp4
```

Frame breakpoints assume 24 fps and old total length; after any script/audio
change, recompute them with `render.py info` before proceeding. Check final
resolution, fps, length, audio, complete decode, subtitles, footage labels,
licences, and genuinely observe a short animation clip. The issued v4 MP4 is
already available from the project v4.0 Release; **do not overwrite it**.
If user approved a new duration or an unpublished edit, that approval is in
private project progress (if accessible), NOT inferred from this static bundle.
"""


def bundle(inputs, sources, c_map, admin1_zip, out):
    files = {}
    for name in SCRIPTS:
        files[name] = (sources / name).read_bytes()
    for name in STATIC:
        files[name] = (inputs / name).read_bytes()
    files["c.json"] = c_map.read_bytes()
    files["maps/ne_50m_admin_1_states_provinces.zip"] = admin1_zip.read_bytes()
    for p in sorted((inputs / "script").glob("s[1-8].txt")):
        files[f"script/{p.name}"] = p.read_bytes()
    if len([name for name in files if name.startswith("script/")]) != 8:
        raise ValueError("need eight script segments")
    for i in range(1, 9):
        files[f"audio/s{i}.mp3"] = (inputs / "audio" / f"s{i}.mp3").read_bytes()
    files["audio/mix.m4a"] = (inputs / "audio/mix.m4a").read_bytes()
    # Inspect source text only to list exactly the referenced imagery; no code exec.
    text = (sources / "render.py").read_text(encoding="utf-8")
    text += (sources / "premium.py").read_text(encoding="utf-8")
    photos = sorted(set(re.findall(r"img/[A-Za-z0-9_]+\.jpg", text)))
    credits = {}
    for line in (inputs / "credits.tsv").read_text(encoding="utf-8").splitlines():
        chunks = line.split("\t")
        if len(chunks) == 4:
            credits[chunks[0]] = chunks
    photo_rows = []
    for name in photos:
        files[name] = (inputs / name).read_bytes()
        if not name.startswith("img/ai_"):
            if name not in credits:
                raise ValueError(f"photo credit missing: {name}")
            photo_rows.append(credits[name])
    files["credits.tsv"] = "\n".join("\t".join(row) for row in photo_rows).encode("utf-8") + b"\n"
    tree = ast.parse((sources / "restore_used.py").read_text(encoding="utf-8"))
    used = next(ast.literal_eval(node.value) for node in tree.body
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "USED" for t in node.targets))
    stock = list(json.loads((inputs / "vsel.json").read_text(encoding="utf-8")).values())
    stock_rows = []
    for clip_name, (idx, _st, _src_len, _out_len) in used.items():
        v = stock[idx]
        stock_rows.append((f"clips/{clip_name}.mp4", v["title"], v["art"], v["lic"]))
    if len(stock_rows) != 14:
        raise ValueError("expected 14 credited stock clips")
    files["CREDITS_USED.md"] = make_credits(photo_rows, stock_rows).encode("utf-8")
    files["README_RESTORE.md"] = make_restore_readme().encode("utf-8")
    manifest = {"schema": "geo-video-source-manifest/1", "project": "karst-video",
                "release": "v4.0 (recoverable edit inputs)",
                "note": "Published v4 unchanged; compatible public-domain replacement c.json; no stock MP4 included.",
                "files": [{"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                          for path, data in sorted(files.items())]}
    files["MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as archive:
        for path, data in sorted(files.items()):
            info = zipfile.ZipInfo(path, (2026, 9, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)
    sha = hashlib.sha256()
    with out.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            sha.update(block)
    print(json.dumps({"path": str(out), "bytes": out.stat().st_size,
                      "sha256": sha.hexdigest(), "files_in_manifest": len(manifest["files"]),
                      "photos_included": len(photos), "stock_clips_not_included": len(stock_rows)},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--sources", required=True, type=Path)
    parser.add_argument("--map", required=True, type=Path)
    parser.add_argument("--admin1-zip", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    a = parser.parse_args()
    bundle(a.inputs, a.sources, a.map, a.admin1_zip, a.out)
