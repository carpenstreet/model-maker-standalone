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


from typing import List, Tuple, Optional
import bpy
from bpy.types import Scene, Context
from . import shadow, layers, objects
from .materials import materials_handler
from math import radians
from .tracker import tracker
from . import cameras

# custom_properties에서 BoolProperty로 prop을 생성하면 버그가 발생해
# is_scene_renamed를 글로벌 변수로 정의함 (참조 : lib.objects의 글로벌 변수 items)
is_scene_renamed = True


def change_dof(self, context: Context) -> None:
    if use_dof := context.scene.ACON_prop.use_dof:
        tracker.depth_of_field_on()
    else:
        tracker.depth_of_field_off()

    context.scene.camera.data.dof.use_dof = use_dof


def change_background_images(self, context: Context) -> None:
    if show_background_images := context.scene.ACON_prop.show_background_images:
        tracker.background_images_on()
    else:
        tracker.background_images_off()

    context.scene.camera.data.show_background_images = show_background_images


def change_bloom(self, context: Context) -> None:
    if use_bloom := context.scene.ACON_prop.use_bloom:
        tracker.bloom_on()
    else:
        tracker.bloom_off()

    context.scene.eevee.use_bloom = use_bloom


def gen_scene_name(name: str, i: int = 1) -> str:
    combinedName: str = name + str(i)

    found = any(scene.name == combinedName for scene in bpy.data.scenes)

    return gen_scene_name(name, i + 1) if found else combinedName


def refresh_look_at_me() -> None:

    context = bpy.context
    prev_active_object = context.active_object
    # 기존에 있는 bpy.ops.object.select_all(action='DESELECT')를 사용하면 가끔 크래시가 나는 경우가 있음
    # 일단 GPU와 RAM의 사용량이 많아서 뭔가 delay가 생기는 경우에 해당 크래시가 나는 것으로 보임
    # 그래서 일단 deselect를 확보된 자원들을 이용해서 사용하도록 아래와 같이 안전하게 처리함.
    try:
        if context.selected_objects:
            bpy.ops.object.mode_set(mode="OBJECT")
            for obj in context.selected_objects:
                obj.select_set(False)
    except Exception as e:
        # raise RuntimeError("Error while deselecting objects: " + str(e)) # TODO: 아직 어떻게 관리되어야 할지 모르겠어서 raise는 일단 주석처리
        pass
    for obj in bpy.data.objects:
        if obj.ACON_prop.constraint_to_camera_rotation_z:
            obj.select_set(True)
            context.view_layer.objects.active = obj
            obj.ACON_prop.constraint_to_camera_rotation_z = True
            obj.select_set(False)

    context.view_layer.objects.active = prev_active_object


def change_background_color(self, context: Context) -> None:
    background_color = context.scene.ACON_prop.background_color

    ui = context.preferences.themes[0].user_interface
    ui.transparent_checker_primary = background_color
    ui.transparent_checker_secondary = background_color


# scene_items should be a global variable due to a bug in EnumProperty
scene_items: List[Tuple[str, str, str]] = []


def add_scene_items_to_collection():
    """scene_col에 bpy.data.scenes 항목 넣어주기"""

    prop = bpy.context.window_manager.ACON_prop
    prop.scene_col.clear()
    for i, scene in enumerate(bpy.data.scenes):
        # 파일 열기 시 씬 이름들을 Scene UI에 넣는 과정에서 change_scene_name이 실행이 됨
        # 실제 이름을 바꾸는 과정이 아니므로 is_scene_renamed를 설정
        # 각 씬마다 change_scene_name 함수에 들어갔다 나오므로 for문 안에서 설정
        global is_scene_renamed
        is_scene_renamed = False

        new_scene = prop.scene_col.add()
        new_scene.name = scene.name
        new_scene.index = i

    # 현재 씬과 scene_col 맞추기
    scene = bpy.context.scene
    scene_col_list = [*prop.scene_col]

    for item in scene_col_list:
        if item.name == scene.name:
            index = item.index
    prop.active_scene_index = index


