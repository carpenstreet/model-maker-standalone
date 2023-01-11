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


import bpy


def setup_snip_compositor(
    node_left=None, node_right=None, snip_layer=None, shade_image=None
):

    if not node_left or not node_right:
        node_left, node_right = clear_compositor()

    context = bpy.context
    scene = context.scene

    tree = scene.node_tree
    nodes = tree.nodes

    node_rlayer = nodes.new("CompositorNodeRLayers")
    node_rlayer.layer = snip_layer.name

    node_setAlpha = nodes.new("CompositorNodeSetAlpha")
    tree.links.new(node_left, node_setAlpha.inputs[0])
    tree.links.new(node_rlayer.outputs[1], node_setAlpha.inputs[1])
    tree.links.new(node_setAlpha.outputs[0], node_right)


def setup_background_images_compositor(node_left=None, node_right=None, scene=None):

    if not node_left or not node_right:
        node_left, node_right = clear_compositor()

    context = bpy.context
    if not scene:
        scene = context.scene

    tree = scene.node_tree
    nodes = tree.nodes

    cam = scene.camera.data
    background_images = cam.background_images
    toggle_texture = context.scene.ACON_prop.toggle_texture

    if not cam.show_background_images or not toggle_texture:
        return

    for background_image in reversed(background_images):

        image = background_image.image

        # 배경 이미지를 추가하지 않았을 때는 알림을 표시하지 않습니다.
        if image is None:
            continue

        # 배경 이미지에 사용된 파일을 찾을 수 없으면 알림을 표시합니다.
        if 0 in image.size:
            bpy.ops.acon3d.alert(
                "INVOKE_DEFAULT",
                title="Check Background Image File",
                message_1="Failed to load background image file:",
                message_2=f"{image.name}",
            )
            continue

        node_image = nodes.new("CompositorNodeImage")
        node_image.image = image

        node_setAlpha_1 = nodes.new("CompositorNodeSetAlpha")
        tree.links.new(node_image.outputs[0], node_setAlpha_1.inputs[0])
        tree.links.new(node_image.outputs[1], node_setAlpha_1.inputs[1])

        node_setAlpha_2 = nodes.new("CompositorNodeSetAlpha")
        node_setAlpha_2.inputs[1].default_value = background_image.alpha
        tree.links.new(node_setAlpha_1.outputs[0], node_setAlpha_2.inputs[0])

        node_scale = nodes.new("CompositorNodeScale")
        node_scale.space = "RENDER_SIZE"
        node_scale.frame_method = background_image.frame_method
        tree.links.new(node_setAlpha_2.outputs[0], node_scale.inputs[0])

        node_conditional = node_scale

        if background_image.use_flip_x or background_image.use_flip_y:
            node_conditional = nodes.new("CompositorNodeFlip")

            if background_image.use_flip_x and background_image.use_flip_y:
                node_conditional.axis = "XY"
            elif background_image.use_flip_y:
                node_conditional.axis = "Y"

            tree.links.new(node_scale.outputs[0], node_conditional.inputs[0])

        node_transform = nodes.new("CompositorNodeTransform")

        node_transform.inputs[1].default_value = (
            background_image.offset[0] * scene.render.resolution_x
        )
        node_transform.inputs[3].default_value = -1 * background_image.rotation
        node_transform.inputs[4].default_value = background_image.scale
        tree.links.new(node_conditional.outputs[0], node_transform.inputs[0])

        node_translate = nodes.new("CompositorNodeTranslate")
        node_translate.use_relative = True

        render_r = scene.render.resolution_y / scene.render.resolution_x
        image_r = image.size[1] / image.size[0]
        background_r = render_r / image_r
        node_translate.inputs[2].default_value = (
            background_image.offset[1] / background_r
        )
        tree.links.new(node_transform.outputs[0], node_translate.inputs[0])

        node_alphaOver = nodes.new("CompositorNodeAlphaOver")
        tree.links.new(node_alphaOver.outputs[0], node_right)

        if background_image.display_depth == "BACK":
            tree.links.new(node_translate.outputs[0], node_alphaOver.inputs[1])
            tree.links.new(node_left, node_alphaOver.inputs[2])
            node_left = node_alphaOver.outputs[0]
        else:
            tree.links.new(node_translate.outputs[0], node_alphaOver.inputs[2])
            tree.links.new(node_left, node_alphaOver.inputs[1])
            node_right = node_alphaOver.inputs[1]


def clear_compositor(scene=None):

    context = bpy.context

    if not scene:
        scene = context.scene

    scene.render.film_transparent = True
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes

    for node in nodes:
        nodes.remove(node)

    node_composite = nodes.new("CompositorNodeComposite")
    node_rlayer = nodes.new("CompositorNodeRLayers")

    node_left = node_rlayer.outputs[0]
    node_right = node_composite.inputs[0]
    tree.links.new(node_left, node_right)

    return node_left, node_right


def match_object_visibility():
    for obj in bpy.data.objects:
        if obj.hide_get():
            obj.hide_render = True
