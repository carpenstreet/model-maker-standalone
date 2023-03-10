# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
# ***** END GPL LICENSE BLOCK *****

set(INC
  ../include
  ../../blenfont
  ../../blenkernel
  ../../blenlib
  ../../blentranslation
  ../../bmesh
  ../../depsgraph
  ../../draw
  ../../gpu
  ../../imbuf
  ../../makesdna
  ../../makesrna
  ../../render
  ../../windowmanager
  ../../../../intern/glew-mx
  ../../../../intern/guardedalloc
  ../../../../intern/mantaflow/extern

  # dna_type_offsets.h
  ${CMAKE_CURRENT_BINARY_DIR}/../../makesdna/intern
)


set(SRC
  drawobject.c
  space_view3d.c
  view3d_buttons.c
  view3d_camera_control.c
  view3d_cursor_snap.c
  view3d_draw.c
  view3d_edit.c
  view3d_gizmo_armature.c
  view3d_gizmo_camera.c
  view3d_gizmo_empty.c
  view3d_gizmo_forcefield.c
  view3d_gizmo_light.c
  view3d_gizmo_navigate.c
  view3d_gizmo_navigate_type.c
  view3d_gizmo_preselect.c
  view3d_gizmo_preselect_type.c
  view3d_gizmo_ruler.c
  view3d_gizmo_tool_generic.c
  view3d_header.c
  view3d_iterators.c
  view3d_navigate_fly.c
  view3d_navigate_walk.c
  view3d_ops.c
  view3d_placement.c
  view3d_project.c
  view3d_select.c
  view3d_snap.c
  view3d_utils.c
  view3d_view.c

  view3d_intern.h
)

set(LIB
  bf_editor_lattice
  bf_editor_mesh
)

if(WITH_PYTHON)
  blender_include_dirs(../../python)
  add_definitions(-DWITH_PYTHON)
endif()


if(WITH_INTERNATIONAL)
  add_definitions(-DWITH_INTERNATIONAL)
endif()

if(WITH_FREESTYLE)
  add_definitions(-DWITH_FREESTYLE)
endif()

if(WITH_XR_OPENXR)
  add_definitions(-DWITH_XR_OPENXR)
endif()

blender_add_lib(bf_editor_space_view3d "${SRC}" "${INC}" "${INC_SYS}" "${LIB}")

# Needed so we can use dna_type_offsets.h for defaults initialization.
add_dependencies(bf_editor_space_view3d bf_dna)
