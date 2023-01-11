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
    "category": "ACON3D",
}

import bpy
from ..lib import layers
from ..lib.tracker import tracker
from typing import Any, Dict, List, Union, Tuple, Optional


def select_active_and_descendants():
    bpy.ops.object.select_grouped()
    bpy.context.view_layer.objects.active.select_set(True)


# items should be a global variable due to a bug in EnumProperty
items: List[Tuple[str, str, str]] = []


def add_group_list_from_collection(
    self, context: bpy.context
) -> List[Tuple[str, str, str]]:
    items.clear()
    draft_selection = manager.selection_undo_stack.copy()
    obj = context.active_object
    for item in draft_selection:
        icon_str = "OUTLINER_OB_MESH" if item.type == "MESH" else "OUTLINER_OB_EMPTY"
        items.append((item.name, item.name, "", icon_str, 0))
    icon_str = "OUTLINER_OB_MESH" if obj.type == "MESH" else "OUTLINER_OB_EMPTY"
    items.append((obj.name, obj.name, "", icon_str, 0))
    if obj.parent:
        while obj.parent.parent:
            icon_str = (
                "OUTLINER_OB_MESH" if obj.parent.type == "MESH" else "OUTLINER_OB_EMPTY"
            )
            items.append((obj.parent.name, obj.parent.name, "", icon_str, 0))
            obj = obj.parent

    return items


class GroupNavigationManager:
    _selection_undo_stack = []
    _user_event_disabled = False

    def __repr__(self):
        return repr(self._selection_undo_stack)

    def go_top(self):
        obj = bpy.context.active_object
        if obj.parent:
            while obj.parent.parent:
                self._selection_undo_stack.append(obj)
                obj = obj.parent
        with self._programmatic_selection_scope():
            bpy.context.view_layer.objects.active = obj
            select_active_and_descendants()

    def go_up(self):
        obj = bpy.context.active_object
        if parent := obj.parent:
            if parent.parent is not None:
                with self._programmatic_selection_scope():
                    self._selection_undo_stack.append(obj)
                    bpy.context.view_layer.objects.active = parent
                    select_active_and_descendants()

    def go_down(self):
        if len(self._selection_undo_stack) > 0:
            with self._programmatic_selection_scope():
                last_selected = self._selection_undo_stack.pop()
                bpy.context.view_layer.objects.active = last_selected
                select_active_and_descendants()

    def go_bottom(self):
        if len(self._selection_undo_stack) > 0:
            with self._programmatic_selection_scope():
                while len(self._selection_undo_stack) > 0:
                    last_selected = self._selection_undo_stack.pop()
                bpy.context.view_layer.objects.active = last_selected
                select_active_and_descendants()

    def _programmatic_selection_scope(self):
        return ProgrammaticSelectionScope(self)

    @property
    def selection_undo_stack(self):
        return self._selection_undo_stack


class ProgrammaticSelectionScope:
    """
    msgbus 콜백이 다음 이벤트 루프에 실행되는 문제가 있어서,
    실행을 지연시키기 위하여 실행 블록을 잡아주는 클래스
    """

    def __init__(self, manager: GroupNavigationManager):
        self._manager = manager

    def __enter__(self):
        self._manager._user_event_disabled = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        def delayed():
            self._manager._user_event_disabled = False

        bpy.app.timers.register(delayed, first_interval=0.01)


manager = GroupNavigationManager()


class GroupNavigateTopOperator(bpy.types.Operator):
    """Move to top group"""

    bl_idname = "acon3d.group_navigate_top"
    bl_label = "Top Group"
    bl_translation_context = "abler"

    def execute(self, context):
        tracker.group_navigate_top()
        manager.go_top()
        return {"FINISHED"}


class GroupNavigateUpOperator(bpy.types.Operator):
    """Move to upper group"""

    bl_idname = "acon3d.group_navigate_up"
    bl_label = "Upper Group"
    bl_translation_context = "abler"

    def execute(self, context):
        tracker.group_navigate_up()
        manager.go_up()
        return {"FINISHED"}


class GroupNavigateDownOperator(bpy.types.Operator):
    """Move to lower group"""

    bl_idname = "acon3d.group_navigate_down"
    bl_label = "Lower Group"
    bl_translation_context = "abler"

    def execute(self, context):
        tracker.group_navigate_down()
        manager.go_down()
        return {"FINISHED"}


class GroupNavigateBottomOperator(bpy.types.Operator):
    """Move to bottom group/object"""

    bl_idname = "acon3d.group_navigate_bottom"
    bl_label = "Bottom Group"
    bl_translation_context = "abler"

    def execute(self, context):
        tracker.group_navigate_bottom()
        manager.go_bottom()
        return {"FINISHED"}


class Acon3dObjectPanel(bpy.types.Panel):
    bl_idname = "ACON_PT_Object_Main"
    bl_label = "Object Control"
    bl_category = "Scene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 11

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon="FILE_3D")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.scale_x = 3
        col.separator()
        col = row.column()

        # context.selected_objects는 드래그로 선택된 개체, context.object는 개별 선택 개체
        # 드래그로 선택해도 context.object=None일 수 있으므로 두 조건을 모두 확인
        # https://docs.blender.org/manual/en/3.0/scene_layout/object/selecting.html#selections-and-the-active-object
        if context.selected_objects and context.object:
            row = col.row()
            row.prop(
                context.object.ACON_prop,
                "constraint_to_camera_rotation_z",
                text="Look at me",
            )
        else:
            row = col.row(align=True)
            row.enabled = False
            row.label(text="Look at me", icon="SELECT_SET")


