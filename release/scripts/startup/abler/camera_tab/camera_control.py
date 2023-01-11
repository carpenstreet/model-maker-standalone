# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import os

bl_info = {
    "name": "ACON3D Panel",
    "description": "",
    "author": "hoie@acon3d.com",
    "version": (0, 0, 1),
    "blender": (2, 93, 0),
    "location": "",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "CAMERA",
}


import bpy
from ..lib import cameras
from ..lib.import_file import AconImportHelper


class CreateCameraOperator(bpy.types.Operator):
    """Creates New Camera"""

    bl_idname = "acon3d.create_camera"
    bl_label = "Create Camera"
    bl_options = {"REGISTER", "UNDO"}

    name: bpy.props.StringProperty(name="Name")

    def execute(self, context):
        cameras.make_sure_camera_exists()

        # duplicate camera
        viewCameraObject = context.scene.camera
        camera_object = viewCameraObject.copy()
        camera_object.name = self.name
        camera_object.hide_viewport = True

        # add camera to designated collection (create one if not exists)
        collection = bpy.data.collections.get("ACON_col_cameras")
        if not collection:
            collection = bpy.data.collections.new("ACON_col_cameras")
            context.scene.collection.children.link(collection)
            layer_collection = context.view_layer.layer_collection
            layer_collection.children.get("ACON_col_cameras").exclude = True
        collection.objects.link(camera_object)

        # select created camera in custom view ui
        context.scene.ACON_prop.view = camera_object.name
        return {"FINISHED"}

    def invoke(self, context, event):
        self.name = cameras.gen_camera_name("ACON_Camera_")
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.separator()
        layout.prop(self, "name")
        layout.separator()


class DeleteCameraOperator(bpy.types.Operator):
    """Deletes Current Camera"""

    bl_idname = "acon3d.delete_camera"
    bl_label = "Delete Camera"
    bl_translation_context = "abler"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        collection = bpy.data.collections.get("ACON_col_cameras")
        return collection and len(collection.objects) > 1

    def execute(self, context):
        if currentCameraName := context.scene.ACON_prop.view:
            bpy.data.objects.remove(bpy.data.objects[currentCameraName])

        return {"FINISHED"}


class Acon3dCameraControlPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""

    bl_idname = "ACON3D_PT_CameraControl"
    bl_label = "Camera Control"
    bl_category = "Camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_translation_context = "abler"
    bl_order = 10
    bl_options = {"HIDE_HEADER"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()
        row.label(text="Camera Control", icon="CAMERA_DATA", text_ctxt="abler")

        cam = context.scene.camera
        if cam is not None:
            layout.prop(cam.data, "lens", text="Focal Length", text_ctxt="abler")

        return


def scene_mychosenobject_poll(self, object):
    return object.type == "CAMERA"


class Acon3dDOFPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""

    bl_parent_id = "ACON3D_PT_CameraControl"
    bl_idname = "ACON3D_PT_dof"
    bl_label = "Depth of Field"
    bl_category = "Camera"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_translation_context = "abler"
    COMPAT_ENGINES = {"BLENDER_EEVEE", "BLENDER_WORKBENCH"}

    def draw_header(self, context):
        if bpy.context.scene.camera is not None:
            scene = context.scene
            self.layout.prop(scene.ACON_prop, "use_dof", text="")
        else:
            self.layout.active = False

    def draw(self, context):
        if bpy.context.scene.camera is not None:
            layout = self.layout
            layout.use_property_split = True
            layout.use_property_decorate = False  # No animation.

            cam = bpy.context.scene.camera.data
            dof = cam.dof
            layout.active = dof.use_dof

            col = layout.column()
            col.prop(dof, "focus_object", text="Focus on Object", text_ctxt="abler")
            sub = col.column()
            sub.active = dof.focus_object is None
            sub.prop(dof, "focus_distance", text="Focus Distance", text_ctxt="abler")
            sub = col.column()
            sub.active = True
            sub.prop(dof, "aperture_fstop", text="F-stop", text_ctxt="abler")


classes = (
    Acon3dCameraControlPanel,
    CreateCameraOperator,
    DeleteCameraOperator,
    Acon3dDOFPanel,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
