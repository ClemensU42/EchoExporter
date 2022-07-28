import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
from bpy_types import Operator


def write_data(context, filepath, use_some_setting):
    print("running write_data")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("Test %s" % use_some_setting)
        f.close()

    return {'FINISHED'}


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

    # List of attributes for the EvaluationProfile
    evaluator: EnumProperty(
        name="Evaluator",
        description="The available evaluators in Echo for rendering",
        items=(
            ("PathTracedEvaluator", "Path traced evaluator", "classical Path tracing"),

        ),
        default="PathTracedEvaluator"
    )

    pattern: EnumProperty(
        name="Pattern",
        description="The pattern in which the different parts of the image will be rendered",
        items=(
            ("HilbertCurve", "Hilbert Curve", "Pattern of the hilbert curve"),
        ),
        default="HilbertCurve"
    )

    max_epoch: IntProperty(
        name="Max epoch amount",
        description="Defines the maximum amount of Epochs",
        min=1,
        step=1,
        soft_max=128,
        default=20
    )

    buffer_width: IntProperty(
        name="Buffer Width",
        description="Defines the maximum width of the render buffer / rendered image",
        min=1,
        soft_max=1920,
        step=1,
        default=1920
    )

    buffer_height: IntProperty(
        name="Buffer Height",
        description="Defines the maximum height of the render buffer / rendered image",
        min=1,
        soft_max=1080,
        step=1,
        default=1080
    )

    distribution_extend: IntProperty(
        name="Distribution Extend",
        description="[to be added]",
        min=1,
        step=1,
        default=16
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

def unregister():
    bpy.utils.unregister_class(EchoExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
