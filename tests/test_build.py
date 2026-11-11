from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "tools/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
from patches import DAILY, DAILY_NEW, MAX, MAX_NEW, core_rules, event_rules


def synthetic_export(path):
    """Minimal rule fragments, not copies of third-party game files."""
    parts = defaultdict(list)
    for name, old, _, expected in core_rules() + event_rules():
        parts[name].extend([old] * expected)
    parts["Widgets Combat"].append('<<set $player.virginity[_args[1]] to false>>')
    with zipfile.ZipFile(path, "w") as z:
        for name, snippets in parts.items():
            z.writestr(f"passage/{name}.twee", "\n".join(snippets))
        z.writestr("js/time.js", DAILY)
        z.writestr("js/stat-changes.js", MAX)


class BuildTests(unittest.TestCase):
    def test_match_count_errors_are_fatal(self):
        for content in ["missing", "target target"]:
            with self.assertRaises(ValueError):
                builder.replace_checked(content, "target", "new", 1, "test")

    def test_build_minimal_export_and_package_allowlist(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "export.zip"
            synthetic_export(source)
            before = source.read_bytes()
            package, report, baseline, patched, boot = builder.build(source, Path(tmp) / "out")
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(report["tweeRules"], 25)
            self.assertEqual(report["jsRules"], 2)
            self.assertEqual(len(event_rules()), 19)
            with zipfile.ZipFile(package) as z:
                self.assertEqual(set(z.namelist()), {"boot.json", "scripts/runtime.js", "README.txt", "patch-validation.json"})
            self.assertNotIn("angelTempleVowProtection", json.dumps(boot))
            self.assertNotEqual(baseline, patched)

    def test_legacy_success_and_failure_reconstruction(self):
        p = {"A": "new", "B": "extended original"}
        manifest = {"version": "2.1.0", "addonPlugin": [{"modName": "TweeReplacer", "params": [
            {"passage": "A", "findString": "old", "replace": "new"},
            {"passage": "B", "findString": "original", "replace": "replacement"},
        ]}]}
        self.assertEqual(builder.undo_legacy(p, {}, manifest, "findString:[original] in:[B]"), 1)
        self.assertEqual(p, {"A": "old", "B": "extended original"})
        with self.assertRaises(ValueError):
            builder.undo_legacy({"A": "unknown", "B": "replacement"}, {}, manifest, "")

    def test_condition_semantics(self):
        result = subprocess.run(["node", str(ROOT / "tests/conditions.cjs")], input=json.dumps({
            "events": event_rules(), "core": core_rules(), "daily": DAILY_NEW, "max": MAX_NEW,
        }), text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_unscoped_global_virginity_patches(self):
        for name, old, new, expected in core_rules() + event_rules():
            self.assertGreater(len(old), 20)
            self.assertNotIn('<<set $player.virginity.vaginal', new)
            self.assertNotIn('<<set $player.virginity.penile', new)
            self.assertNotIn("dynamic.trigger", old)

    @unittest.skipUnless(os.environ.get("DOL_EXPORT"), "set DOL_EXPORT for private local integration")
    def test_real_export_integration(self):
        source = Path(os.environ["DOL_EXPORT"])
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            _, report, baseline, patched, boot = builder.build(source, tmp)
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(report["tweeRules"], 25)
            self.assertEqual(report["jsRules"], 2)
            combat_before = baseline["passages"]["Widgets Combat"]
            combat_after = patched["passages"]["Widgets Combat"]
            # Every actual history write is retained exactly, including NPC records.
            writes = r'<<set \$player\.virginity[^>]*>>'
            self.assertEqual(re.findall(writes, combat_before), re.findall(writes, combat_after))
            self.assertIn('<<case "anal">><<purity -25>>', combat_after)
            self.assertIn('<<case "kiss">><<purity -10>>', combat_after)
            self.assertIn('RobinTemple', combat_after)
            self.assertIn('VanillaPlus', patched["passages"]["Transformation Widgets"])
            # Wrapping the fallen macro adds exactly one balanced if pair.
            name = "Transformation Widgets"
            for tag in [r'<<if\b', r'<</if>>']:
                self.assertEqual(len(re.findall(tag, patched["passages"][name])),
                                 len(re.findall(tag, baseline["passages"][name])) + 1)
            for name in ["time.js", "stat-changes.js"]:
                file = Path(tmp) / name
                file.write_text(patched["scripts"][name], encoding="utf-8")
                result = subprocess.run(["node", "--check", str(file)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            # No dynamic-anchor initialization or saved eligibility remains.
            self.assertNotIn("$angelTempleVowProtection", json.dumps(boot))


if __name__ == "__main__":
    unittest.main()
