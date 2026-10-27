"""Temporary GUI check using the existing local Blender MCP addon."""
import json
from pathlib import Path
import sys

import addon_utils
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_blender import load_addon

root = Path(__file__).resolve().parents[1]


def snapshot():
    output = root / ".verification/chinese-ui.png"
    with bpy.context.temp_override(window=bpy.context.window_manager.windows[0]):
        bpy.ops.screen.screenshot(filepath=str(output))
    print("KIMODO_UI_SCREENSHOT", output, flush=True)
    return None


def setup():
    addon_utils.enable("bl_ext.blender_org.mmd_tools", default_set=False)
    load_addon(root)
    bpy.ops.wm.open_mainfile(filepath=str(root / ".verification/pmx-kimodo-wave.blend"))
    settings = bpy.context.scene.kimodo
    settings.python_executable = str(root / ".runtime/kimodo-venv/Scripts/python.exe")
    settings.use_offload = False
    for obj in bpy.context.scene.objects:
        if obj.type in {"ARMATURE", "EMPTY", "LIGHT", "CAMERA"}:
            obj.hide_set(True)
    window = bpy.context.window_manager.windows[0]
    for area in window.screen.areas:
        if area.type == "VIEW_3D":
            with bpy.context.temp_override(window=window, area=area):
                space = area.spaces.active
                space.show_region_ui = True
                space.overlay.show_overlays = False
                space.region_3d.view_distance = 6.5
                space.region_3d.view_location = Vector((2, 0, 0.9))
    with bpy.context.temp_override(window=window):
        addon_utils.enable("addon", default_set=False)
        if not getattr(bpy.types, "blendermcp_server", None):
            bpy.ops.blendermcp.start_server()
    view = next(area for area in window.screen.areas if area.type == "VIEW_3D")
    with bpy.context.temp_override(window=window, area=view):
        bpy.ops.wm.call_panel(name="KIMODO_PT_Generate", keep_open=True)
    (root / ".verification/gui-probe.json").write_text(json.dumps({"blender": bpy.app.version_string,
        "filepath": bpy.data.filepath, "module": "kimodo_dev", "mcp": bool(getattr(bpy.types, "blendermcp_server", None))}), encoding="utf-8")
    bpy.app.timers.register(snapshot, first_interval=3.0)
    return None


bpy.app.timers.register(setup, first_interval=1.0)
