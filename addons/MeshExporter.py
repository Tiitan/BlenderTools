import json
from typing import Dict, Set, Union

import bpy
from bpy.props import StringProperty, CollectionProperty, EnumProperty
from bpy.types import Mesh, Operator, PropertyGroup
from bpy_extras.io_utils import ExportHelper


bl_info = {
    "name": "Flexible mesh exporter",
    "blender": (3, 1, 0),
    "category": "Object",
}



_BlenderTypeMap: Dict[str, Dict[str, Union[str, int]]] = {
    "FLOAT": {"type": "float32", "count": 1},
    "INT": {"type": "int32", "count": 1},
    "FLOAT_VECTOR": {"type": "float32", "count": 3},
    "FLOAT_COLOR": {"type": "float32", "count": 4},
    "BYTE_COLOR": {"type": "uint8", "count": 4},
    "FLOAT2": {"type": "float32", "count": 2},
}


def export_mesh(filepath: str, mesh: Mesh, config: Dict) -> Set[str]:
    # vertices data
    vertices = []
    for i in range(len(mesh.vertices)):
        vertex = {
            "POSITION": mesh.vertices[i].co[:]
        }
        for attr_map in config["attr_maps"]:
            vertex[attr_map.semantic] = mesh.attributes[attr_map.attribute].data[i].value
        vertices.append(vertex)

    # Index data
    indices = []
    if config["topology"] == "EDGE":
        indices = [v for edge in mesh.edges for v in edge.vertices]

    # attribute Header
    attributes = {
        "POSITION": _BlenderTypeMap["FLOAT_VECTOR"]
    }
    for attr_map in config["attr_maps"]:
        attributes[attr_map.semantic] = _BlenderTypeMap[mesh.attributes[attr_map.attribute].data_type]

    output = {
        "header": {
            "attributes": attributes,
            "verticesCount": len(vertices),
            "indicesCount": len(indices),
            "topology": config["topology"]
        },
        "data": {
            "vertices": vertices,
            "indices": indices
        }
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(json.dumps(output))

    return {'FINISHED'}


class AttributeMapping(PropertyGroup):
    attribute: StringProperty(name="Attribute", description="vertex attribute")
    semantic: StringProperty(name="Semantic", description="shader semantic (ex: TEXCOORD0)")


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

    topology: EnumProperty(
        name="Topology",
        description="select topology",
        items=(
            ('EDGE', "Edge", "export edges"),
            ('TRIANGLE', "Triangle", "export triangles"),
        ),
        default='EDGE',
    )

    attribute_mapping: CollectionProperty(
        name="Attribute mapping",
        type=AttributeMapping,
        description="map vertex attribute to shader semantic"
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        mesh: Mesh = context.active_object.data
        for i, attr_name in enumerate(mesh.attributes.keys()):
            new_attr_mapping: AttributeMapping = self.attribute_mapping.add()
            new_attr_mapping.name = attr_name
            new_attr_mapping.attribute = attr_name
            new_attr_mapping.semantic = f"TEXCOORD{i}"
        return super().invoke(context, event)

    def execute(self, context):
        mesh: Mesh = context.active_object.data
        return export_mesh(self.filepath, mesh, {"topology": self.topology, "attr_maps": self.attribute_mapping})


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
