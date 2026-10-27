"""Chinese PMX preparation and common human-motion workflow operators."""
import json
import math

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Operator, Panel

from . import humanoid, motion_retarget, pmx_adapter


def populate_mapping(settings):
    if not settings.source_armature or not settings.target_armature:
        raise ValueError("请先指定动作源骨架与目标角色骨架")
    pairs = humanoid.mapping(settings.source_armature, settings.target_armature)
    settings.bone_mappings.clear()
    for role, source, target in pairs:
        item = settings.bone_mappings.add()
        item.source_bone, item.target_bone = source, target
        item.role = role
        item.enabled = True
    roles = humanoid.identify(settings.target_armature)
    settings.retarget_root_bone = humanoid.root_carrier(settings.target_armature, roles)
    action = settings.source_armature.animation_data.action if settings.source_armature.animation_data else None
    if action:
        settings.bake_start_frame = math.floor(action.frame_range[0])
        settings.bake_end_frame = math.ceil(action.frame_range[1])
    return pairs


class KIMODO_OT_ImportPMX(Operator):
    bl_idname = "kimodo.import_pmx"
    bl_label = "导入 PMX 并自动修复"
    bl_description = "通过 MMD Tools 导入角色，自动修复骨名和骨序，建立人形骨骼配置"
    bl_options = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.pmx", options={"HIDDEN"})

    def execute(self, context):
        try:
            armature, result = pmx_adapter.import_model(self.filepath, context.scene.kimodo.pmx_import_scale)
            settings = context.scene.kimodo
            settings.target_armature = armature
            settings.preparation_status = f"已准备 {len(result['roles'])} 个人形关节；累计修复 {len(result['name_changes'])} 个骨名"
            if settings.source_armature:
                populate_mapping(settings)
            self.report({"INFO"}, settings.preparation_status)
        except (ValueError, RuntimeError, OSError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class KIMODO_OT_PrepareTarget(Operator):
    bl_idname = "kimodo.prepare_target"
    bl_label = "使用所选角色并自动修复"
    bl_description = "为已导入的 PMX 角色执行骨骼修复与人形骨架检测"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            target = pmx_adapter.armature_for(context.active_object or context.scene.kimodo.target_armature)
            result = pmx_adapter.prepare(target)
            settings = context.scene.kimodo
            settings.target_armature = target
            settings.preparation_status = f"已准备 {len(result['roles'])} 个人形关节；累计修复 {len(result['name_changes'])} 个骨名"
            if settings.source_armature:
                populate_mapping(settings)
            self.report({"INFO"}, settings.preparation_status)
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


PRESETS = {
    "WALK": "A person walks forward at a natural pace.",
    "WAVE": "A person stands still and waves their right hand.",
    "SQUAT": "A person squats down and then stands back up.",
    "TURN": "A person turns around and then stands still.",
}


class KIMODO_OT_MotionPreset(Operator):
    bl_idname = "kimodo.motion_preset"
    bl_label = "使用动作预设"
    preset: EnumProperty(items=[("WALK", "自然走路", ""), ("WAVE", "挥手", ""),
                                ("SQUAT", "下蹲起身", ""), ("TURN", "转身", "")])

    def execute(self, context):
        context.scene.kimodo.prompt = PRESETS[self.preset]
        return {"FINISHED"}


class KIMODO_PT_Preparation(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Kimodo"
    bl_label = "模型准备 · PMX"
    bl_idname = "KIMODO_PT_Preparation"
    bl_order = 0

    def draw(self, context):
        layout, settings = self.layout, context.scene.kimodo
        layout.operator("kimodo.import_pmx", icon="IMPORT")
        layout.operator("kimodo.prepare_target", icon="ARMATURE_DATA")
        layout.prop(settings, "target_armature", text="目标角色")
        target = settings.target_armature
        if target and target.get(pmx_adapter.PREPARED_KEY):
            data = json.loads(target[pmx_adapter.PREPARED_KEY])
            layout.label(text=f"已准备 {len(data['roles'])} 个人形关节", icon="CHECKMARK")
            layout.label(text=f"累计修复 {len(data['name_changes'])} 个骨名")
        elif target:
            layout.label(text="目标尚未准备，请先执行自动修复", icon="INFO")
        row = layout.row()
        row.prop(settings, "pmx_import_scale")
        layout.label(text="导入后自动修复骨名与骨序", icon="TOOL_SETTINGS")
        layout.label(text="人形解算保留原有辅助骨与绑定")


_classes = [KIMODO_OT_ImportPMX, KIMODO_OT_PrepareTarget, KIMODO_OT_MotionPreset, KIMODO_PT_Preparation]


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
