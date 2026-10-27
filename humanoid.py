"""Format-independent human joint semantics; original bone names stay intact."""
import json
import re
import unicodedata

ROLES = {
    "pelvis": ("骨盆", ("下半身", "Hips", "Pelvis", "Hip")),
    "spine": ("下躯干", ("上半身", "Spine", "spine_01")),
    "spine_mid": ("中躯干", ("上半身1", "上半身3", "Spine1", "spine_02")),
    "chest": ("胸部", ("上半身2", "Spine2", "Chest", "spine_03")),
    "neck": ("颈部", ("首", "Neck", "Neck1")),
    "head": ("头部", ("頭", "头", "Head")),
    "shoulder_l": ("左肩", ("左肩", "LeftShoulder", "shoulder.L", "clavicle_l")),
    "upper_arm_l": ("左上臂", ("左腕", "LeftArm", "LeftUpArm", "upper_arm.L", "upperarm_l")),
    "forearm_l": ("左前臂", ("左ひじ", "左肘", "LeftForeArm", "forearm.L", "lowerarm_l")),
    "hand_l": ("左手", ("左手首", "LeftHand", "hand.L", "hand_l")),
    "shoulder_r": ("右肩", ("右肩", "RightShoulder", "shoulder.R", "clavicle_r")),
    "upper_arm_r": ("右上臂", ("右腕", "RightArm", "RightUpArm", "upper_arm.R", "upperarm_r")),
    "forearm_r": ("右前臂", ("右ひじ", "右肘", "RightForeArm", "forearm.R", "lowerarm_r")),
    "hand_r": ("右手", ("右手首", "RightHand", "hand.R", "hand_r")),
    "thigh_l": ("左大腿", ("左足", "LeftUpLeg", "LeftThigh", "thigh.L", "thigh_l")),
    "shin_l": ("左小腿", ("左ひざ", "左膝", "LeftLeg", "LeftShin", "shin.L", "calf_l")),
    "foot_l": ("左脚踝", ("左足首", "LeftFoot", "foot.L", "foot_l")),
    "toe_l": ("左脚趾", ("左つま先", "左足先EX", "LeftToeBase", "toe.L", "ball_l")),
    "thigh_r": ("右大腿", ("右足", "RightUpLeg", "RightThigh", "thigh.R", "thigh_r")),
    "shin_r": ("右小腿", ("右ひざ", "右膝", "RightLeg", "RightShin", "shin.R", "calf_r")),
    "foot_r": ("右脚踝", ("右足首", "RightFoot", "foot.R", "foot_r")),
    "toe_r": ("右脚趾", ("右つま先", "右足先EX", "RightToeBase", "toe.R", "ball_r")),
}
REQUIRED = ("pelvis", "spine", "head", "upper_arm_l", "forearm_l", "hand_l",
            "upper_arm_r", "forearm_r", "hand_r", "thigh_l", "shin_l", "foot_l",
            "thigh_r", "shin_r", "foot_r")
CHILD_ROLE = {"upper_arm_l": "forearm_l", "forearm_l": "hand_l",
              "upper_arm_r": "forearm_r", "forearm_r": "hand_r",
              "thigh_l": "shin_l", "shin_l": "foot_l", "foot_l": "toe_l",
              "thigh_r": "shin_r", "shin_r": "foot_r", "foot_r": "toe_r"}
ALIASES_KEY = "kimodo_original_bone_aliases"
SOMA_ROLES = {
    "pelvis": "Hips", "spine": "Spine1", "spine_mid": "Spine2", "chest": "Chest",
    "neck": "Neck2", "head": "Head", "shoulder_l": "LeftShoulder",
    "upper_arm_l": "LeftArm", "forearm_l": "LeftForeArm", "hand_l": "LeftHand",
    "shoulder_r": "RightShoulder", "upper_arm_r": "RightArm", "forearm_r": "RightForeArm",
    "hand_r": "RightHand", "thigh_l": "LeftLeg", "shin_l": "LeftShin",
    "foot_l": "LeftFoot", "toe_l": "LeftToeBase", "thigh_r": "RightLeg",
    "shin_r": "RightShin", "foot_r": "RightFoot", "toe_r": "RightToeBase",
}


def normalize(name):
    name = unicodedata.normalize("NFKC", name or "").casefold().split(":")[-1]
    return re.sub(r"[\s_.\-]", "", name)


def bone_names(armature, pose_bone):
    """Metadata and saved aliases survive name repairs and Blender LR renaming."""
    mmd = getattr(pose_bone, "mmd_bone", None)
    names = [(pose_bone.name, 90)]
    if mmd:
        names += [(mmd.name_j, 110), (mmd.name_e, 70)]
    saved = json.loads(armature.get(ALIASES_KEY, "{}"))
    names += [(name, 105) for name in saved.get(pose_bone.name, [])]
    return [(normalize(name), rank) for name, rank in names if name]


def identify(armature, strict=True):
    if armature is None or armature.type != "ARMATURE":
        raise ValueError("请选择有效的角色骨架")
    candidates = {p.name: bone_names(armature, p) for p in armature.pose.bones
                  if not getattr(p, "is_mmd_shadow_bone", False)}
    result = {}
    for role, (label, aliases) in ROLES.items():
        scores = []
        for name, names in candidates.items():
            score = max((rank * 100 - index for index, alias in enumerate(aliases)
                         for candidate, rank in names if candidate == normalize(alias)), default=0)
            if score:
                scores.append((score, name))
        scores.sort(reverse=True)
        if scores:
            if len(scores) > 1 and scores[0][0] == scores[1][0]:
                raise ValueError(f"{label}存在同等匹配的骨骼：{scores[0][1]}、{scores[1][1]}，请修正骨名或映射")
            result[role] = scores[0][1]
    # SOMA is not the Mixamo hierarchy: Spine1 is the first spine and LeftLeg
    # is the thigh. Detect its complete signature before assigning those roles.
    if {"Spine1", "Spine2", "Chest", "LeftLeg", "LeftShin", "RightLeg", "RightShin"} <= candidates.keys():
        result.update({role: name for role, name in SOMA_ROLES.items() if name in candidates})
    missing = [ROLES[role][0] for role in REQUIRED if role not in result]
    if strict and missing:
        raise ValueError("缺少必要的人形骨骼：" + "、".join(missing))
    if len(set(result.values())) != len(result):
        raise ValueError("同一目标骨骼被分配到多个关节，请检查映射")
    return result


def root_carrier(armature, roles):
    for alias in ("センター", "Center", "Groove", "グルーブ", "Root", "全ての親"):
        matches = [p.name for p in armature.pose.bones
                   if any(name == normalize(alias) for name, _ in bone_names(armature, p))]
        if len(matches) == 1:
            return matches[0]
    return roles["pelvis"]


def mapping(source, target):
    source_roles, target_roles = identify(source), identify(target)
    return [(role, name, target_roles[role]) for role, name in source_roles.items()
            if role in target_roles]
