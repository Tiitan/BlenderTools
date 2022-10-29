from typing import Set, List

import bpy
from bpy.types import Mesh, Operator, Attribute, MeshUVLoopLayer, MeshLoop, MeshUVLoop
from mathutils import Vector


bl_info = {
    "name": "ColorToUv",
    "blender": (3, 1, 0),
    "category": "Object",
}


class ColorToUvOperator(Operator):
    """
    This operator must be used in object mode with a mesh selected that have matching color and UV attributes.
    It will copy the R and G vertex color into U and V texture coordinate.
    """

    bl_idname = "object.colortouv"
    bl_label = "color to UV"

    @classmethod
    def poll(cls, context) -> bool:
        return context.active_object is not None

    def execute(self, context: bpy.context) -> Set[str]:
        mesh: Mesh = context.active_object.data
        for attr in mesh.attributes:
            uv_layer = mesh.uv_layers.get(attr.name)
            if uv_layer:
                self._copy_color_to_uv(attr, uv_layer, mesh.loops)

        return {'FINISHED'}

    def _copy_color_to_uv(self, attr: Attribute, uv_layer: MeshUVLoopLayer, loops: List[MeshLoop]) -> None:
        uv_loops: List[MeshUVLoop] = uv_layer.data
        for loop in loops:
            color = attr.data[loop.index].color
            uv_loops[loop.index].uv = Vector([color[0], color[1]])


def menu_func(self, context) -> None:
    self.layout.operator(ColorToUvOperator.bl_idname, text="Color to UV Operator")


def register() -> None:
    bpy.utils.register_class(ColorToUvOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister() -> None:
    bpy.utils.unregister_class(ColorToUvOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)


if __name__ == "__main__":
    bpy.utils.register_class(ColorToUvOperator)
    bpy.ops.object.colortouv()
