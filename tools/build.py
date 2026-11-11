"""Build against a local export; never modify or publish original packages."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from patches import API, DAILY, DAILY_NEW, MAX, MAX_NEW, core_rules, event_rules

VERSION = "2.2.0"
NAME = "Angel-Temple-Vow-Protection"


def replace_checked(text, old, new, expected, label):
    actual = text.count(old)
    if actual != expected:
        raise ValueError(f"{label}: expected {expected} matches, found {actual}")
    return text.replace(old, new)


def load_export(path):
    with zipfile.ZipFile(path) as z:
        passages = {n[8:-5]: z.read(n).decode("utf-8-sig") for n in z.namelist()
                    if n.startswith("passage/") and n.endswith(".twee")}
        scripts = {}
        for n in z.namelist():
            if n.startswith("js/") and n.endswith(".js"):
                name = n.rsplit("/", 1)[-1]
                if name in scripts:
                    raise ValueError(f"Ambiguous JavaScript basename: {name}")
                scripts[name] = z.read(n).decode("utf-8-sig")
        manifest_path = f"ExportLoadedModScript/{NAME}/boot.json"
        legacy = json.loads(z.read(manifest_path)) if manifest_path in z.namelist() else None
        log = z.read("ModLoaderLog.txt").decode("utf-8-sig") if "ModLoaderLog.txt" in z.namelist() else ""
    return passages, scripts, legacy, log


def undo_legacy(passages, scripts, manifest, log):
    """Undo only this mod's known successful edits, retaining all other mods.

    This is an in-memory build reference, not an uninstall or save migration.
    The input may already contain the partially applied 2.1.0 package.
    """
    if manifest is None:
        return 0
    if manifest.get("version") not in {"1.0.0", "2.0.0", "2.1.0"}:
        raise ValueError("Use an export without this mod, or a supported legacy version (1.x/2.0/2.1)")
    undone = 0
    for addon in reversed(manifest.get("addonPlugin", [])):
        if addon["modName"] == "TweeReplacer":
            for p in reversed(addon["params"]):
                name, old, new = p["passage"], p["findString"], p["replace"]
                text = passages[name]
                count = text.count(new)
                failure = f"findString:[{old}] in:[{name}]" in log
                if failure:
                    if count:
                        raise ValueError(f"Conflicting legacy failure and replacement: {name}")
                    continue
                if not count or (count != 1 and not p.get("all")):
                    raise ValueError(f"Cannot safely reconstruct legacy patch: {name}")
                passages[name] = text.replace(new, old)
                undone += 1
        elif addon["modName"] == "ReplacePatcher":
            for p in reversed(addon["params"].get("js", [])):
                name = p["fileName"]
                scripts[name] = replace_checked(scripts[name], p["to"], p["from"], 1, f"legacy {name}")
                undone += 1
    return undone


def build(export, out_dir=None):
    passages, scripts, legacy, log = load_export(export)
    undone = undo_legacy(passages, scripts, legacy, log)
    baseline = {"passages": deepcopy(passages), "scripts": deepcopy(scripts)}
    checks, twee = [], []
    for name, old, new, expected in core_rules() + event_rules():
        passages[name] = replace_checked(passages[name], old, new, expected, name)
        twee.append({"passage": name, "findString": old, "replace": new, "all": expected > 1})
        checks.append({"kind": "twee", "target": name, "matches": expected})
    js = []
    for name, old, new in [("time.js", DAILY, DAILY_NEW), ("stat-changes.js", MAX, MAX_NEW)]:
        scripts[name] = replace_checked(scripts[name], old, new, 1, name)
        js.append({"fileName": name, "from": old, "to": new})
        checks.append({"kind": "js", "target": name, "matches": 1})
    # Exact records must remain in all paths, not be forged for eligibility.
    combat = passages["Widgets Combat"]
    if '<<set $player.virginity[_args[1]] to false>>' not in combat:
        raise ValueError("Real virginity recording unexpectedly missing")
    boot = {
        "name": NAME, "version": VERSION,
        "nickName": {"cn": "贞洁待遇与天使誓约保护", "en": "Virginity Benefits & Angel Vow Protection"},
        "alias": [], "styleFileList": [], "scriptFileList": ["scripts/runtime.js"],
        "tweeFileList": [], "imgFileList": [], "additionFile": ["README.txt", "patch-validation.json"],
        "addonPlugin": [
            {"modName": "TweeReplacer", "addonName": "TweeReplacerAddon", "modVersion": ">=1.7.0", "params": twee},
            {"modName": "ReplacePatcher", "addonName": "ReplacePatcherAddon", "modVersion": ">=1.3.0", "params": {"js": js}},
        ],
        "dependenceInfo": [
            {"modName": name, "version": version} for name, version in [
                ("ModLoader", ">=2.60.1"), ("GameVersion", "=0.5.12.13"),
                ("TweeReplacer", ">=1.7.0"), ("ReplacePatcher", ">=1.3.0"),
                ("maplebirch", "=5.6.2"), ("deadwood-reblooms", "=2.5.8"),
                ("revelation-the-book-of-return", "=1.4.6"),
            ]
        ],
    }
    report = {
        "version": VERSION, "sourceSha256": hashlib.sha256(Path(export).read_bytes()).hexdigest(),
        "legacyVersion": legacy.get("version") if legacy else None, "legacyEditsReconstructed": undone,
        "tweeRules": len(twee), "jsRules": len(js), "checks": checks,
        "scope": "Static reconstruction and patch validation only; not live-game verification.",
    }
    out = Path(out_dir) if out_dir else ROOT / "dist"
    out.mkdir(parents=True, exist_ok=True)
    package = out / f"{NAME}-{VERSION}.mod.zip"
    with zipfile.ZipFile(package, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("boot.json", json.dumps(boot, ensure_ascii=False, indent=2))
        z.writestr("patch-validation.json", json.dumps(report, ensure_ascii=False, indent=2))
        z.write(ROOT / "src/runtime.js", "scripts/runtime.js")
        z.write(ROOT / "README.md", "README.txt")
    with zipfile.ZipFile(package) as z:
        if z.testzip() is not None:
            raise ValueError("Invalid ZIP")
    return package, report, baseline, {"passages": passages, "scripts": scripts}, boot


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    package, report, _, _, _ = build(args.export, args.out_dir)
    print(json.dumps({"package": str(package), **report}, ensure_ascii=True, indent=2))
