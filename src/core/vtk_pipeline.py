# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import os

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

from core.constants import CURRENT_DIRECTORY


class VtkPipeline:
    def __init__(self):

        # Create renderer, render window, and interactor
        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor = vtkRenderWindowInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)
        self.renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        # Read Data
        self.reader = vtkXMLUnstructuredGridReader()
        self.reader.SetFileName(
            os.path.join(CURRENT_DIRECTORY, "../../data/disk_out_ref.vtu")
        )
        self.reader.Update()

        # Extract Array/Field information
        self.dataset_arrays = []
        fields = [
            (
                self.reader.GetOutput().GetPointData(),
                vtkDataObject.FIELD_ASSOCIATION_POINTS,
            ),
            (
                self.reader.GetOutput().GetCellData(),
                vtkDataObject.FIELD_ASSOCIATION_CELLS,
            ),
        ]
        for field in fields:
            field_arrays, association = field
            for i in range(field_arrays.GetNumberOfArrays()):
                array = field_arrays.GetArray(i)
                array_range = array.GetRange()
                self.dataset_arrays.append(
                    {
                        "text": array.GetName(),
                        "value": i,
                        "range": list(array_range),
                        "type": association,
                    }
                )
        default_array = self.dataset_arrays[0]
        self.default_min, self.default_max = default_array.get("range")

        # Mesh
        self.mesh_mapper = vtkDataSetMapper()
        self.mesh_mapper.SetInputConnection(self.reader.GetOutputPort())
        self.mesh_actor = vtkActor()
        self.mesh_actor.SetMapper(self.mesh_mapper)
        self.renderer.AddActor(self.mesh_actor)

        # Mesh: Setup default representation to surface
        self.mesh_actor.GetProperty().SetRepresentationToSurface()
        self.mesh_actor.GetProperty().SetPointSize(1)
        self.mesh_actor.GetProperty().EdgeVisibilityOff()

        # Mesh: Apply rainbow color map
        mesh_lut = self.mesh_mapper.GetLookupTable()
        mesh_lut.SetHueRange(0.666, 0.0)
        mesh_lut.SetSaturationRange(1.0, 1.0)
        mesh_lut.SetValueRange(1.0, 1.0)
        mesh_lut.Build()

        # Mesh: Color by default array
        self.mesh_mapper.SelectColorArray(default_array.get("text"))
        self.mesh_mapper.GetLookupTable().SetRange(self.default_min, self.default_max)
        if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
            self.mesh_mapper.SetScalarModeToUsePointFieldData()
        else:
            self.mesh_mapper.SetScalarModeToUseCellFieldData()
        self.mesh_mapper.SetScalarVisibility(True)
        self.mesh_mapper.SetUseLookupTableScalarRange(True)

        # Contour
        self.contour = vtkContourFilter()
        self.contour.SetInputConnection(self.reader.GetOutputPort())
        self.contour_mapper = vtkDataSetMapper()
        self.contour_mapper.SetInputConnection(self.contour.GetOutputPort())
        self.contour_actor = vtkActor()
        self.contour_actor.SetMapper(self.contour_mapper)
        self.renderer.AddActor(self.contour_actor)

        # Contour: ContourBy default array
        self.contour_value = 0.5 * (self.default_max + self.default_min)
        self.contour.SetInputArrayToProcess(
            0, 0, 0, default_array.get("type"), default_array.get("text")
        )
        self.contour.SetValue(0, self.contour_value)

        # Contour: Setup default representation to surface
        self.contour_actor.GetProperty().SetRepresentationToSurface()
        self.contour_actor.GetProperty().SetPointSize(1)
        self.contour_actor.GetProperty().EdgeVisibilityOff()

        # Contour: Apply rainbow color map
        contour_lut = self.contour_mapper.GetLookupTable()
        contour_lut.SetHueRange(0.666, 0.0)
        contour_lut.SetSaturationRange(1.0, 1.0)
        contour_lut.SetValueRange(1.0, 1.0)
        contour_lut.Build()

        # Contour: Color by default array
        self.contour_mapper.SelectColorArray(default_array.get("text"))
        self.contour_mapper.GetLookupTable().SetRange(
            self.default_min, self.default_max
        )
        if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
            self.contour_mapper.SetScalarModeToUsePointFieldData()
        else:
            self.contour_mapper.SetScalarModeToUseCellFieldData()
        self.contour_mapper.SetScalarVisibility(True)
        self.contour_mapper.SetUseLookupTableScalarRange(True)

        # Cube Axes
        self.cube_axes = vtkCubeAxesActor()
        self.renderer.AddActor(self.cube_axes)

        # Cube Axes: Boundaries, camera, and styling
        self.cube_axes.SetBounds(self.mesh_actor.GetBounds())
        self.cube_axes.SetCamera(self.renderer.GetActiveCamera())
        self.cube_axes.SetXLabelFormat("%6.1f")
        self.cube_axes.SetYLabelFormat("%6.1f")
        self.cube_axes.SetZLabelFormat("%6.1f")
        self.cube_axes.SetFlyModeToOuterEdges()

        self.renderer.ResetCamera()
