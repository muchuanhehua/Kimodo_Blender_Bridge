"""Ground-aware leg solving baked onto the original rig without new constraints."""
import math
import statistics

import bpy
from mathutils import Matrix, Quaternion, Vector


SIDES = ("l", "r")


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[round((len(ordered)-1) * fraction)]


def world_bone(target, name):
    return target.matrix_world @ target.pose.bones[name].matrix


def foot_geometry(target, roles, target_rest):
    """Calibrate the actual shoes, including weighted MMD D/helper chains."""
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.find_armature() == target
              and getattr(obj, "mmd_type", "NONE") not in {"RIGID_BODY", "JOINT"} and not obj.hide_render]
    if not meshes:
        raise ValueError("贴地修正需要角色网格以识别鞋底；请指定带网格的角色，或关闭足部贴地")
    feet = {side: target_rest["foot_"+side] for side in SIDES}
    length = sum((target_rest[a+"_l"].translation-target_rest[b+"_l"].translation).length
                 for a, b in (("thigh", "shin"), ("shin", "foot")))
    profiles = {side: {"points": [], "masks": {}} for side in SIDES}
    for mesh in meshes:
        for side in SIDES:
            ankle = feet[side].translation
            other = feet["r" if side == "l" else "l"].translation
            inverse = feet[side].to_quaternion().inverted()
            indices = []
            for vertex in mesh.data.vertices:
                point = mesh.matrix_world @ vertex.co
                if (point.z < ankle.z+length*.08 and (point-ankle).xy.length < length*.36
                        and (point-ankle).xy.length < (point-other).xy.length):
                    indices.append(vertex.index)
                    profiles[side]["points"].append(inverse @ (point-ankle))
            profiles[side]["masks"][mesh.name] = indices
    for side, profile in profiles.items():
        if len(profile["points"]) < 3:
            raise ValueError("无法识别" + ("左" if side == "l" else "右") + "脚鞋底，请检查角色参考姿态和骨骼映射")
        rotation = feet[side].to_quaternion()
        profile["rest_floor"] = feet[side].translation.z + min((rotation @ point).z for point in profile["points"])
        # A modest support hull is enough for the initial analytic height.
        points = profile["points"]
        profile["support"] = [points[index] for index in sorted(set(
            min(range(len(points)), key=lambda index: (rotation @ points[index]).dot(direction))
            for direction in (Vector((0, 0, 1)), Vector((0, 1, 1)), Vector((0, -1, 1)),
                              Vector((1, 0, 1)), Vector((-1, 0, 1)))))]
    return profiles, meshes


def measured_soles(meshes, profiles):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    result = {}
    for mesh in meshes:
        evaluated = mesh.evaluated_get(depsgraph)
        data = evaluated.to_mesh()
        try:
            for side in SIDES:
                indices = profiles[side]["masks"][mesh.name]
                if indices and max(indices) >= len(data.vertices):
                    raise ValueError("角色修改器改变了鞋底顶点索引，无法进行可靠的贴地校验")
                for index in indices:
                    point = evaluated.matrix_world @ data.vertices[index].co
                    if side not in result or point.z < result[side].z:
                        result[side] = point
        finally:
            evaluated.to_mesh_clear()
    return result


def source_contacts(samples, side, fps, leg_scale):
    feet = [sample["foot_"+side].translation for sample in samples]
    toes = [sample.get("toe_"+side, sample["foot_"+side]).translation for sample in samples]
    floor_ankle = percentile([point.z for point in feet], .15)
    floor_toe = percentile([point.z for point in toes], .15)
    speed = []
    for index in range(len(feet)):
        before, after = max(0, index-1), min(len(feet)-1, index+1)
        speed.append((feet[after]-feet[before]).xy.length * fps / max(1, after-before))
    stationary = [point.z <= floor_ankle+leg_scale*.025 and velocity < leg_scale*.22
                  for point, velocity in zip(feet, speed)]
    runs = []
    index = 0
    while index < len(samples):
        if not stationary[index]:
            index += 1
            continue
        end = index+1
        while end < len(samples) and stationary[end]:
            end += 1
        if end-index >= 3:
            runs.append((index, end))
        index = end
    if runs:
        stable = min((index for begin, end in runs for index in range(begin, end)),
                     key=lambda index: speed[index] + abs(toes[index].z-floor_toe))
    else:
        stable = min(range(len(samples)), key=lambda index: feet[index].z)
    return {"ankle_floor": floor_ankle, "toe_floor": floor_toe, "runs": runs, "neutral": stable,
            "clearance": [max(0.0, min(foot.z-floor_ankle, toe.z-floor_toe)) for foot, toe in zip(feet, toes)]}


