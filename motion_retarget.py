"""Rest-calibrated FK retargeting through common human joint semantics.

Preview is a separate sampled Action. No source or target rig is rebuilt, and
no original constraint is deleted. Cancel restores the prior Action and pose.
"""
import json
import math

import bpy
from mathutils import Matrix, Vector

from . import humanoid

STATE_KEY = "kimodo_retarget_state"


def rest_world(armature, name):
    return armature.matrix_world @ armature.data.bones[name].matrix_local


def human_basis(armature, roles):
    point = lambda role: rest_world(armature, roles[role]).translation
    # Anatomical rest-pose lean must never tilt the locomotion ground plane.
    # MMD lower-body pivots and SOMA pelvis joints differ by several degrees.
    up = Vector((0, 0, 1))
    right = point("upper_arm_r") - point("upper_arm_l")
    right.z = 0
    right.normalize()
    forward = up.cross(right).normalized()
    if min(right.length, forward.length) < 0.9 or point("head").z <= point("pelvis").z:
        raise ValueError("无法从角色的肩部、骨盆与头部建立人形方向，请检查参考姿态")
    return Matrix((right, forward, up)).transposed()


def leg_length(armature, roles):
    points = [rest_world(armature, roles[role]).translation for role in ("thigh_l", "shin_l", "foot_l")]
    length = (points[0] - points[1]).length + (points[1] - points[2]).length
    if length < 1e-6:
        raise ValueError("腿长为零，无法换算动作位移")
    return length


def action_curves(action):
    if hasattr(action, "layers") and action.layers:
        return [curve for layer in action.layers for strip in layer.strips
                for bag in getattr(strip, "channelbags", ()) for curve in bag.fcurves]
    return list(getattr(action, "fcurves", ()))


def _capture(target, controlled):
    animation = target.animation_data_create()
    if animation.nla_tracks and any(not track.mute for track in animation.nla_tracks):
        raise ValueError("目标存在启用的 NLA 轨道，请先停用轨道后重定向")
    ik_controllers = {c.subtarget for bone in target.pose.bones for c in bone.constraints
                      if c.type == "IK" and c.target == target}
    return {"previous_action": animation.action.name if animation.action else "",
            "previous_fake_user": animation.action.use_fake_user if animation.action else False,
            "slot": animation.action_slot.identifier if getattr(animation, "action_slot", None) else "",
            "pose": {name: {"mode": target.pose.bones[name].rotation_mode,
                             "matrix": [list(row) for row in target.pose.bones[name].matrix_basis]}
                     for name in controlled},
            "ik": {p.name: bool(p.mmd_ik_toggle) for p in target.pose.bones
                   if p.name in ik_controllers and hasattr(p, "mmd_ik_toggle")}}


def _restore(target, state):
    previous = state["previous_action"]
    action = bpy.data.actions.get(previous) if previous else None
    if previous and action is None:
        raise RuntimeError("原动作已被删除，无法自动恢复：" + previous)
    target.animation_data_create().action = action
    if action:
        action.use_fake_user = state.get("previous_fake_user", False)
    if action and state.get("slot") and hasattr(action, "slots"):
        slot = next((s for s in action.slots if s.identifier == state["slot"]), None)
        if slot:
            target.animation_data.action_slot = slot
    for name, pose in state["pose"].items():
        bone = target.pose.bones.get(name)
        if bone:
            bone.rotation_mode = pose["mode"]
            bone.matrix_basis = Matrix(pose["matrix"])
    for name, enabled in state["ik"].items():
        target.pose.bones[name].mmd_ik_toggle = enabled
    bpy.context.view_layer.update()


def cancel(target):
    if not target.get(STATE_KEY):
        raise ValueError("当前角色没有可恢复的重定向记录")
    state = json.loads(target[STATE_KEY])
    preview = bpy.data.actions.get(state.get("preview_action", ""))
    _restore(target, state)
    del target[STATE_KEY]
    if preview and preview.get("kimodo_preview") and preview.users == 0:
        bpy.data.actions.remove(preview)


def commit(target, name=""):
    if not target.get(STATE_KEY):
        raise ValueError("请先生成重定向预览")
    state = json.loads(target[STATE_KEY])
    action = target.animation_data.action
    if action is None or action.name != state["preview_action"]:
        raise ValueError("当前动作已改变，请重新生成重定向预览")
    action.name = name.strip() or "Kimodo_" + target.name
    action["kimodo_preview"] = False
    action.use_fake_user = True
    state["preview_action"] = action.name
    state["committed"] = True
    target[STATE_KEY] = json.dumps(state, ensure_ascii=False)
    return action


