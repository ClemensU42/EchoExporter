import math
from math import pi, degrees

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.props import *
from bpy_types import Operator
import os

blender_materials_to_echo_materials = {
    "ShaderNodeBsdfDiffuse": "Diffuse",
    "ShaderNodeEmission": "Emissive",
    "ShaderNodeBsdfGlossy": "Mirror",

}


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

    obj_files = {}

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

    return obj_files


def get_materials(context):
    scene = context.scene

    obs = [o for o in scene.objects if o.type == 'MESH']

    materials = {}

    for ob in obs:
        node_tree = ob.active_material.node_tree

        # find output node
        output_node = None
        for n in node_tree.nodes:
            if n.bl_idname == 'ShaderNodeOutputMaterial':
                output_node = n
                break
        if output_node is None:
            continue

        material_node = None
        # get material connected to output node
        for nl in node_tree.links:
            if nl.to_node.bl_idname == 'ShaderNodeOutputMaterial':
                material_node = nl.from_node
                break
        if material_node is None:
            continue

        echo_material = blender_materials_to_echo_materials.get(material_node.bl_idname)
        if echo_material is None:
            continue

        new_material_string = ""

        if echo_material == "Diffuse":
            color = material_node.inputs.get("Color").default_value
            new_material_string = f"\t:material{ob.name.replace(' ', '').replace('_','')} = new Matte {{.Albedo = new Pure(\"hdr({color[0]}, {color[1]}, {color[2]}, {color[3]} )\")}}\n"

        elif echo_material == "Emissive":
            color = material_node.inputs.get("Color").default_value
            power = material_node.inputs.get("Strength").default_value
            color[0] *= power / 10.0
            color[1] *= power / 10.0
            color[2] *= power / 10.0
            color[3] *= power / 10.0
            new_material_string = f"\t:material{ob.name.replace(' ', '').replace('_','')} = new Emissive {{.Albedo = new Pure(\"hdr({color[0]}, {color[1]}, {color[2]}, {color[3]} )\")}}\n"

        elif echo_material == "Mirror":
            color = material_node.inputs.get("Color").default_value
            new_material_string = f"\t:material{ob.name.replace(' ', '').replace('_','')} = new Mirror {{.Albedo = new Pure(\"hdr({color[0]}, {color[1]}, {color[2]}, {color[3]} )\")}}\n"

        else:
            continue

        materials[ob.name] = new_material_string

    return materials


def write_echo_data(context, filepath, exporter):
    print("running write_data")

    texture_path = os.path.join(filepath, "textures")
    geometries_path = os.path.join(filepath, "geometries")
    echo_file_name = filepath.split('/')[-1]

    create_echo_directories(filepath, texture_path, geometries_path)

    with open(os.path.join(filepath, echo_file_name), 'w', encoding='utf-8') as file:
        # create scene
        obj_files = save_geometries(context, geometries_path)
        obj_materials = get_materials(context)

        scene_content = ""
        # add materials to scene
        for material_key in obj_materials:
            scene_content += obj_materials[material_key]

        # add meshed to scene
        scene = context.scene
        obs = [o for o in scene.objects if o.type == 'MESH']
        for ob in obs:
            relative_geometry_path = os.path.join("./geometries", obj_files[ob.name])
            rotation = ob.rotation_euler
            scale = ob.scale
            location = ob.location

            rotation_string = f"\"{round(degrees(rotation[0]))} {round(degrees(rotation[1]))} {round(degrees(rotation[2]))}\""
            scale_string = f"\"{scale[0]}\""
            location_string = f"\"{location[0]} {location[1]} {location[2]}\""
            material_string = f"link material{ob.name.replace(' ', '').replace('_','')}"
            mesh_string = f"\"{relative_geometry_path}\""

            mesh_entity = f"\t.Add(new MeshEntity {{ .Source = {mesh_string} .Material = {material_string} .Position = {location_string} .Rotation = {rotation_string} .Scale = {scale_string}}})\n"

            scene_content += mesh_entity

        # add camera to scene

        camera = [o for o in scene.objects if o.type == 'CAMERA'][0]
        camera_location = camera.location
        camera_rotation = camera.rotation_euler

        camera_fov_string = f"\"{round(camera.data.angle_x * 180 / pi)}\""
        camera_position_string = f"\"{camera_location[0]} {camera_location[1]} {camera_location[2]}\""
        camera_rotation_string = f"\"{round(degrees(camera_rotation[0]))} {round(degrees(camera_rotation[1]))} {round(degrees(camera_rotation[2]))}\""

        scene_content += f"\t.Add(new Camera({camera_fov_string}) {{ .Position = {camera_position_string} .Rotation = {camera_rotation_string} }})\n "

        # add lights to scene

        lights = [o for o in scene.objects if o.type == 'LIGHT']
        point_lights = [light for light in lights if light.data.type == 'POINT']

        for pl in point_lights:
            location = pl.location
            color = pl.data.color
            energy = pl.data.energy
            intensity = [color[0] * energy / 10, color[1] * energy / 10, color[2] * energy / 10]

            intensity_string = f"\"hdr({intensity[0]}, {intensity[1]}, {intensity[2]})\""
            position_string = f"\"{location[0]} {location[1]} {location[2]}\""

            scene_content += f"\t.Add(new PointLight {{ .Intensity = {intensity_string} .Position = {position_string} }})\n"

        scene = f":scene = new Scene\n{{\n{scene_content}}}\n\n"

        # create profile
        profileContent = f"\t.Evaluator = new {exporter.evaluator}\n"
        profileContent += f"\t.Distribution = new StratifiedDistribution {{ .Extend = \"{exporter.distribution_extend}\" }}\n"
        profileContent += f"\t.Buffer = new RenderBuffer(\"{exporter.buffer_width} {exporter.buffer_height}\")\n"
        profileContent += f"\t.Pattern = new {exporter.pattern}\n"
        profileContent += f"\t.MinEpoch = \"1\"\n\t.MaxEpoch = \"{exporter.max_epoch}\"\n"
        profile = f":profile = new EvaluationProfile\n{{\n{profileContent}}}"

        file.write(scene)
        file.write(profile)

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
            ("HilbertCurvePattern", "Hilbert Curve", "Pattern of the hilbert curve"),
        ),
        default="HilbertCurvePattern"
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