def load_scene_by_index(self, context: Context) -> None:
    if not context:
        context = bpy.context

    if not self:
        self = context.window_manager.ACON_prop

    scene_col = self.scene_col
    active_scene_index = self.active_scene_index

    # EnumProperty인 self.scene을 select scene으로 변경
    self.scene = scene_col[active_scene_index].name
    load_scene(self, context)


def change_scene_name(self, context):
    global is_scene_renamed

    # CreateSceneOperator에서 create_scene 후에 change_scene_name이 실행되면서
    # active_scene_index가 이전 씬을 가리킨 상태에서 씬 복사를 하면서 씬 네이밍이 어긋나는 문제가 발생
    # 이를 위해 create_scene 후엔 change_scene_name을 실행하지 않도록 is_scene_renamed을 False로 설정해
    # 실제로 이름을 바꿀 때만 change_scene_name을 실행
    if is_scene_renamed:
        prop = context.window_manager.ACON_prop

        scene_col = prop.scene_col
        active_scene_index = prop.active_scene_index
        bpy.context.scene.name = scene_col[active_scene_index].name

    is_scene_renamed = True


def add_scene_items(self, context: Context) -> List[Tuple[str, str, str]]:
    scene_items.clear()
    for scene in bpy.data.scenes:
        scene_items.append((scene.name, scene.name, ""))

    return scene_items


def snap_to_face():
    scene = bpy.context.scene
    scene.tool_settings.use_snap = False
    scene.tool_settings.snap_elements = {"FACE"}


def load_scene(self, context: Context) -> None:

    if not context:
        context = bpy.context

    if not self:
        self = context.window_manager.ACON_prop

    newScene: Optional[Scene] = bpy.data.scenes.get(self.scene)
    oldScene: Optional[Scene] = context.scene
    context.window.scene = newScene

    materials_handler.toggle_toon_edge(None, context)
    materials_handler.change_line_props(None, context)
    materials_handler.toggle_toon_face(None, context)
    materials_handler.toggle_texture(None, context)
    materials_handler.toggle_shading(None, context)
    materials_handler.change_toon_depth(None, context)
    materials_handler.change_toon_shading_brightness(None, context)
    materials_handler.change_image_adjust_brightness(None, context)
    materials_handler.change_image_adjust_contrast(None, context)
    materials_handler.change_image_adjust_color(None, context)
    materials_handler.change_image_adjust_hue(None, context)
    materials_handler.change_image_adjust_saturation(None, context)

    layers.handle_layer_visibility_on_scene_change(oldScene, newScene)

    shadow.toggle_sun(None, context)
    shadow.change_sun_strength(None, context)
    shadow.toggle_shadow(None, context)
    shadow.change_sun_rotation(None, context)
    cameras.make_sure_camera_unselectable(self, context)

    # refresh look_at_me
    refresh_look_at_me()


