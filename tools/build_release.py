"""Build, validate and index a Blender extension with an explicit payload."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import tomllib
import zipfile


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blender", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = tomllib.loads((root / "blender_manifest.toml").read_text(encoding="utf-8"))
    metadata = ast.parse((root / "__init__.py").read_text(encoding="utf-8"))
    info = ast.literal_eval(next(n.value for n in metadata.body if isinstance(n, ast.Assign)
                                and any(isinstance(t, ast.Name) and t.id == "bl_info" for t in n.targets)))
    assert ".".join(map(str, info["version"])) == manifest["version"], "Version mismatch"
    python_files = {path.name for path in root.glob("*.py")}
    for name in python_files:
        ast.parse((root / name).read_text(encoding="utf-8"), filename=name)
    # Verify that the final retarget core matches the actual three-model test.
    evidence = json.loads((root / ".verification/three-models-kimodo-wave.json").read_text(encoding="utf-8"))
    assert len(evidence["models"]) == 3 and evidence["source_kind"] == "kimodo_bvh"
    for name, expected in evidence["core_sha256"].items():
        assert sha256((root / name).read_bytes()) == expected, f"Changed core needs verification: {name}"
    expected_payload = python_files | {"blender_manifest.toml", "README.md", "UPSTREAM.md", "CHANGELOG.md", "NOTICE", "LICENSE"}
    release = root / "release"
    release.mkdir(exist_ok=True)
    filename = f"{manifest['id']}-{manifest['version']}.zip"
    archive = release / filename
    command = [str(args.blender), "--background", "--factory-startup", "--command", "extension"]
    subprocess.run([*command, "build", "--source-dir", str(root), "--output-filepath", str(archive)], check=True)
    subprocess.run([*command, "validate", str(archive)], check=True)
    fingerprints = {}
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None, "ZIP CRC failed"
        actual = set(package.namelist())
        assert actual == expected_payload, f"Unexpected/missing payload: {actual ^ expected_payload}"
        for name in sorted(expected_payload):
            data = (root/name).read_bytes()
            assert package.read(name) == data, f"Packaged bytes differ: {name}"
            fingerprints[name] = sha256(data)
    digest = sha256(archive.read_bytes())
    item = {key: value for key, value in manifest.items() if key != "build"}
    item.update(archive_url=f"https://github.com/muchuanhehua/Kimodo_Blender_Bridge/releases/download/v{manifest['version']}/{filename}",
                archive_size=archive.stat().st_size, archive_hash="sha256:" + digest)
    (release / "index.json").write_text(json.dumps({"version": "v1", "blocklist": [], "data": [item]}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    record = {"version": manifest["version"], "archive": filename, "bytes": archive.stat().st_size,
              "sha256": digest, "payload": fingerprints, "verified_core": evidence["core_sha256"],
              "checks": ["python_syntax", "versions", "native_extension_build", "native_extension_validate",
                         "exact_payload", "zip_crc", "source_archive_bytes", "three_real_pmx_models"]}
    (release / f"build-v{manifest['version']}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    print("RELEASE_VERIFIED", filename, digest, len(fingerprints), flush=True)


if __name__ == "__main__":
    main()
