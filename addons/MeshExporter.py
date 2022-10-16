from typing import Dict, Set

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy.types import Mesh, Operator, PropertyGroup
from bpy_extras.io_utils import ExportHelper


def export_mesh(mesh: Mesh, filepath: str, config: Dict) -> Set[str]:
    print("running write_some_data...")
    f = open(filepath, 'w', encoding='utf-8')
    f.write("Hello World %s" % config)
    f.close()

    return {'FINISHED'}


class AttributeMapping(PropertyGroup):
    attribute = StringProperty(name="Attribute", description="vertex attribute")
    semantic = StringProperty(name="Semantic", description="shader semantic (ex: TEXCOORD0)")


class ExportFlexibleMesh(Operator, ExportHelper):
    """
    Export a mesh in the custom flexible mesh text format .fmt,
    this format allow to export blender attributes into specified vertex semantic type and mapping.
    """

    bl_idname = "export.flexible_mesh"
    bl_label = "Export flexible mesh"
    filename_ext = ".fmt"

    filter_glob: StringProperty(
        default="*.fmt",
        options={'HIDDEN'},
        maxlen=255,
    )

    attribute_mapping: CollectionProperty(
        name="Attribute mapping",
        type=AttributeMapping,
        description="map vertex attribute to shader semantic"
    )

    def invoke(self, context, event):
        mesh: Mesh = context.active_object.data
        for attr_name in mesh.attributes.keys():
            new_attr_mapping: AttributeMapping = self.attribute_mapping.add()
            new_attr_mapping.name = attr_name
        return super().invoke(context, event)

    def execute(self, context):
        mesh: Mesh = context.active_object.data
        return export_mesh(mesh, self.filepath, self.attribute_mapping)


def menu_func_export(self, context):
    self.layout.operator(ExportFlexibleMesh.bl_idname, text="Export flexible mesh operator")


_classes = [AttributeMapping, ExportFlexibleMesh]


def register():
    for c in _classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    for c in _classes:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


if __name__ == "__main__":
    # unregister()
    register()

    # test call
    bpy.ops.export.flexible_mesh('INVOKE_DEFAULT')
