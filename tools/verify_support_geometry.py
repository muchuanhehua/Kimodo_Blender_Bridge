"""Exercise bare feet, flat soles and thick soles with different avatar scales."""
import json
from pathlib import Path
import sys

import addon_utils
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_blender import load_addon


def main():
    root = Path(__file__).resolve().parents[1]
    addon_utils.enable("bl_ext.blender_org.mmd_tools", default_set=False)
    load_addon(root)
    from kimodo_dev import humanoid, motion_retarget
    bpy.ops.wm.open_mainfile(filepath=str(root / ".verification/pmx-kimodo-walk.blend"))
    scene = bpy.context.scene
    source = next(obj for obj in scene.objects if obj.type == "ARMATURE" and obj.get("kimodo_source"))
    # The procedural meshes are verification fixtures, not edits to private characters.
    for obj in scene.objects:
        if obj != source:
            obj.hide_viewport = True
    results = []
    cases = (("barefoot", (.06, .06), .8, 0.0), ("flat_sole", (.09, .09), 1.0, 0.0),
             ("thick_sole", (.20, .20), 1.25, 0.0), ("mixed_soles", (.06, .18), 1.0, .1))
    for index, (label, depths, body_scale, ground) in enumerate(cases):
        target = source.copy()
        target.data = source.data.copy()
        target.name = "SupportFixture_" + label
        target.animation_data_clear()
        target.location = (index*3, 0, 0)
        target.scale = (body_scale,)*3
        scene.collection.objects.link(target)
        for bone in target.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        bpy.context.view_layer.update()
        roles = humanoid.identify(target)
        vertices, faces, memberships = [], [], {}
        for side, depth in zip(("l", "r"), depths):
            name = roles["foot_"+side]
            ankle = target.matrix_world @ target.data.bones[name].head_local
            inverse = target.matrix_world.inverted()
            offset = len(vertices)
            vertices.extend(inverse @ (ankle+Vector((x, y, z))*body_scale)
                            for z in (-depth, .025) for y in (-.16, .06) for x in (-.04, .04))
            faces.extend(tuple(offset+i for i in face) for face in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)))
            memberships[name] = list(range(offset, offset+8))
        data = bpy.data.meshes.new(target.name+"_feet")
        data.from_pydata(vertices, [], faces)
        mesh = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(mesh)
        mesh.parent = target
        for name, indices in memberships.items():
            mesh.vertex_groups.new(name=name).add(indices, 1.0, "REPLACE")
        mesh.modifiers.new("FixtureSkin", "ARMATURE").object = target
        state = motion_retarget.preview(source, target, 1, 73, ground_height=ground)
        contact = state["foot_contact"]
        assert contact["max_contact_height_error"] < .002, (label, contact)
        assert contact["max_penetration"] < .002, (label, contact)
        assert max(contact["max_stance_ankle_drift"].values()) < .002, (label, contact)
        mesh_minimum = float("inf")
        for frame in range(1, 74):
            scene.frame_set(frame)
            evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh_minimum = min(mesh_minimum, min((evaluated.matrix_world @ vertex.co).z for vertex in evaluated.data.vertices))
        assert mesh_minimum >= ground-.002, (label, mesh_minimum)
        results.append({"fixture": label, "foot_depths": depths, "body_scale": body_scale,
                        "ground_height": ground, "actual_mesh_min_z": mesh_minimum, "contact": contact})
        print("SUPPORT_GEOMETRY_PASS", json.dumps(results[-1]), flush=True)
        mesh.hide_viewport = True
        target.hide_viewport = True
    output = root / ".verification/foot-contact/support-geometry.json"
    output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
