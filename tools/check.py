"""Checks every community firmware and builds index.json for the WardriveESP flasher.

    python tools/check.py            check every firmware/<id>/ folder, print what's wrong
    python tools/check.py --index    also write site/index.json and copy the images into site/ (the published files)

A firmware folder is firmware/<id>/ with manifest.json and firmware.bin (one merged image, written at 0x0).
Standard library only, so it runs anywhere Python 3.9+ does.
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "firmware"
SITE = ROOT / "site"
MAX_BYTES = 8 * 1024 * 1024
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,40}$")
# Chip -> (image chip id in the ESP image header, where the bootloader sits in a merged image).
CHIPS = {
    "ESP32": (0, 0x1000),
    "ESP32-C3": (5, 0x0),
    "ESP32-C5": (23, 0x2000),
    "ESP32-C6": (13, 0x0),
    "ESP32-S3": (9, 0x0),
}
REQUIRED = {
    "name": "what people see in the picker, like \"Marauder for the XYZ Board\"",
    "author": "your name or handle",
    "chip": "one of " + ", ".join(CHIPS),
    "boards": "a list of the boards it runs on, like [\"XYZ Board v2\"]",
    "version": "your firmware's version, like \"1.2.0\"",
    "description": "one or two sentences: what it does on these boards",
    "source": "an https:// link to its source code",
    "license": "its license, like \"MIT\" or \"GPL-3.0\"",
}
LIMITS = {"name": 60, "author": 40, "version": 24, "description": 300, "license": 40}


def check_one(folder: Path) -> tuple[list[str], dict | None]:
    """Problems with one firmware folder (empty = good), and its index entry."""
    errs = []
    fid = folder.name
    if not ID_RE.match(fid):
        errs.append(f"folder name '{fid}': use 3-41 lowercase letters, digits and dashes, starting with a letter or digit")
    mpath, bpath = folder / "manifest.json", folder / "firmware.bin"
    extra = sorted(p.name for p in folder.iterdir() if p.name not in ("manifest.json", "firmware.bin", "README.md"))
    if extra:
        errs.append(f"only manifest.json, firmware.bin and an optional README.md go in the folder (found {', '.join(extra)})")
    if not mpath.exists():
        return errs + ["manifest.json is missing (copy template/manifest.json)"], None
    try:
        m = json.loads(mpath.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return errs + [f"manifest.json isn't valid JSON: {e}"], None
    if not isinstance(m, dict):
        return errs + ["manifest.json must be one JSON object"], None
    for key, what in REQUIRED.items():
        if key not in m or m[key] in ("", [], None):
            errs.append(f"manifest.json needs \"{key}\": {what}")
    for key, n in LIMITS.items():
        if isinstance(m.get(key), str) and len(m[key]) > n:
            errs.append(f"\"{key}\" is {len(m[key])} characters, keep it to {n}")
    unknown = sorted(set(m) - set(REQUIRED) - {"notes", "website"})
    if unknown:
        errs.append(f"unknown fields in manifest.json: {', '.join(unknown)}")
    chip = m.get("chip")
    if chip is not None and chip not in CHIPS:
        errs.append(f"\"chip\" is '{chip}', use one of {', '.join(CHIPS)}")
    boards = m.get("boards")
    if boards is not None and (not isinstance(boards, list) or not all(isinstance(b, str) and b.strip() for b in boards)):
        errs.append("\"boards\" must be a list of board names, like [\"XYZ Board v2\"]")
    for key in ("source", "website"):
        if key in m and not (isinstance(m[key], str) and m[key].startswith("https://")):
            errs.append(f"\"{key}\" must be an https:// link")
    if "notes" in m and not (isinstance(m["notes"], str) and len(m["notes"]) <= 300):
        errs.append("\"notes\" must be text of 300 characters or less")
    if not bpath.exists():
        return errs + ["firmware.bin is missing (the merged image, written at 0x0)"], None
    data = bpath.read_bytes()
    if len(data) > MAX_BYTES:
        errs.append(f"firmware.bin is {len(data) // 1024} KB, the limit is {MAX_BYTES // 1024} KB")
    if chip in CHIPS:
        cid, at = CHIPS[chip]
        other = next((c for c, (i, a) in CHIPS.items() if c != chip and len(data) > a + 16 and data[a] == 0xE9
                      and int.from_bytes(data[a + 12:a + 14], "little") == i), None)
        if (len(data) < at + 16 or data[at] != 0xE9) and other:
            errs.append(f"firmware.bin is a merged image for {other}, but the manifest says {chip}")
        elif len(data) < at + 16 or data[at] != 0xE9:
            errs.append(f"firmware.bin isn't a merged {chip} image: the bootloader should start at {hex(at)} "
                        "(build a merged image, e.g. esptool merge_bin, or idf.py merge-bin)")
        elif int.from_bytes(data[at + 12:at + 14], "little") != cid:
            found = next((c for c, (i, _) in CHIPS.items() if i == int.from_bytes(data[at + 12:at + 14], "little")), "another chip")
            errs.append(f"firmware.bin is built for {found}, but the manifest says {chip}")
    if errs:
        return errs, None
    return [], {
        "id": fid,
        "name": m["name"].strip(),
        "author": m["author"].strip(),
        "chip": chip,
        "boards": [b.strip() for b in boards],
        "version": str(m["version"]).strip(),
        "description": m["description"].strip(),
        "notes": (m.get("notes") or "").strip(),
        "source": m["source"],
        "website": m.get("website", ""),
        "license": m["license"].strip(),
        "bin": f"firmware/{fid}/firmware.bin",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> int:
    write = "--index" in sys.argv
    folders = sorted(p for p in FW.iterdir() if p.is_dir()) if FW.exists() else []
    entries, bad = [], 0
    for f in folders:
        errs, entry = check_one(f)
        if errs:
            bad += 1
            print(f"✗ firmware/{f.name}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"✓ firmware/{f.name}: {entry['name']} {entry['version']} ({entry['chip']}, {entry['size'] // 1024} KB)")
            entries.append(entry)
    if bad:
        print(f"\n{bad} firmware folder(s) need fixing. See README.md, \"Submit your firmware\".")
        return 1
    print(f"\nAll {len(entries)} firmware folder(s) look good.")
    if write:
        if SITE.exists():
            shutil.rmtree(SITE)
        SITE.mkdir(parents=True)
        for e in entries:
            dst = SITE / e["bin"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / e["bin"], dst)
        entries.sort(key=lambda e: (e["chip"], e["name"].lower()))
        (SITE / "index.json").write_text(json.dumps({"firmware": entries}, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(ROOT / "tools" / "home.html", SITE / "index.html")
        print(f"Wrote site/index.json with {len(entries)} firmware.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