def yaw_only(rotation):
    forward = rotation @ Vector((0, -1, 0))
    return Quaternion((0, 0, 1), math.atan2(forward.x, -forward.y))


def set_rotation(target, name, rotation):
    bone = target.pose.bones[name]
    matrix = world_bone(target, name)
    matrix = Matrix.LocRotScale(matrix.translation, rotation, matrix.to_scale())
    bone.matrix = target.matrix_world.inverted() @ matrix
    bone.location = (0, 0, 0)
    bpy.context.view_layer.update()


def solve_leg(target, roles, side, goal, foot_rotation, toe_rotation):
    thigh, shin, foot = (roles[part+"_"+side] for part in ("thigh", "shin", "foot"))
    hip, knee, ankle = (world_bone(target, name).translation for name in (thigh, shin, foot))
    upper, lower = (knee-hip).length, (ankle-knee).length
    direction = goal-hip
    distance = direction.length
    if distance < 1e-7:
        raise ValueError("脚部目标与髋关节重合，无法求解腿部")
    axis = direction.normalized()
    bend = knee-hip
    bend -= axis*bend.dot(axis)
    if bend.length < 1e-5:
        bend = Vector((0, -1, 0))
        bend -= axis*bend.dot(axis)
    bend.normalize()
    distance = min(max(distance, abs(upper-lower)+1e-6), upper+lower-1e-6)
    along = (upper*upper-lower*lower+distance*distance)/(2*distance)
    height = math.sqrt(max(0.0, upper*upper-along*along))
    wanted_knee = hip+axis*along+bend*height
    delta = (knee-hip).rotation_difference(wanted_knee-hip)
    set_rotation(target, thigh, delta @ world_bone(target, thigh).to_quaternion())
    knee, ankle = (world_bone(target, name).translation for name in (shin, foot))
    delta = (ankle-knee).rotation_difference(goal-knee)
    set_rotation(target, shin, delta @ world_bone(target, shin).to_quaternion())
    set_rotation(target, foot, foot_rotation)
    toe = roles.get("toe_"+side)
    if toe and toe_rotation:
        set_rotation(target, toe, toe_rotation)
    return (world_bone(target, foot).translation-goal).length


def lower_for_reach(target, roles, goals, carrier):
    offset = 0.0
    for side in SIDES:
        hip, knee, ankle = (world_bone(target, roles[part+"_"+side]).translation for part in ("thigh", "shin", "foot"))
        reach = (hip-knee).length+(knee-ankle).length-.0005
        horizontal = (goals[side]-hip).xy.length
        if horizontal >= reach:
            raise ValueError("脚部目标超出腿部可达范围，请检查动作与角色比例")
        maximum = goals[side].z+math.sqrt(reach*reach-horizontal*horizontal)
        offset = min(offset, maximum-hip.z)
    if offset < 0:
        matrix = world_bone(target, carrier)
        matrix.translation.z += offset
        target.pose.bones[carrier].matrix = target.matrix_world.inverted() @ matrix
        bpy.context.view_layer.update()
    return offset


