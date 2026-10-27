"""
Kimodo Blender Bridge
=====================
Runs NVIDIA Kimodo in a managed subprocess for AI-powered human(oid)
motion generation directly inside Blender.

Features:
  • Generate motion from text prompts via a persistent bridge process
    (bridge_server.py, JSON over stdin/stdout — model loads once)
  • Automatic BVH import into Blender armature
  • Custom bone-mapping retargeting to any existing rig
  • Constraint-based retargeting with one-click bake
  • Save / load bone mapping presets

Requirements:
  • Blender 4.2+ (tested on 4.x and 5.x)
  • NVIDIA GPU (CUDA); Kimodo is installed automatically into ~/.kimodo-venv
    See: https://github.com/nv-tlabs/kimodo

"""

bl_info = {
    "name":        "Kimodo 动作桥接",
    "author":      "Lewdineer, muchuanhehua",
    "version":     (1, 6, 2),
    "blender":     (4, 2, 0),
    "location":    "View3D › Sidebar (N-Panel) › Kimodo",
    "description": "中文 Kimodo 动作生成、PMX 自动骨骼修复与人形动作重定向",
    "doc_url":     "https://github.com/muchuanhehua/Kimodo_Blender_Bridge",
    "tracker_url": "https://github.com/muchuanhehua/Kimodo_Blender_Bridge/issues",
    "category":    "Animation",
    "support":     "COMMUNITY",
}

import bpy

# Sub-modules (imported after bl_info for Blender's enable/disable system)
from . import properties, operators, ui_list, panels, constraints, timeline
from . import setup_operator, i18n, workflow
from . import subprocess_client as sc


def register():
    i18n.register()
    properties.register()
    operators.register()
    setup_operator.register()
    ui_list.register()
    panels.register()
    timeline.register()
    workflow.register()


def unregister():
    # Kill the bridge process so we don't leave orphaned GPU processes
    sc.stop()
    workflow.unregister()
    timeline.unregister()
    panels.unregister()
    ui_list.unregister()
    setup_operator.unregister()
    operators.unregister()
    properties.unregister()
    i18n.unregister()
