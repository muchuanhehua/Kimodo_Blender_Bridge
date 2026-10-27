"""
Kimodo Blender Bridge — UIList
Custom UIList for displaying bone mapping pairs.
"""

from .i18n import ui, zh, report, localize_class

import bpy
from bpy.types import UIList


_MODE_ICONS = {
    "COPY_ROTATION":      'CON_ROTLIKE',
    "COPY_TRANSFORMS":    'CON_TRANSLIKE',
    "CHILD_OF":           'CON_CHILDOF',
    "CHILD_OF_ROTATION":  'CON_CHILDOF',
}


class KIMODO_UL_BoneMappings(UIList):
    """Draws each bone mapping row: [✓] SourceBone → TargetBone [mode]"""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        s = context.scene.kimodo

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            # Checkbox must live outside any disabled sub-row so it stays clickable
            row.prop(item, "enabled", text="", emboss=False,
                     icon='CHECKBOX_HLT' if item.enabled else 'CHECKBOX_DEHLT')

            # Everything else is dimmed when the pair is disabled
            sub = row.row(align=True)
            sub.enabled = item.enabled

            sub.prop_search(item, "source_bone",
                            s.source_armature.data if s.source_armature else bpy.data,
                            "bones" if s.source_armature else "objects",
                            text="", icon='BONE_DATA')

            sub.label(text="", icon='FORWARD')

            sub.prop_search(item, "target_bone",
                            s.target_armature.data if s.target_armature else bpy.data,
                            "bones" if s.target_armature else "objects",
                            text="", icon='BONE_DATA')

            if item.role:
                from .humanoid import ROLES
                sub.label(text=ROLES.get(item.role, (item.role,))[0])

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='BONE_DATA')

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        flt_flags = []
        flt_neworder = []

        if self.filter_name:
            flt_flags = bpy.types.UI_UL_list.filter_items_by_name(
                self.filter_name, self.bitflag_filter_item, items,
                "source_bone", reverse=self.use_filter_invert
            )

        return flt_flags, flt_neworder


class KIMODO_UL_History(UIList):
    """Draws each history entry: timestamp, truncated prompt, seed, duration, file check."""

    def draw_item(self, context, layout, data, item, icon, active_data,
                  active_propname, index):
        if self.layout_type not in {'DEFAULT', 'COMPACT'}:
            layout.label(text="", icon='TIME')
            return

        import os
        row = layout.row(align=True)
        ts_short = item.timestamp[-8:] if len(item.timestamp) >= 8 else item.timestamp
        row.label(text=ts_short, icon='TIME')
        prompt_preview = item.prompt[:48] + ("…" if len(item.prompt) > 48 else "")
        row.label(text=prompt_preview)
        # Compact stats hug the right so the prompt gets the leftover width
        stats = row.row(align=True)
        stats.alignment = 'RIGHT'
        # "…" marks multi-segment entries: all seeds are in the detail view
        seed_txt = str(item.seed) + ("…" if "," in item.seeds else "")
        stats.label(text=seed_txt)
        stats.label(text=f"{item.duration:.1f}s")
        stats.label(text="", icon='CHECKMARK' if os.path.isfile(item.bvh_path) else 'ERROR')


def register():
    bpy.utils.register_class(localize_class(KIMODO_UL_BoneMappings))
    bpy.utils.register_class(localize_class(KIMODO_UL_History))


def unregister():
    bpy.utils.unregister_class(KIMODO_UL_History)
    bpy.utils.unregister_class(KIMODO_UL_BoneMappings)