class Acon3dGroupNavigationPanel(bpy.types.Panel):
    bl_parent_id = "ACON_PT_Object_Main"
    bl_idname = "ACON_PT_Group_Navigation"
    bl_label = "Group Navigation"
    bl_category = "Scene"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        if context.selected_objects and context.object:
            obj = context.object
            prop = obj.ACON_prop
            row = layout.row(align=True)
            row.prop(prop, "group_list", text="")
            row.operator("acon3d.group_navigate_top", text="", icon="TRIA_UP_BAR")
            row.operator("acon3d.group_navigate_up", text="", icon="TRIA_UP")
            row.operator("acon3d.group_navigate_down", text="", icon="TRIA_DOWN")
            row.operator("acon3d.group_navigate_bottom", text="", icon="TRIA_DOWN_BAR")
        else:
            row = layout.row()
            col = row.column()
            col.scale_x = 3
            col.separator()
            col = row.column()
            col.label(text="No selected object", text_ctxt="abler")


# Camera, Sun 제외 전체 선택
class ObjectAllSelectOperator(bpy.types.Operator):
    """Select all objects"""

    bl_idname = "acon3d.object_select_all"
    bl_label = "Object All Select"
    bl_translation_context = "*"
    bl_options = {"REGISTER", "UNDO"}
    action = ""

    def invoke(self, context, event):
        key_type = event.type
        key_value = event.value

        if (key_type == "A" and key_value == "DOUBLE_CLICK") or (
            key_type == "ESC" and key_value == "PRESS"
        ):
            self.action = "DESELECT"
        elif key_type == "I" and key_value == "PRESS":
            self.action = "INVERT"
        elif key_type == "A" and key_value == "PRESS":
            self.action = "SELECT"

        return self.execute(context)

    def execute(self, context):
        if self.action == "SELECT":
            bpy.ops.object.select_by_type(extend=False, type="EMPTY")
            bpy.ops.object.select_by_type(extend=True, type="MESH")
        # INVERT 는 현재 사용되지 않음
        elif self.action == "DESELECT" or self.action == "INVERT":
            bpy.ops.object.select_all(action=self.action)

        return {"FINISHED"}


classes = (
    GroupNavigateUpOperator,
    GroupNavigateTopOperator,
    GroupNavigateDownOperator,
    GroupNavigateBottomOperator,
    Acon3dObjectPanel,
    Acon3dGroupNavigationPanel,
    ObjectAllSelectOperator,
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)


## Use State 기록용
## 목적별 탭 분리 기획에서 Use State가 빠지기로 결정돼 주석처리 후 보관하기로 논의됨.
## 노션 문서 : https://www.notion.so/acon3d/Object-Control-d2706235c0334950a70e88081f65333c
# class Acon3dStateUpdateOperator(bpy.types.Operator):
#     """Save newly adjusted state data of the object"""

#     bl_idname = "acon3d.state_update"
#     bl_label = "Update State"
#     bl_translation_context = "*"
#     bl_options = {"REGISTER", "UNDO"}

#     @classmethod
#     def poll(cls, context):
#         return context.selected_objects

#     def execute(self, context):

#         for obj in context.selected_objects:

#             prop = obj.ACON_prop

#             if not prop.use_state:
#                 continue

#             for att in ["location", "rotation_euler", "scale"]:

#                 vector = getattr(obj, att)
#                 setattr(prop.state_end, att, vector)

#         context.object.ACON_prop.state_slider = 1

#         return {"FINISHED"}


# class Acon3dStateActionOperator(bpy.types.Operator):
#     """Move object state"""

#     bl_idname = "acon3d.state_action"
#     bl_label = "Move State"
#     bl_translation_context = "*"
#     bl_options = {"REGISTER", "UNDO"}

#     step: bpy.props.FloatProperty(name="Toggle Mode", default=0.25)

#     def execute(self, context):

#         for obj in context.selected_objects:

#             prop = obj.ACON_prop
#             x = prop.state_slider

#             if x == 1:
#                 x = 0
#             else:
#                 x += self.step

#             x = min(x, 1)
#             prop.state_slider = x

#         return {"FINISHED"}

# class ObjectSubPanel(bpy.types.Panel):
#     bl_parent_id = "ACON_PT_Object_Main"
#     bl_idname = "ACON_PT_Object_Sub"
#     bl_label = "Use State"
#     bl_category = "Style"
#     bl_space_type = "VIEW_3D"
#     bl_region_type = "UI"

#     def draw_header(self, context):
#         if obj := context.object:
#             layout = self.layout
#             layout.active = bool(len(context.selected_objects))
#             layout.enabled = layout.active
#             layout.prop(obj.ACON_prop, "use_state", text="")

#     def draw(self, context):
#         layout = self.layout
#         layout.use_property_split = True
#         layout.use_property_decorate = True

#         if context.selected_objects and context.object:
#             obj = context.object
#             prop = obj.ACON_prop

#             layout.active = prop.use_state and bool(len(context.selected_objects))
#             layout.enabled = layout.active
#             row = layout.row(align=True)
#             row.prop(prop, "state_slider", slider=True)
#             row.operator("acon3d.state_update", text="", icon="FILE_REFRESH")
#         else:
#             row = layout.row()
#             col = row.column()
#             col.scale_x = 3
#             col.separator()
#             col = row.column()
#             col.label(text="No selected object")