def preview(source, target, start, end, pairs=None, root_mode="TRAVEL", foot_contact=True, ground_height=0.0):
    if source is None or target is None or source == target:
        raise ValueError("请分别指定动作源骨架与目标角色骨架")
    if source.type != "ARMATURE" or target.type != "ARMATURE":
        raise ValueError("动作源与目标必须是骨架对象")
    if not source.animation_data or not source.animation_data.action:
        raise ValueError("动作源骨架没有动画")
    if target.library or target.data.library:
        raise ValueError("目标为链接数据，请先建立本地覆盖或本地副本")
    if start > end:
        raise ValueError("结束帧必须不小于开始帧")
    if target.get(STATE_KEY):
        cancel(target)
    src_roles, dst_roles = humanoid.identify(source), humanoid.identify(target)
    if pairs:
        by_source = {src: dst for src, dst in pairs}
        dst_roles.update({role: by_source[name] for role, name in src_roles.items() if name in by_source})
    for role, name in dst_roles.items():
        if name not in target.pose.bones:
            raise ValueError(f"目标的{humanoid.ROLES[role][0]}骨骼不存在：{name}")
    shared = [role for role in src_roles if role in dst_roles and (not pairs or src_roles[role] in by_source)]
    carrier = humanoid.root_carrier(target, dst_roles)
    controlled = set(dst_roles[role] for role in shared) | {carrier}
    state = _capture(target, controlled)
    scene, original_frame = bpy.context.scene, bpy.context.scene.frame_current
    alignment = human_basis(target, dst_roles) @ human_basis(source, src_roles).transposed()
    align_q = alignment.to_quaternion()
    scale = leg_length(target, dst_roles) / leg_length(source, src_roles)
    source_rest = {role: rest_world(source, src_roles[role]) for role in shared}
    target_rest = {role: rest_world(target, dst_roles[role]) for role in shared}
    references = {}
    for role in shared:
        rotation = target_rest[role].to_quaternion()
        child = humanoid.CHILD_ROLE.get(role)
        if child in shared:
            source_direction = alignment @ (source_rest[child].translation - source_rest[role].translation)
            target_direction = target_rest[child].translation - target_rest[role].translation
            if min(source_direction.length, target_direction.length) > 1e-6:
                rotation = target_direction.rotation_difference(source_direction) @ rotation
        references[role] = rotation
    carrier_rest = rest_world(target, carrier)
    samples = []
    # Sample the evaluated source before assigning anything to the target.
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
        samples.append({role: evaluated.matrix_world @ evaluated.pose.bones[src_roles[role]].matrix
                        for role in shared})
    first = samples[0]["pelvis"].translation
    source_base = source_rest["pelvis"].translation.copy()
    source_base.x, source_base.y = first.x, first.y
    ordered = sorted(shared, key=lambda role: len(target.data.bones[dst_roles[role]].parent_recursive))
    action = bpy.data.actions.new("Kimodo_预览_" + target.name)
    action["kimodo_preview"] = True
    action["kimodo_source_action"] = source.animation_data.action.name
    action["kimodo_root_mode"] = root_mode
    max_rotation_error = 0.0
    previous_quaternions = {}
    try:
        if target.animation_data.action:
            target.animation_data.action.use_fake_user = True
        target.animation_data.action = action
        for name in controlled:
            target.pose.bones[name].rotation_mode = "QUATERNION"
            target.pose.bones[name].matrix_basis = Matrix.Identity(4)
        for name in state["ik"]:
            target.pose.bones[name].mmd_ik_toggle = False
        for offset, sample in enumerate(samples):
            frame = start + offset
            scene.frame_set(frame)
            displacement = alignment @ (sample["pelvis"].translation - source_base) * scale
            if root_mode == "IN_PLACE":
                displacement.x = displacement.y = 0.0
            carrier_bone = target.pose.bones[carrier]
            carrier_matrix = carrier_rest.copy()
            carrier_matrix.translation += displacement
            carrier_bone.matrix = target.matrix_world.inverted() @ carrier_matrix
            carrier_bone.keyframe_insert("location", frame=frame, group="角色位移")
            bpy.context.view_layer.update()
            for role in ordered:
                bone = target.pose.bones[dst_roles[role]]
                delta = sample[role].to_quaternion() @ source_rest[role].to_quaternion().inverted()
                desired = align_q @ delta @ align_q.inverted() @ references[role]
                desired.normalize()
                world = target.matrix_world @ bone.matrix
                matrix = Matrix.LocRotScale(world.translation, desired, world.to_scale())
                bone.matrix = target.matrix_world.inverted() @ matrix
                if bone.name != carrier:
                    bone.location = (0.0, 0.0, 0.0)
                if bone.name in previous_quaternions:
                    bone.rotation_quaternion.make_compatible(previous_quaternions[bone.name])
                previous_quaternions[bone.name] = bone.rotation_quaternion.copy()
                bpy.context.view_layer.update()
                actual = (target.matrix_world @ bone.matrix).to_quaternion()
                error = actual.rotation_difference(desired).angle
                error = min(error, abs(2 * math.pi - error))
                max_rotation_error = max(max_rotation_error, error)
                bone.keyframe_insert("rotation_quaternion", frame=frame, group=humanoid.ROLES[role][0])
            for name in state["ik"]:
                target.pose.bones[name].mmd_ik_toggle = False
                target.pose.bones[name].keyframe_insert("mmd_ik_toggle", frame=frame, group="腿部 FK 控制")
        contact_state = None
        if foot_contact:
            from . import foot_contact as contact_solver
            contact_state = contact_solver.correct(target, src_roles, dst_roles, shared, samples, source_rest,
                target_rest, alignment, scale, carrier, start, root_mode, ground_height)
        for curve in action_curves(action):
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"
        state.update(preview_action=action.name, scale=scale, frames=end-start+1,
                     rotation_error_radians=max_rotation_error, rotation_error_scope="FK-before-contact",
                     foot_contact=contact_state, committed=False)
        target[STATE_KEY] = json.dumps(state, ensure_ascii=False)
        scene.frame_set(start)
        return state
    except Exception:
        _restore(target, state)
        if action.users == 0:
            bpy.data.actions.remove(action)
        scene.frame_set(original_frame)
        raise
