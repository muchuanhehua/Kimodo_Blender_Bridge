"""Exercise real PMX imports, repairs and retargeting in an isolated Blender.

Private fixtures and evidence are supplied by command-line arguments and are
never packaged. --synthetic checks solving before model downloads complete;
the final verification must pass a real Kimodo BVH using --bvh.
"""
import argparse
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import addon_utils
import bpy
from mathutils import Matrix, Quaternion, Vector


def load_addon(root):
    spec = importlib.util.spec_from_file_location("kimodo_dev", root / "__init__.py", submodule_search_locations=[str(root)])
    addon = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = addon
    spec.loader.exec_module(addon)
    addon.register()
    return addon


def synthetic_source(target, humanoid):
    roles = humanoid.identify(target)
    names = {role: aliases[1] if role == "pelvis" else next((alias for alias in aliases if alias.isascii()), aliases[0])
             for role, (_, aliases) in humanoid.ROLES.items()}
    positions = {role: (target.matrix_world @ target.data.bones[name].matrix_local).translation.copy() for role, name in roles.items()}
    parent_roles = {"spine": "pelvis", "spine_mid": "spine", "chest": "spine_mid", "neck": "chest", "head": "neck"}
    for side in ("l", "r"):
        parent_roles.update({f"shoulder_{side}": "chest", f"upper_arm_{side}": f"shoulder_{side}",
                             f"forearm_{side}": f"upper_arm_{side}", f"hand_{side}": f"forearm_{side}",
                             f"thigh_{side}": "pelvis", f"shin_{side}": f"thigh_{side}",
                             f"foot_{side}": f"shin_{side}", f"toe_{side}": f"foot_{side}"})
        arm_height = positions[f"upper_arm_{side}"].z
        for role in (f"forearm_{side}", f"hand_{side}"):
            positions[role].z = arm_height
    data = bpy.data.armatures.new("SyntheticSource")
    obj = bpy.data.objects.new("SyntheticSource", data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for role, position in positions.items():
        bone = data.edit_bones.new(names[role])
        bone.head = position
        child = humanoid.CHILD_ROLE.get(role)
        bone.tail = positions[child] if child in positions else position + Vector((0, 0, 0.08))
        if (bone.tail-bone.head).length < 0.001:
            bone.tail = bone.head + Vector((0, 0, 0.08))
    for role, parent in parent_roles.items():
        if role in roles and parent in roles:
            data.edit_bones[names[role]].parent = data.edit_bones[names[parent]]
    bpy.ops.object.mode_set(mode="OBJECT")
    for frame, angle in ((1, 0.0), (8, 0.45)):
        for bone in obj.pose.bones:
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = Quaternion((0, 1, 0), angle) if bone.name == names["upper_arm_r"] else Quaternion()
            bone.keyframe_insert("rotation_quaternion", frame=frame)
        pelvis = obj.pose.bones[names["pelvis"]]
        pelvis.location = (angle * 0.4, 0, -angle * 0.1)
        pelvis.keyframe_insert("location", frame=frame)
    return obj


def constraints(armature):
    return {bone.name: [(c.name, c.type, c.target.name if hasattr(c, "target") and c.target else "")
                        for c in bone.constraints] for bone in armature.pose.bones}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", type=Path, nargs="+", required=True)
    parser.add_argument("--bvh", type=Path)
    parser.add_argument("--synthetic", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--save-blend", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    if not args.bvh and not args.synthetic:
        raise ValueError("Supply --bvh or explicitly request --synthetic")
    root = Path(__file__).resolve().parents[1]
    addon_utils.enable("bl_ext.blender_org.mmd_tools", default_set=False)
    addon_utils.enable("io_anim_bvh", default_set=False)
    addon = load_addon(root)
    from kimodo_dev import humanoid, motion_retarget, pmx_adapter, workflow
    report = {"blender": bpy.app.version_string, "source_kind": "synthetic" if args.synthetic else "kimodo_bvh", "models": []}
    report["core_sha256"] = {name: hashlib.sha256((root/name).read_bytes()).hexdigest()
                             for name in ("humanoid.py", "motion_retarget.py", "pmx_adapter.py")}
    scene = bpy.context.scene
    scene.render.fps = 30 if args.synthetic else 24
    source = None
    hidden = []
    for index, path in enumerate(args.models):
        started = time.monotonic()
        print("VERIFY_IMPORT", path.name, flush=True)
        result = bpy.ops.kimodo.import_pmx(filepath=str(path.resolve()))
        assert result == {"FINISHED"}, result
        target = scene.kimodo.target_armature
        prepare = json.loads(target[pmx_adapter.PREPARED_KEY])
        parents_before = {b.name: b.parent.name if b.parent else None for b in target.data.bones}
        names_before = {b.name: b.mmd_bone.name_j for b in target.pose.bones if not getattr(b, "is_mmd_shadow_bone", False)}
        pmx_adapter.prepare(target)
        assert names_before == {b.name: b.mmd_bone.name_j for b in target.pose.bones if not getattr(b, "is_mmd_shadow_bone", False)}, "Preparation is not idempotent"
        assert not pmx_adapter.name_issues(target)
        if source is None:
            if args.synthetic:
                source = synthetic_source(target, humanoid)
            else:
                assert bpy.ops.kimodo.import_bvh(filepath=str(args.bvh.resolve())) == {"FINISHED"}
                source = scene.kimodo.source_armature
        scene.kimodo.source_armature, scene.kimodo.target_armature = source, target
        pairs = workflow.populate_mapping(scene.kimodo)
        frame_start, frame_end = scene.kimodo.bake_start_frame, scene.kimodo.bake_end_frame
        original_constraints = constraints(target)
        # A real existing Action must survive both successful preview and cancel.
        target.animation_data_create()
        bone = target.pose.bones[humanoid.identify(target)["head"]]
        bone.keyframe_insert("rotation_quaternion", frame=frame_start)
        previous = target.animation_data.action
        previous.name = "Existing_" + path.stem
        previous.use_fake_user = True
        print("VERIFY_PREVIEW", path.name, len(pairs), frame_start, frame_end, flush=True)
        settings = scene.kimodo
        assert bpy.ops.kimodo.apply_retargeting() == {"FINISHED"}
        state = json.loads(target[motion_retarget.STATE_KEY])
        assert constraints(target) == original_constraints, "Original constraints were removed or rebuilt"
        preview = target.animation_data.action
        assert preview != previous and previous.name in bpy.data.actions
        assert motion_retarget.action_curves(preview), "No animation curves written"
        assert state["rotation_error_radians"] < math.radians(5), state["rotation_error_radians"]
        assert bpy.ops.kimodo.remove_retargeting() == {"FINISHED"}
        assert target.animation_data.action == previous, "Cancel did not restore previous Action"
        assert constraints(target) == original_constraints
        assert bpy.ops.kimodo.apply_retargeting() == {"FINISHED"}
        settings.retarget_action_name = "Kimodo_" + path.stem
        assert bpy.ops.kimodo.bake_retargeting() == {"FINISHED"}
        action = target.animation_data.action
        assert action.get("kimodo_preview") is False
        assert action.name != previous.name and previous.name in bpy.data.actions
        assert parents_before == {b.name: b.parent.name if b.parent else None for b in target.data.bones}
        assert constraints(target) == original_constraints
        for frame in sorted({frame_start, (frame_start+frame_end)//2, frame_end}):
            scene.frame_set(frame)
            for p in target.pose.bones:
                assert all(math.isfinite(value) for row in p.matrix for value in row), p.name
        report["models"].append({"model": path.stem, "bones": prepare["bone_count"],
            "fixed_names": len(prepare["name_changes"]), "mapped_joints": len(pairs),
            "frames": state["frames"], "rotation_error_degrees": math.degrees(state["rotation_error_radians"]),
            "preserved_constraints": sum(len(v) for v in original_constraints.values()),
            "previous_action_preserved": True, "cancel_restores_action": True,
            "repeat_preparation_stable": True, "action": action.name,
            "seconds": round(time.monotonic()-started, 2)})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        pmx_adapter.model_root(target).location.x += index * 2.0
        bpy.context.view_layer.update()
        print("VERIFY_MODEL_PASS", json.dumps(report["models"][-1], ensure_ascii=False), flush=True)
        # Already-verified characters need not be evaluated while solving another.
        for obj in [pmx_adapter.model_root(target), *pmx_adapter.model_root(target).children_recursive]:
            hidden.append((obj, obj.hide_viewport))
            obj.hide_viewport = True
    for obj, value in hidden:
        obj.hide_viewport = value
    if args.save_blend:
        scene.frame_set((frame_start+frame_end)//2)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()))
    print("KIMODO_VERIFICATION_PASS", json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
