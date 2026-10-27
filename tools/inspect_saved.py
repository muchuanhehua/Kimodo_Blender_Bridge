"""Verify saved retargeted poses after reopening and render private evidence."""
import argparse
import json
from pathlib import Path
import sys

import addon_utils
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_blender import load_addon


def pose_samples():
    from kimodo_dev import humanoid, pmx_adapter
    result = {}
    for obj in bpy.data.objects:
        if obj.type != "ARMATURE" or not obj.get(pmx_adapter.PREPARED_KEY):
            continue
        roles = humanoid.identify(obj)
        action = obj.animation_data.action if obj.animation_data else None
        if action is None:
            raise RuntimeError("Saved target has no Action: " + obj.name)
        start, end = action.frame_range
        for frame in sorted({round(start), round((start+end)/2), round(end)}):
            bpy.context.scene.frame_set(frame)
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            for role in ("pelvis", "head", "hand_l", "hand_r", "foot_l", "foot_r"):
                matrix = evaluated.matrix_world @ evaluated.pose.bones[roles[role]].matrix
                result[f"{obj.name}/{frame}/{role}"] = [value for row in matrix for value in row]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    root = Path(__file__).resolve().parents[1]
    addon_utils.enable("bl_ext.blender_org.mmd_tools", default_set=False)
    addon = load_addon(root)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    first = pose_samples()
    # Re-save and reopen our private verification copy, retaining original assets.
    copy = args.output.parent / "roundtrip-verification.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(copy.resolve()))
    bpy.ops.wm.open_mainfile(filepath=str(copy.resolve()))
    second = pose_samples()
    if first.keys() != second.keys():
        raise RuntimeError("Saved pose identifiers changed after reopening")
    maximum = max(abs(value-other) for key, values in first.items() for value, other in zip(values, second[key]))
    if maximum > 1e-5:
        raise RuntimeError(f"Saved pose matrices changed: {maximum}")
    result = {"blender": bpy.app.version_string, "sample_matrices": len(first), "max_matrix_delta": maximum,
              "save_reopen_preserves_pose": True}
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SAVE_REOPEN_PASS", json.dumps(result), flush=True)
    if not args.image:
        return
    scene = bpy.context.scene
    scene.frame_set(37)
    # Use only imported character meshes; helper rigidbodies remain hidden.
    for obj in scene.objects:
        if obj.type == "MESH" and not obj.find_armature():
            obj.hide_render = True
        if obj.type in {"CAMERA", "LIGHT"}:
            obj.hide_render = True
        if obj.type == "MESH" and getattr(obj, "mmd_type", "NONE") in {"RIGID_BODY", "JOINT"}:
            obj.hide_render = True
    camera_data = bpy.data.cameras.new("Kimodo_Verification_Camera")
    camera = bpy.data.objects.new(camera_data.name, camera_data)
    scene.collection.objects.link(camera)
    camera.location = (2.2, -9.0, 2.0)
    point = Vector((2.0, 0.0, 0.9))
    camera.rotation_euler = (point-camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 7.1
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(args.image.resolve())
    shading = scene.display.shading
    shading.light = "STUDIO"
    shading.color_type = "TEXTURE"
    shading.show_shadows = True
    shading.show_cavity = True
    shading.cavity_type = "BOTH"
    shading.background_type = "WORLD"
    scene.world.color = (0.15, 0.15, 0.15)
    for material in bpy.data.materials:
        if material.use_nodes:
            texture = next((node for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image), None)
            if texture:
                material.node_tree.nodes.active = texture
    bpy.ops.render.render(write_still=True)
    print("EVIDENCE_RENDER", args.image, flush=True)


if __name__ == "__main__":
    main()
