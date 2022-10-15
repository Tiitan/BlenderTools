from typing import Set, List

import bpy
from bpy.types import Mesh, Operator


class SkinModifierToAttributeOperator(Operator):
    """
    This operator mist be used in object mode with a mesh selected that have a skin modifier and a Radius float attribute.
    It will initialize the radius attribute, copying data from the skin X radius.
    """

    bl_idname = "object.skinradiustoattribute"
    bl_label = "Skin radius to attribute"

    def execute(self, context: bpy.context) -> Set[str]:
        mesh: Mesh = context.active_object.data
        radius_values: List[float] = [v.radius[0] for v in mesh.skin_vertices[0].data]
        mesh.attributes["Radius"].data.foreach_set("value", radius_values)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SkinModifierToAttributeOperator.bl_idname, text="Skin radius to attribute Operator")


bpy.utils.register_class(SkinModifierToAttributeOperator)
bpy.types.VIEW3D_MT_object.append(menu_func)
# bpy.ops.object.skinradiustoattribute()
