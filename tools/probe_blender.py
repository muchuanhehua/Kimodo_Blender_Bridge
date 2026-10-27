"""Read the Blender environment before development and deployment."""
import json
import sys
from pathlib import Path

import bpy

root = Path(__file__).resolve().parents[1]
result = {
    "blender": bpy.app.version_string,
    "binary": bpy.app.binary_path,
    "python": sys.version,
    "file": bpy.data.filepath,
    "addons": list(bpy.context.preferences.addons.keys()),
    "repos": [
        {"name": repo.name, "module": repo.module, "directory": repo.directory,
         "remote_url": repo.remote_url}
        for repo in bpy.context.preferences.extensions.repos
    ],
    "operators": {},
}
for name in ("import_model", "fix_bone_issues", "fix_bone_order"):
    operator = getattr(bpy.ops.mmd_tools, name)
    try:
        result["operators"][name] = [p.identifier for p in operator.get_rna_type().properties]
    except RuntimeError as exc:
        result["operators"][name] = {"error": str(exc)}
output = root / ".verification/probe.json"
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("KIMODO_PROBE", json.dumps(result, ensure_ascii=False), flush=True)
