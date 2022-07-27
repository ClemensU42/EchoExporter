import bpy

import bpy


def write_data(context, filepath, use_some_setting):
    print("running write_data")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Test %s" % use_some_setting)
        f.close()

    return {'FINISHED'}


from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_types import Operator


class EchoExporter(Operator, ExportHelper):
    """Export the current scene as a .echo folder for the Echo Renderer"""
    bl_idname = "echo_exporter.export_data"
    bl_label = "Export Echo Scene (.echo)"

    filename_ext = ".echo"

    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    use_setting: BoolProperty(
        name="Example Boolean",
        description="Example Tooltip",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('OPT_A', "First Option", "Description one"),
            ('OPT_B', "Second Option", "Description two"),
        ),
        default='OPT_A',
    )

    def execute(self, context):
        return write_data(context, self.filepath, self.use_setting)


def menu_func_export(self, context):
    self.layout.operator(EchoExporter.bl_idname, text="Export Echo Scene")


bl_info = {
    "name": "EchoExporter",
    "author": "ClemensU42",
    "description": "An addon to export your scene as a .echo folder for EchoRenderer",
    "blender": (3, 2, 1),
    "location": "View3D",
    "warning": "",
    "category": "Generic"
}

def register():
    bpy.utils.register_class(EchoExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

if __name__ == "__main__":
    register()