def create_scene(old_scene: Scene, type: str, name: str) -> Optional[Scene]:
    global is_scene_renamed
    is_scene_renamed = False

    new_scene = old_scene.copy()
    new_scene.name = name
    if old_scene.camera:
        new_scene.camera = old_scene.camera.copy()
        new_scene.camera.data = old_scene.camera.data.copy()
        new_scene.camera.hide_select = True
        new_scene.collection.objects.link(new_scene.camera)
        try:
            new_scene.collection.objects.unlink(old_scene.camera)
        except:
            print("Failed to unlink camera from old scene.")

    else:
        obj = cameras.make_camera()
        new_scene.collection.objects.link(obj)
        new_scene.camera = obj
        cameras.switch_to_rendered_view()
        cameras.turn_on_camera_view(False)

    prop = new_scene.ACON_prop

    if type == "Indoor Daytime":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 0.7
        prop.toggle_shadow = True
        prop.sun_rotation_x = radians(45)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = 0.7
        prop.image_adjust_contrast = 0.5
        prop.image_adjust_color_r = 0.95
        prop.image_adjust_color_g = 0.95
        prop.image_adjust_color_b = 1.05
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1
        new_scene.eevee.use_bloom = True
        new_scene.eevee.bloom_threshold = 2
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (1, 1, 1)
        new_scene.eevee.bloom_intensity = 0.1
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    if type == "Indoor Sunset":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 1
        prop.toggle_shadow = True
        prop.sun_rotation_x = radians(15)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = 0
        prop.image_adjust_contrast = 0
        prop.image_adjust_color_r = 1.1
        prop.image_adjust_color_g = 0.9
        prop.image_adjust_color_b = 0.9
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1
        new_scene.eevee.use_bloom = True
        new_scene.eevee.bloom_threshold = 1
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (1, 1, 1)
        new_scene.eevee.bloom_intensity = 0.5
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    if type == "Indoor Nighttime":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 0.5
        prop.toggle_shadow = False
        prop.sun_rotation_x = radians(65)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = 0.1
        prop.image_adjust_contrast = 0
        prop.image_adjust_color_r = 1.05
        prop.image_adjust_color_g = 1
        prop.image_adjust_color_b = 0.95
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1
        new_scene.eevee.use_bloom = True
        new_scene.eevee.bloom_threshold = 1
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (0.9, 0.9, 1)
        new_scene.eevee.bloom_intensity = 0.5
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    if type == "Outdoor Daytime":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 1
        prop.toggle_shadow = True
        prop.sun_rotation_x = radians(60)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = 0.7
        prop.image_adjust_contrast = 0.5
        prop.image_adjust_color_r = 1
        prop.image_adjust_color_g = 1
        prop.image_adjust_color_b = 1
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1
        new_scene.eevee.use_bloom = False
        new_scene.eevee.bloom_threshold = 1
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (1, 1, 1)
        new_scene.eevee.bloom_intensity = 0.1
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    if type == "Outdoor Sunset":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 1
        prop.toggle_shadow = True
        prop.sun_rotation_x = radians(15)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = 0
        prop.image_adjust_contrast = 0
        prop.image_adjust_color_r = 1.1
        prop.image_adjust_color_g = 0.9
        prop.image_adjust_color_b = 0.9
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1
        new_scene.eevee.use_bloom = True
        new_scene.eevee.bloom_threshold = 0.8
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (1, 0.9, 0.8)
        new_scene.eevee.bloom_intensity = 0.5
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    if type == "Outdoor Nighttime":

        prop.toggle_toon_edge = True
        prop.edge_min_line_width = 1
        prop.edge_max_line_width = 1
        prop.edge_line_detail = 1.5
        prop.toggle_toon_face = True
        prop.toggle_texture = True
        prop.toggle_shading = True
        prop.toon_shading_depth = "3"
        prop.toon_shading_brightness_1 = 3
        prop.toon_shading_brightness_2 = 5
        prop.toggle_sun = True
        prop.sun_strength = 0.4
        prop.toggle_shadow = False
        prop.sun_rotation_x = radians(60)
        prop.sun_rotation_z = radians(45)
        prop.image_adjust_brightness = -0.3
        prop.image_adjust_contrast = -0.25
        prop.image_adjust_color_r = 0.9
        prop.image_adjust_color_g = 0.9
        prop.image_adjust_color_b = 1.1
        prop.image_adjust_hue = 0.5
        prop.image_adjust_saturation = 1.2
        new_scene.eevee.use_bloom = True
        new_scene.eevee.bloom_threshold = 1
        new_scene.eevee.bloom_knee = 0.5
        new_scene.eevee.bloom_radius = 6.5
        new_scene.eevee.bloom_color = (1, 1, 1)
        new_scene.eevee.bloom_intensity = 1
        new_scene.eevee.bloom_clamp = 0
        new_scene.render.resolution_x = 4800
        new_scene.render.resolution_y = 2700

    return new_scene