def correct(target, source_roles, roles, shared, samples, source_rest, target_rest, alignment, scale,
            carrier, start, root_mode, ground_height):
    required = [part+"_"+side for side in SIDES for part in ("thigh", "shin", "foot")]
    if any(role not in shared for role in required):
        raise ValueError("足部贴地需要完整的左右大腿、小腿和脚踝映射；请补齐映射或关闭足部贴地")
    profiles, meshes = foot_geometry(target, roles, target_rest)
    scene = bpy.context.scene
    fps = scene.render.fps/scene.render.fps_base
    source_leg = sum((source_rest[a+"_l"].translation-source_rest[b+"_l"].translation).length
                     for a, b in (("thigh", "shin"), ("shin", "foot")))
    contacts = {side: source_contacts(samples, side, fps, source_leg) for side in SIDES}
    alignment_q = alignment.to_quaternion()
    first = samples[0]["pelvis"].translation
    source_base = Vector((first.x, first.y, source_rest["pelvis"].translation.z))
    root_offset = ground_height-statistics.mean(profile["rest_floor"] for profile in profiles.values())
    goals = {side: [] for side in SIDES}
    foot_rotations, toe_rotations = {side: [] for side in SIDES}, {side: [] for side in SIDES}
    for side in SIDES:
        role = "foot_"+side
        toe_role = "toe_"+side
        neutral = samples[contacts[side]["neutral"]]
        neutral_foot = neutral[role].to_quaternion()
        neutral_yaw = yaw_only(neutral_foot @ source_rest[role].to_quaternion().inverted())
        reference = neutral_yaw.inverted() @ neutral_foot
        toe_reference = neutral_yaw.inverted() @ neutral[toe_role].to_quaternion() if toe_role in neutral else None
        for index, sample in enumerate(samples):
            delta = sample[role].to_quaternion() @ reference.inverted()
            rotation = alignment_q @ delta @ alignment_q.inverted() @ target_rest[role].to_quaternion()
            foot_rotations[side].append(rotation)
            toe_rotation = None
            if toe_role in shared:
                delta = sample[toe_role].to_quaternion() @ toe_reference.inverted()
                toe_rotation = alignment_q @ delta @ alignment_q.inverted() @ target_rest[toe_role].to_quaternion()
            toe_rotations[side].append(toe_rotation)
            goal = target_rest["pelvis"].translation + alignment @ (sample[role].translation-source_base)*scale
            if root_mode == "IN_PLACE":
                travel = alignment @ (sample["pelvis"].translation-first)*scale
                goal.x -= travel.x
                goal.y -= travel.y
            goal.z = ground_height-min((rotation @ point).z for point in profiles[side]["support"])
            goal.z += contacts[side]["clearance"][index]*scale
            goals[side].append(goal)
        if root_mode == "TRAVEL":
            for begin, end in contacts[side]["runs"]:
                anchor = Vector((statistics.median(goals[side][i].x for i in range(begin, end)),
                                 statistics.median(goals[side][i].y for i in range(begin, end)), 0))
                for index in range(begin, end):
                    weight = min(1.0, (index-begin+1)/2, (end-index)/2)
                    weight = weight*weight*(3-2*weight)
                    goals[side][index].x += (anchor.x-goals[side][index].x)*weight
                    goals[side][index].y += (anchor.y-goals[side][index].y)*weight
    max_error, max_ground_error, max_penetration = 0.0, 0.0, 0.0
    ankle_tracks = {side: [] for side in SIDES}
    previous_quaternions = {}
    max_reach_adjustment = 0.0
    for index in range(len(samples)):
        frame = start+index
        scene.frame_set(frame)
        carrier_matrix = world_bone(target, carrier)
        carrier_matrix.translation.z += root_offset
        target.pose.bones[carrier].matrix = target.matrix_world.inverted() @ carrier_matrix
        bpy.context.view_layer.update()
        reach_adjustment = 0.0
        for _ in range(3):
            reach_adjustment += lower_for_reach(target, roles, {side: goals[side][index] for side in SIDES}, carrier)
            for side in SIDES:
                error = solve_leg(target, roles, side, goals[side][index], foot_rotations[side][index], toe_rotations[side][index])
                max_error = max(max_error, error)
            soles = measured_soles(meshes, profiles)
            errors = {side: ground_height+contacts[side]["clearance"][index]*scale-soles[side].z for side in SIDES}
            if max(abs(error) for error in errors.values()) < .0008:
                break
            for side in SIDES:
                goals[side][index].z += errors[side]
        soles = measured_soles(meshes, profiles)
        max_reach_adjustment = max(max_reach_adjustment, -reach_adjustment)
        for side in SIDES:
            if contacts[side]["clearance"][index] < .001:
                max_ground_error = max(max_ground_error, abs(soles[side].z-ground_height))
            max_penetration = max(max_penetration, ground_height-soles[side].z)
            ankle_tracks[side].append(world_bone(target, roles["foot_"+side]).translation.copy())
            for part in ("thigh", "shin", "foot", "toe"):
                name = roles.get(part+"_"+side)
                if name:
                    bone = target.pose.bones[name]
                    if name in previous_quaternions:
                        bone.rotation_quaternion.make_compatible(previous_quaternions[name])
                    previous_quaternions[name] = bone.rotation_quaternion.copy()
                    target.pose.bones[name].keyframe_insert("rotation_quaternion", frame=frame, group="足部贴地")
        target.pose.bones[carrier].keyframe_insert("location", frame=frame, group="角色位移")
    drift = {}
    for side in SIDES:
        spans = []
        for begin, end in contacts[side]["runs"]:
            points = ankle_tracks[side][begin+1:end-1]
            if points:
                anchor = points[0]
                spans.append(max((point-anchor).xy.length for point in points))
        drift[side] = max(spans, default=0.0)
    return {"ground_height": ground_height, "rest_ground_offset": root_offset,
            "max_ankle_solve_error": max_error, "max_contact_height_error": max_ground_error,
            "max_penetration": max_penetration, "max_stance_ankle_drift": drift,
            "max_pelvis_reach_adjustment": max_reach_adjustment,
            "contact_spans": {side: [[start+begin, start+end-1] for begin, end in contacts[side]["runs"]] for side in SIDES},
            "world_foot_lock": root_mode == "TRAVEL"}
