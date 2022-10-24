from typing import Set, List

from numpy import zeros, ndarray

import bmesh
import bpy
from bpy.types import Mesh, Operator, MeshSkinVertexLayer, MeshSkinVertex, Attribute


class ComputeDepthOperator(Operator):
    """
    This operator mist be used in object mode with a mesh selected that have a skin modifier and a Depth int attribute.
    It will initialize the depth attribute, setting the skin root to 1 and each vertex to its edge count distance to the root (+1).
    """

    bl_idname = "object.computedepth"
    bl_label = "compute depth"

    def _compute_depth(self, skin_layer_data: List[MeshSkinVertex], bm: bmesh) -> ndarray[int]:
        depth_values = zeros(len(bm.verts), dtype=int)
        current_depth = 1
        vertices_index = [vi for vi, msv in enumerate(skin_layer_data) if msv.use_root]
        while vertices_index:
            next_vert_index = []
            for vi in vertices_index:
                depth_values[vi] = current_depth
                linked_vert = [e.verts for e in bm.verts[vi].link_edges]
                linked_vert_index = [v.index for ve in linked_vert for v in ve]
                next_vert_index.extend([x for x in linked_vert_index if x != vi and x not in next_vert_index and not depth_values[x]])
            vertices_index = next_vert_index
            current_depth += 1

        return depth_values

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context: bpy.context) -> Set[str]:
        mesh: Mesh = context.active_object.data
        skin_layer: MeshSkinVertexLayer = mesh.skin_vertices[0]
        
        bm = bmesh.new(use_operators=False)  # create an empty BMesh
        bm.from_mesh(mesh)  # fill it in from a Mesh
        bm.verts.ensure_lookup_table()

        depth_values = self._compute_depth(skin_layer.data, bm)

        print(depth_values)
        mesh.attributes["Depth"].data.foreach_set("value", depth_values)
        
        bm.free()
        
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ComputeDepthOperator.bl_idname, text="Compute depth")


bpy.utils.register_class(ComputeDepthOperator)
bpy.types.VIEW3D_MT_object.append(menu_func)
# bpy.ops.object.computedepth()
