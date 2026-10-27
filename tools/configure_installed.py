"""Configure or verify the released extension in the user's Blender preferences."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tomllib

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--system-python", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--update", action="store_true", help="Sync and update only the Kimodo repository package")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    module_name = "bl_ext.kimodo.kimodo_blender_bridge"
    repo_index, repo = next((index, repo) for index, repo in enumerate(bpy.context.preferences.extensions.repos)
                           if repo.module == "kimodo")
    expected_url = "https://raw.githubusercontent.com/muchuanhehua/Kimodo_Blender_Bridge/main/release/index.json"
    if repo.remote_url != expected_url or not repo.enabled:
        raise RuntimeError("Kimodo remote extension repository is not configured")
    if args.update:
        if bpy.ops.extensions.repo_sync(repo_index=repo_index) != {"FINISHED"}:
            raise RuntimeError("Kimodo repository synchronization did not finish")
        if bpy.ops.extensions.package_install(repo_index=repo_index, pkg_id="kimodo_blender_bridge",
                                              enable_on_install=True) != {"FINISHED"}:
            raise RuntimeError("Kimodo repository update did not finish")
    if module_name not in bpy.context.preferences.addons:
        raise RuntimeError("Released Kimodo extension is not enabled")
    addon = importlib.import_module(module_name)
    root = Path(__file__).resolve().parents[1]
    installed = Path(addon.__file__).resolve().parent
    manifest = tomllib.loads((installed / "blender_manifest.toml").read_text(encoding="utf-8"))
    build = json.loads((root / f"release/build-v{manifest['version']}.json").read_text(encoding="utf-8"))
    for name, expected in build["payload"].items():
        actual = hashlib.sha256((installed / name).read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError("Installed payload differs from release: " + name)
    runtime = args.runtime.resolve()
    python = runtime / "Scripts/python.exe"
    if not python.is_file() or not args.system_python.is_file():
        raise RuntimeError("Configured Python executable does not exist")
    if not (runtime / ".kimodo_install_complete").is_file():
        raise RuntimeError("Kimodo runtime installation is incomplete")
    prefs = bpy.context.preferences.addons[module_name].preferences
    if args.check_only:
        if Path(prefs.install_location).resolve() != runtime:
            raise RuntimeError("Runtime preference was not persisted")
        if Path(prefs.system_python_override).resolve() != args.system_python.resolve():
            raise RuntimeError("System Python preference was not persisted")
    else:
        prefs.install_location = str(runtime)
        prefs.system_python_override = str(args.system_python.resolve())
    addon.properties._reset_transient_generation_state()
    settings = bpy.context.scene.kimodo
    if Path(settings.python_executable).resolve() != python:
        raise RuntimeError("Fresh scene did not resolve the configured Kimodo runtime")
    if not args.check_only:
        settings.use_offload = False
        bpy.ops.wm.save_userpref()
    report = {
        "blender": bpy.app.version_string,
        "module": module_name,
        "version": manifest["version"],
        "directory": str(installed),
        "repository": repo.remote_url,
        "runtime": str(runtime),
        "python": settings.python_executable,
        "payload_files_verified": len(build["payload"]),
        "fresh_process_preferences_verified": args.check_only,
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("INSTALLED_RELEASE_VERIFIED", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
