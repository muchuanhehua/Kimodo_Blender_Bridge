"""Measure actual skinned feet, planted-frame drift and restoration on saved rigs."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import addon_utils
import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_blender import constraints, load_addon


def samples_for(target, roles, start, end):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.find_armature() == target
              and getattr(obj, "mmd_type", "NONE") not in {"RIGID_BODY", "JOINT"} and not obj.hide_render]
    rows = []
    for frame in range(start, end+1):
        bpy.context.scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        rig = target.evaluated_get(depsgraph)
        joints = {role: list((rig.matrix_world @ rig.pose.bones[name].matrix).translation) for role, name in roles.items()}
        minimum = float("inf")
        for mesh in meshes:
            evaluated = mesh.evaluated_get(depsgraph)
            data = evaluated.to_mesh()
            try:
                points = np.empty(len(data.vertices)*3, dtype=np.float32)
                data.vertices.foreach_get("co", points)
                matrix = np.array(evaluated.matrix_world, dtype=np.float64)
                heights = points.reshape(-1, 3) @ matrix[2, :3] + matrix[2, 3]
                minimum = min(minimum, float(heights.min()))
            finally:
                evaluated.to_mesh_clear()
        rows.append({"frame": frame, "joints": joints, "mesh_min_z": minimum})
    return rows


def drift(rows, spans, start):
    result = {}
    for side, intervals in spans.items():
        maximum = 0.0
        for begin, end in intervals:
            points = [np.array(rows[frame-start]["joints"]["foot_"+side][:2]) for frame in range(begin+1, end)]
            if points:
                maximum = max(maximum, max(float(np.linalg.norm(point-points[0])) for point in points))
        result[side] = maximum
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--save-blend", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    root = Path(__file__).resolve().parents[1]
    addon_utils.enable("bl_ext.blender_org.mmd_tools", default_set=False)
    load_addon(root)
    from kimodo_dev import humanoid, motion_retarget, pmx_adapter
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve()))
    scene = bpy.context.scene
    source = next(obj for obj in scene.objects if obj.type == "ARMATURE" and obj.get("kimodo_source"))
    targets = sorted((obj for obj in scene.objects if obj.type == "ARMATURE" and obj.get(pmx_adapter.PREPARED_KEY)),
                     key=lambda obj: obj.matrix_world.translation.x)
    assert len(targets) == 3
    visibility = {obj.name: obj.hide_viewport for obj in scene.objects}
    report = {"blender": bpy.app.version_string, "source_kind": "kimodo_bvh", "models": [],
              "core_sha256": {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                              for name in ("humanoid.py", "motion_retarget.py", "pmx_adapter.py", "foot_contact.py")}}
    source_roles = humanoid.identify(source)
    source_before = samples_for(source, source_roles, 1, 73)
    for target in targets:
        for other in targets:
            model = pmx_adapter.model_root(other)
            for obj in [model, *model.children_recursive]:
                obj.hide_viewport = visibility[obj.name] if other == target else True
        started = time.monotonic()
        roles = humanoid.identify(target)
        old_action = target.animation_data.action
        old_action.use_fake_user = True
        original_constraints = constraints(target)
        parents = {bone.name: bone.parent.name if bone.parent else None for bone in target.data.bones}
        print("GROUND_VERIFY_BEGIN", target.name, flush=True)
        before = samples_for(target, roles, 1, 73)
        # A short real-source transaction checks cancel independently of the final Action.
        short = motion_retarget.preview(source, target, 1, 8)
        previous = json.loads(target[motion_retarget.STATE_KEY])["previous_action"]
        motion_retarget.cancel(target)
        assert (target.animation_data.action.name if target.animation_data.action else "") == previous
        assert constraints(target) == original_constraints
        assert {bone.name: bone.parent.name if bone.parent else None for bone in target.data.bones} == parents
        state = motion_retarget.preview(source, target, 1, 73)
        action = motion_retarget.commit(target, "Kimodo_贴地修复_" + target.name)
        after = samples_for(target, roles, 1, 73)
        spans = state["foot_contact"]["contact_spans"]
        before_drift, after_drift = drift(before, spans, 1), drift(after, spans, 1)
        old_rise = before[-1]["joints"]["pelvis"][2]-before[0]["joints"]["pelvis"][2]
        new_rise = after[-1]["joints"]["pelvis"][2]-after[0]["joints"]["pelvis"][2]
        assert state["foot_contact"]["max_contact_height_error"] < .003, state["foot_contact"]
        assert max(after_drift.values()) < .002, after_drift
        assert min(row["mesh_min_z"] for row in after) > -.003
        assert abs(new_rise) < .10
        assert constraints(target) == original_constraints
        assert old_action.name in bpy.data.actions
        result = {"model": target.name, "action": action.name, "frames": 73,
                  "before_pelvis_vertical_travel": old_rise, "after_pelvis_vertical_travel": new_rise,
                  "before_max_stance_ankle_drift": before_drift, "after_max_stance_ankle_drift": after_drift,
                  "after_mesh_min_z": min(row["mesh_min_z"] for row in after),
                  "contact": state["foot_contact"], "preserved_constraints": sum(len(value) for value in original_constraints.values()),
                  "cancel_restores_action": True, "original_action_preserved": True, "hierarchy_preserved": True,
                  "seconds": round(time.monotonic()-started, 2)}
        report["models"].append(result)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        (args.output.parent / (target.name+"-trajectories.json")).write_text(
            json.dumps({"before": before, "after": after}, ensure_ascii=False), encoding="utf-8")
        print("GROUND_VERIFY_PASS", json.dumps(result, ensure_ascii=False), flush=True)
    for obj in scene.objects:
        obj.hide_viewport = visibility[obj.name]
    source_after = samples_for(source, source_roles, 1, 73)
    assert source_before == source_after, "Source motion was modified"
    report["source_motion_preserved"] = True
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    scene.frame_start, scene.frame_end = 1, 73
    scene.frame_set(37)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()))
    print("GROUND_VERIFY_COMPLETE", args.output, flush=True)


if __name__ == "__main__":
    main()
