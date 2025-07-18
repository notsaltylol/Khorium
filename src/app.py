import os

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2
from trame.app import get_server
from trame.ui.vuetify import SinglePageWithDrawerLayout
from trame.widgets import trame, vtk, vuetify
from trame_vtk.modules.vtk.serializers import configure_serializer
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkContourFilter

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from core.constants import LookupTable, Representation
from core.vtk_pipeline import VtkPipeline
from ui.components.cards import contour_card, mesh_card  # noqa

# Configure scene encoder
configure_serializer(encode_lut=True, skip_light=True)

vtk_pipeline = VtkPipeline()

# -----------------------------------------------------------------------------
# Trame setup
# -----------------------------------------------------------------------------

server = get_server(client_type="vue2")
state, ctrl = server.state, server.controller

state.setdefault("active_ui", None)

# -----------------------------------------------------------------------------
# Callbacks
# -----------------------------------------------------------------------------


@state.change("cube_axes_visibility")
def update_cube_axes_visibility(cube_axes_visibility, **kwargs):
    vtk_pipeline.cube_axes.SetVisibility(cube_axes_visibility)
    ctrl.view_update()


# Selection Change
def actives_change(ids):
    _id = ids[0]
    if _id == "1":  # Mesh
        state.active_ui = "mesh"
    elif _id == "2":  # Contour
        state.active_ui = "contour"
    else:
        state.active_ui = "nothing"


# Visibility Change
def visibility_change(event):
    _id = event["id"]
    _visibility = event["visible"]

    if _id == "1":  # Mesh
        vtk_pipeline.mesh_actor.SetVisibility(_visibility)
    elif _id == "2":  # Contour
        vtk_pipeline.contour_actor.SetVisibility(_visibility)
    ctrl.view_update()


# Representation Callbacks
def update_representation(actor, mode):
    property = actor.GetProperty()
    if mode == Representation.Points:
        property.SetRepresentationToPoints()
        property.SetPointSize(5)
        property.EdgeVisibilityOff()
    elif mode == Representation.Wireframe:
        property.SetRepresentationToWireframe()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.Surface:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOff()
    elif mode == Representation.SurfaceWithEdges:
        property.SetRepresentationToSurface()
        property.SetPointSize(1)
        property.EdgeVisibilityOn()


@state.change("mesh_representation")
def update_mesh_representation(mesh_representation, **kwargs):
    update_representation(vtk_pipeline.mesh_actor, mesh_representation)
    ctrl.view_update()


@state.change("contour_representation")
def update_contour_representation(contour_representation, **kwargs):
    update_representation(vtk_pipeline.contour_actor, contour_representation)
    ctrl.view_update()


# Color By Callbacks
def color_by_array(actor, array):
    _min, _max = array.get("range")
    mapper = actor.GetMapper()
    mapper.SelectColorArray(array.get("text"))
    mapper.GetLookupTable().SetRange(_min, _max)
    if array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
        vtk_pipeline.mesh_mapper.SetScalarModeToUsePointFieldData()
    else:
        vtk_pipeline.mesh_mapper.SetScalarModeToUseCellFieldData()
    mapper.SetScalarVisibility(True)
    mapper.SetUseLookupTableScalarRange(True)


@state.change("mesh_color_array_idx")
def update_mesh_color_by_name(mesh_color_array_idx, **kwargs):
    array = vtk_pipeline.dataset_arrays[mesh_color_array_idx]
    color_by_array(vtk_pipeline.mesh_actor, array)
    ctrl.view_update()


@state.change("contour_color_array_idx")
def update_contour_color_by_name(contour_color_array_idx, **kwargs):
    array = vtk_pipeline.dataset_arrays[contour_color_array_idx]
    color_by_array(vtk_pipeline.contour_actor, array)
    ctrl.view_update()


# Color Map Callbacks
def use_preset(actor, preset):
    lut = actor.GetMapper().GetLookupTable()
    if preset == LookupTable.Rainbow:
        lut.SetHueRange(0.666, 0.0)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Inverted_Rainbow:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)
    elif preset == LookupTable.Greyscale:
        lut.SetHueRange(0.0, 0.0)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(0.0, 1.0)
    elif preset == LookupTable.Inverted_Greyscale:
        lut.SetHueRange(0.0, 0.666)
        lut.SetSaturationRange(0.0, 0.0)
        lut.SetValueRange(1.0, 0.0)
    lut.Build()


