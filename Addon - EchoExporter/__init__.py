import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
from bpy_types import Operator
import os


def create_echo_directories(filepath, texture_path, geometries_path):
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    if not os.path.exists(texture_path):
        os.mkdir(texture_path)
    if not os.path.exists(geometries_path):
        os.mkdir(geometries_path)


def save_geometries(context, geometries_path):
    scene = context.scene
    viewlayer = context.view_layer

    obs = [o for o in scene.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')

    obj_files = []

    for ob in obs:
        viewlayer.objects.active = ob
        ob.select_set(True)
        ply_path = os.path.join(geometries_path, f"{ob.name}.ply")
        bpy.ops.export_mesh.ply(
            filepath=str(ply_path),
            use_selection=True,
            use_colors=False
        )
        ob.select_set(False)

        obj_files[ob.name] = f"{ob.name}.ply"

def write_echo_data(context, filepath, exporter):
    print("running write_data")

    texture_path = os.path.join(filepath, "textures")
    geometries_path = os.path.join(filepath, "geometries")
    echo_file_name = filepath.split('/')[-1]

    create_echo_directories(filepath, texture_path, geometries_path)

    with open(os.path.join(filepath, echo_file_name), 'w', encoding='utf-8') as file:
        #create scene

        #create profile
        profileContent = f"\t.Evaluator = new {exporter.evaluator}\n"
        profileContent += f"\t.Distribution = new StratifiedDistribution {{ .Extend = \"{exporter.distribution_extend}\" }}\n"
        profileContent += f"\t.Buffer = new RenderBuffer(\"{exporter.buffer_width} {exporter.buffer_height}\")\n"
        profileContent += f"\t.Pattern = new {exporter.pattern}\n"
        profileContent += f"\t.MinEpoch = \"1\"\n\t.MaxEpoch = \"{exporter.max_epoch}\"\n"
        profile = f":profile = new EvaluationProfile\n{{\n{profileContent}}}"
        file.write(profile)

    save_geometries(context, geometries_path)

    return {'FINISHED'}


class EchoExporter(Operator, ExportHelper):
    """Export the current scene as a .echo folder for the Echo Renderer"""
    bl_idname = "echo_exporter.export_data"
    bl_label = "Export Echo Scene (.echo)"

    filename_ext = ".echo"

    filter_glob: StringProperty(
        default="*.echo",
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
        return write_echo_data(context, self.filepath, self)


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
