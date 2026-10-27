"""PMX import and scoped MMD Tools repairs before common retargeting."""
import json
from pathlib import Path

import bpy

from . import humanoid

PREPARED_KEY = "kimodo_pmx_preparation"


def armature_for(obj):
    if obj is None:
        raise ValueError("请先选择一个角色")
    if obj.type == "ARMATURE":
        return obj
    if obj.type == "MESH":
        armature = obj.find_armature()
        if armature:
            return armature
    root = obj
    while root.parent:
        root = root.parent
    matches = [child for child in root.children_recursive if child.type == "ARMATURE"]
    if len(matches) != 1:
        raise ValueError("目标层级需要包含唯一骨架，请直接选择角色骨架")
    return matches[0]


def model_root(armature):
    obj = armature
    while obj:
        if getattr(obj, "mmd_type", None) == "ROOT":
            return obj
        obj = obj.parent
    raise ValueError("目标不是通过 MMD Tools 导入的 PMX 模型")


def require_tools():
    for name in ("import_model", "fix_bone_order", "fix_bone_issues"):
        try:
            getattr(bpy.ops.mmd_tools, name).get_rna_type()
        except RuntimeError as exc:
            raise RuntimeError("请启用支持骨骼修复的 MMD Tools（本版验证版本：4.5.14）") from exc


def select_armature(armature):
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    armature.hide_set(False)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature


def name_issues(armature):
    issues, seen = [], set()
    for bone in armature.pose.bones:
        if getattr(bone, "is_mmd_shadow_bone", False):
            continue
        name = bone.mmd_bone.name_j
        try:
            valid = bool(name) and len(name.encode("cp932")) <= 15
        except UnicodeEncodeError:
            valid = False
        if not valid or name in seen:
            issues.append(bone.name)
        seen.add(name)
    return issues


def prepare(armature, order_already_fixed=False):
    require_tools()
    model_root(armature)
    select_armature(armature)
    aliases = json.loads(armature.get(humanoid.ALIASES_KEY, "{}"))
    before = {}
    for bone in armature.pose.bones:
        if getattr(bone, "is_mmd_shadow_bone", False):
            continue
        names = [bone.name, bone.mmd_bone.name_j, bone.mmd_bone.name_e]
        aliases[bone.name] = list(dict.fromkeys(aliases.get(bone.name, []) + [n for n in names if n]))
        before[bone.name] = bone.mmd_bone.name_j
    armature[humanoid.ALIASES_KEY] = json.dumps(aliases, ensure_ascii=False)
    if not order_already_fixed and not armature.get(PREPARED_KEY):
        if bpy.ops.mmd_tools.fix_bone_order() != {"FINISHED"}:
            raise RuntimeError("MMD Tools 骨骼顺序修复失败")
        select_armature(armature)
    if bpy.ops.mmd_tools.fix_bone_issues() != {"FINISHED"}:
        raise RuntimeError("MMD Tools 骨名问题修复失败")
    remaining = name_issues(armature)
    if remaining:
        raise RuntimeError("骨骼修复后仍存在非法或重复骨名：" + "、".join(remaining[:8]))
    roles = humanoid.identify(armature)
    changed = {name: {"before": old, "after": armature.pose.bones[name].mmd_bone.name_j}
               for name, old in before.items() if armature.pose.bones[name].mmd_bone.name_j != old}
    previous = json.loads(armature.get(PREPARED_KEY, "{}"))
    cumulative = previous.get("name_changes", {})
    cumulative.update(changed)
    result = {"schema": 1, "roles": roles, "name_changes": cumulative,
              "root_carrier": humanoid.root_carrier(armature, roles),
              "bone_count": len(before)}
    armature[PREPARED_KEY] = json.dumps(result, ensure_ascii=False)
    bpy.context.scene.kimodo.target_armature = armature
    select_armature(armature)
    return result


def import_model(filepath, scale=0.08):
    require_tools()
    path = Path(bpy.path.abspath(filepath))
    if not path.is_file() or path.suffix.lower() != ".pmx":
        raise ValueError("请选择存在的 PMX 模型文件")
    before = {obj.as_pointer() for obj in bpy.data.objects}
    result = bpy.ops.mmd_tools.import_model(
        filepath=str(path), scale=scale, types={"MESH", "ARMATURE", "MORPHS", "DISPLAY", "PHYSICS"},
        fix_bone_order=True, fix_ik_links=False, apply_bone_fixed_axis=False,
        rename_bones=True, clean_model=False, remove_doubles=False,
        save_log=False,
    )
    if result != {"FINISHED"}:
        raise RuntimeError("MMD Tools 未完成 PMX 导入")
    armatures = [obj for obj in bpy.data.objects if obj.as_pointer() not in before and obj.type == "ARMATURE"]
    if len(armatures) != 1:
        raise RuntimeError("本次导入没有得到唯一角色骨架")
    armature = armatures[0]
    report = prepare(armature, order_already_fixed=True)
    armature["kimodo_import_scale"] = scale
    return armature, report