@state.change("mesh_color_preset")
def update_mesh_color_preset(mesh_color_preset, **kwargs):
    use_preset(vtk_pipeline.mesh_actor, mesh_color_preset)
    ctrl.view_update()


@state.change("contour_color_preset")
def update_contour_color_preset(contour_color_preset, **kwargs):
    use_preset(vtk_pipeline.contour_actor, contour_color_preset)
    ctrl.view_update()


# Opacity Callbacks
@state.change("mesh_opacity")
def update_mesh_opacity(mesh_opacity, **kwargs):
    vtk_pipeline.mesh_actor.GetProperty().SetOpacity(mesh_opacity)
    ctrl.view_update()


@state.change("contour_opacity")
def update_contour_opacity(contour_opacity, **kwargs):
    vtk_pipeline.contour_actor.GetProperty().SetOpacity(contour_opacity)
    ctrl.view_update()


# Contour Callbacks
@state.change("contour_by_array_idx")
def update_contour_by(contour_by_array_idx, **kwargs):
    array = vtk_pipeline.dataset_arrays[contour_by_array_idx]
    contour_min, contour_max = array.get("range")
    contour_step = 0.01 * (contour_max - contour_min)
    contour_value = 0.5 * (contour_max + contour_min)
    vtk_pipeline.contour.SetInputArrayToProcess(
        0, 0, 0, array.get("type"), array.get("text")
    )
    vtk_pipeline.contour.SetValue(0, contour_value)

    # Update UI
    state.contour_min = contour_min
    state.contour_max = contour_max
    state.contour_value = contour_value
    state.contour_step = contour_step

    # Update View
    ctrl.view_update()


@state.change("contour_value")
def update_contour_value(contour_value, **kwargs):
    vtk_pipeline.contour.SetValue(0, float(contour_value))
    ctrl.view_update()


# -----------------------------------------------------------------------------
# GUI elements
# -----------------------------------------------------------------------------


def standard_buttons():
    vuetify.VCheckbox(
        v_model=("cube_axes_visibility", True),
        on_icon="mdi-cube-outline",
        off_icon="mdi-cube-off-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model="$vuetify.theme.dark",
        on_icon="mdi-lightbulb-off-outline",
        off_icon="mdi-lightbulb-outline",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    vuetify.VCheckbox(
        v_model=("viewMode", "local"),
        on_icon="mdi-lan-disconnect",
        off_icon="mdi-lan-connect",
        true_value="local",
        false_value="remote",
        classes="mx-1",
        hide_details=True,
        dense=True,
    )
    with vuetify.VBtn(icon=True, click="$refs.view.resetCamera()"):
        vuetify.VIcon("mdi-crop-free")


def pipeline_widget():
    trame.GitTree(
        sources=(
            "pipeline",
            [
                {"id": "1", "parent": "0", "visible": 1, "name": "Mesh"},
                {"id": "2", "parent": "1", "visible": 1, "name": "Contour"},
            ],
        ),
        actives_change=(actives_change, "[$event]"),
        visibility_change=(visibility_change, "[$event]"),
    )


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

with SinglePageWithDrawerLayout(server) as layout:
    layout.title.set_text("Viewer")

    with layout.toolbar:
        # toolbar components
        vuetify.VSpacer()
        vuetify.VDivider(vertical=True, classes="mx-2")
        standard_buttons()

    with layout.drawer as drawer:
        # drawer components
        drawer.width = 325
        pipeline_widget()
        vuetify.VDivider(classes="mb-2")
        mesh_card(dataset_arrays=vtk_pipeline.dataset_arrays)
        contour_card(
            dataset_arrays=vtk_pipeline.dataset_arrays,
            contour_value=vtk_pipeline.contour_value,
            default_min=vtk_pipeline.default_min,
            default_max=vtk_pipeline.default_max,
        )

    with layout.content:
        # content components
        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            # view = vtk.VtkRemoteView(renderWindow, interactive_ratio=1)
            # view = vtk.VtkLocalView(renderWindow)
            view = vtk.VtkRemoteLocalView(
                vtk_pipeline.renderWindow,
                namespace="view",
                mode="local",
                interactive_ratio=1,
            )
            ctrl.view_update = view.update
            ctrl.view_reset_camera = view.reset_camera

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    server.start(host="0.0.0.0", port=10000)
