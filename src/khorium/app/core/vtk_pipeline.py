import os

# Required for rendering initialization, not necessary for
# local rendering, but doesn't hurt to include it
import vtkmodules.vtkRenderingOpenGL2  # noqa: F401
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkFiltersCore import vtkContourFilter

# Required for interactor initialization
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleSwitch  # noqa: F401
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader
from vtkmodules.vtkIOLegacy import vtkUnstructuredGridReader
from vtkmodules.vtkIOGeometry import vtkSTLReader
from vtkmodules.vtkRenderingAnnotation import vtkCubeAxesActor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkDataSetMapper,
    vtkRenderer,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
)

from khorium.app.core.constants import CURRENT_DIRECTORY


class VtkPipeline:
    def _create_reader(self, file_path):
        """Create appropriate VTK reader based on file extension"""
        if file_path.lower().endswith('.vtu'):
            return vtkXMLUnstructuredGridReader()
        elif file_path.lower().endswith('.vtk'):
            return vtkUnstructuredGridReader()
        elif file_path.lower().endswith('.stl'):
            return vtkSTLReader()
        else:
            # Default to XML reader
            return vtkXMLUnstructuredGridReader()

    def __init__(self):
        # Create renderer, render window, and interactor
        self.renderer = vtkRenderer()
        self.renderer.SetBackground(1.0, 1.0, 1.0)  # Set background to white
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)

        self.renderWindowInteractor = vtkRenderWindowInteractor()
        self.renderWindowInteractor.SetRenderWindow(self.renderWindow)
        self.renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        
        # Track generated mesh actors separately
        self.generated_mesh_reader = None
        self.generated_mesh_mapper = None
        self.generated_mesh_actor = None
        self.has_generated_mesh = False
        
        # Track default fallback mesh
        self.default_mesh_reader = None
        self.default_mesh_mapper = None
        self.default_mesh_actor = None
        self.has_default_mesh = False
        
        # Track STL mesh actors separately
        self.stl_mesh_reader = None
        self.stl_mesh_mapper = None
        self.stl_mesh_actor = None
        self.has_stl_mesh = False
        self.current_stl_file = None

        # Read Data
        initial_file = os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
        self.reader = self._create_reader(initial_file)
        self.reader.SetFileName(initial_file)
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

        # Mesh: Set solid pastel blue color
        self.mesh_mapper.SetScalarVisibility(False)  # Disable scalar coloring
        self.mesh_actor.GetProperty().SetColor(0.7, 0.8, 1.0)  # Pastel blue color

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

        # Contour: Set solid pastel blue color
        self.contour_mapper.SetScalarVisibility(False)  # Disable scalar coloring
        self.contour_actor.GetProperty().SetColor(0.7, 0.8, 1.0)  # Pastel blue color

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
        self.cube_axes.SetVisibility(True)  # Ensure axes are visible
        
        # Set axes colors to dark gray for visibility against white background
        self.cube_axes.GetXAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
        self.cube_axes.GetYAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
        self.cube_axes.GetZAxesLinesProperty().SetColor(0.3, 0.3, 0.3)
        self.cube_axes.GetXAxesGridlinesProperty().SetColor(0.5, 0.5, 0.5)
        self.cube_axes.GetYAxesGridlinesProperty().SetColor(0.5, 0.5, 0.5)
        self.cube_axes.GetZAxesGridlinesProperty().SetColor(0.5, 0.5, 0.5)
        
        # Set label colors to dark for visibility
        self.cube_axes.SetXAxisLabelVisibility(True)
        self.cube_axes.SetYAxisLabelVisibility(True)
        self.cube_axes.SetZAxisLabelVisibility(True)
        self.cube_axes.SetXAxisVisibility(True)
        self.cube_axes.SetYAxisVisibility(True)
        self.cube_axes.SetZAxisVisibility(True)

        self.renderer.ResetCamera()
        
        # Load default fallback mesh
        self._load_default_mesh()

    def _setup_default_pipeline(self):
        """Setup a minimal pipeline when VTK file cannot be read"""
        # Create empty/default mesh mapper and actor
        self.mesh_mapper = vtkDataSetMapper()
        self.mesh_actor = vtkActor()
        self.mesh_actor.SetMapper(self.mesh_mapper)
        self.renderer.AddActor(self.mesh_actor)

        # Create empty contour filter and mapper
        self.contour = vtkContourFilter()
        self.contour_mapper = vtkDataSetMapper()
        self.contour_actor = vtkActor()
        self.contour_actor.SetMapper(self.contour_mapper)
        self.renderer.AddActor(self.contour_actor)

        # Create cube axes
        self.cube_axes = vtkCubeAxesActor()
        self.renderer.AddActor(self.cube_axes)
        self.cube_axes.SetCamera(self.renderer.GetActiveCamera())

        # Set default contour value
        self.contour_value = 0.5

        self.renderer.ResetCamera()
    
    def _load_default_mesh(self):
        """Load default fallback mesh (cad_000_mesh.vtk)"""
        default_mesh_path = os.path.join(CURRENT_DIRECTORY, "cad_000_mesh.vtk")
        
        if not os.path.exists(default_mesh_path):
            print(f">>> VTK Pipeline: Default mesh file not found: {default_mesh_path}")
            return False
            
        print(f">>> VTK Pipeline: Loading default mesh from {default_mesh_path}")
        
        try:
            # Create mesh reader and pipeline
            self.default_mesh_reader = self._create_reader(default_mesh_path)
            self.default_mesh_mapper = vtkDataSetMapper()
            self.default_mesh_actor = vtkActor()
            self.default_mesh_actor.SetMapper(self.default_mesh_mapper)
            
            # Update reader with file
            self.default_mesh_reader.SetFileName(default_mesh_path)
            self.default_mesh_reader.Update()
            self.default_mesh_mapper.SetInputConnection(self.default_mesh_reader.GetOutputPort())
            
            # Style the mesh (wireframe with green color to differentiate from generated mesh)
            self.default_mesh_actor.GetProperty().SetRepresentationToWireframe()
            self.default_mesh_actor.GetProperty().SetColor(0.0, 1.0, 0.0)  # Green color
            self.default_mesh_actor.GetProperty().SetLineWidth(2)
            
            # Add to renderer but keep hidden initially
            self.renderer.AddActor(self.default_mesh_actor)
            self.default_mesh_actor.SetVisibility(False)
            
            self.has_default_mesh = True
            print(">>> VTK Pipeline: Default mesh loaded successfully")
            return True
            
        except Exception as e:
            print(f">>> VTK Pipeline: Error loading default mesh: {e}")
            return False

    def load_file(self, file_path, is_generated_mesh=False):
        """Load a new VTU, VTK, or STL file and update the pipeline"""
        if file_path.lower().endswith('.stl'):
            return self._load_stl_file(file_path)
        elif is_generated_mesh:
            return self._load_generated_mesh(file_path)
        else:
            return self._load_original_data(file_path)
    
    def _load_original_data(self, file_path):
        """Load original VTU data"""
        # Hide STL mesh if it was previously loaded
        if self.has_stl_mesh and self.stl_mesh_actor:
            self.stl_mesh_actor.SetVisibility(False)
            self.has_stl_mesh = False
            print(">>> VTK Pipeline: STL mesh hidden for VTU file loading")
        
        # Show VTU-based visualization elements
        self.mesh_actor.SetVisibility(True)
        self.contour_actor.SetVisibility(True)
        
        # Create appropriate reader for the file type
        current_reader_type = type(self.reader)
        new_reader = self._create_reader(file_path)
        
        # If reader type changed, we need to reconnect the pipeline
        if type(new_reader) != current_reader_type:
            self.reader = new_reader
            # Reconnect mesh mapper
            self.mesh_mapper.SetInputConnection(self.reader.GetOutputPort())
            # Reconnect contour filter
            self.contour.SetInputConnection(self.reader.GetOutputPort())
        
        # Update the reader with new file
        self.reader.SetFileName(file_path)
        self.reader.Modified()  # Force reader to recognize file changes

        # Try to read the file with error handling
        try:
            self.reader.Update()
        except Exception as e:
            print(f">>> VTK Pipeline: Error reading VTU file {file_path}: {e}")
            return False

        # Extract new Array/Field information
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
                if array is None:
                    continue
                array_range = array.GetRange()
                self.dataset_arrays.append(
                    {
                        "text": array.GetName(),
                        "value": i,
                        "range": list(array_range),
                        "type": association,
                    }
                )

        # Update default array and ranges if data exists
        if self.dataset_arrays:
            default_array = self.dataset_arrays[0]
            self.default_min, self.default_max = default_array.get("range")

            # Update mesh mapper with new data
            self.mesh_mapper.SelectColorArray(default_array.get("text"))
            self.mesh_mapper.GetLookupTable().SetRange(
                self.default_min, self.default_max
            )
            if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
                self.mesh_mapper.SetScalarModeToUsePointFieldData()
            else:
                self.mesh_mapper.SetScalarModeToUseCellFieldData()

            # Update contour with new data
            self.contour_value = 0.5 * (self.default_max + self.default_min)
            self.contour.SetInputArrayToProcess(
                0, 0, 0, default_array.get("type"), default_array.get("text")
            )
            self.contour.SetValue(0, self.contour_value)

            # Update contour mapper
            self.contour_mapper.SelectColorArray(default_array.get("text"))
            self.contour_mapper.GetLookupTable().SetRange(
                self.default_min, self.default_max
            )
            if default_array.get("type") == vtkDataObject.FIELD_ASSOCIATION_POINTS:
                self.contour_mapper.SetScalarModeToUsePointFieldData()
            else:
                self.contour_mapper.SetScalarModeToUseCellFieldData()

            # Update cube axes bounds
            self.cube_axes.SetBounds(self.mesh_actor.GetBounds())

            # Reset camera to fit new data
            self.renderer.ResetCamera()

            print(
                f">>> VTK Pipeline: Loaded new file {file_path} with {len(self.dataset_arrays)} arrays"
            )
            return True
        print(f">>> VTK Pipeline: No readable arrays found in {file_path}")
        return False
    
    def _load_generated_mesh(self, file_path):
        """Load generated mesh file (VTK format)"""
        print(f">>> VTK Pipeline: Loading generated mesh from {file_path}")
        
        # Create mesh reader and pipeline if not exists
        if self.generated_mesh_reader is None:
            self.generated_mesh_reader = self._create_reader(file_path)
            self.generated_mesh_mapper = vtkDataSetMapper()
            self.generated_mesh_actor = vtkActor()
            self.generated_mesh_actor.SetMapper(self.generated_mesh_mapper)
            
            # Style the mesh differently (wireframe with different color)
            self.generated_mesh_actor.GetProperty().SetRepresentationToWireframe()
            self.generated_mesh_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Red color
            self.generated_mesh_actor.GetProperty().SetLineWidth(2)
            
            # Add to renderer but keep hidden initially
            self.renderer.AddActor(self.generated_mesh_actor)
            self.generated_mesh_actor.SetVisibility(False)
        
        # Update reader with new file
        self.generated_mesh_reader.SetFileName(file_path)
        self.generated_mesh_reader.Modified()
        
        try:
            self.generated_mesh_reader.Update()
            self.generated_mesh_mapper.SetInputConnection(self.generated_mesh_reader.GetOutputPort())
            self.has_generated_mesh = True
            
            # Hide default mesh when generated mesh is loaded
            if self.has_default_mesh and self.default_mesh_actor:
                self.default_mesh_actor.SetVisibility(False)
                
            print(">>> VTK Pipeline: Generated mesh loaded successfully")
            return True
        except Exception as e:
            print(f">>> VTK Pipeline: Error loading generated mesh: {e}")
            return False
    
    def _load_stl_file(self, file_path):
        """Load STL file and update the pipeline"""
        print(f">>> VTK Pipeline: Loading STL file from {file_path}")
        
        # Create STL mesh reader and pipeline if not exists
        if self.stl_mesh_reader is None:
            self.stl_mesh_reader = vtkSTLReader()
            self.stl_mesh_mapper = vtkDataSetMapper()
            self.stl_mesh_actor = vtkActor()
            self.stl_mesh_actor.SetMapper(self.stl_mesh_mapper)
            
            # Style the STL mesh with default surface properties
            self.stl_mesh_actor.GetProperty().SetRepresentationToSurface()
            self.stl_mesh_actor.GetProperty().SetColor(0.8, 0.8, 0.9)  # Light blue color
            self.stl_mesh_actor.GetProperty().SetOpacity(1.0)
            
            # Add to renderer
            self.renderer.AddActor(self.stl_mesh_actor)
        
        # Update reader with new file
        self.stl_mesh_reader.SetFileName(file_path)
        self.stl_mesh_reader.Modified()
        
        try:
            self.stl_mesh_reader.Update()
            self.stl_mesh_mapper.SetInputConnection(self.stl_mesh_reader.GetOutputPort())
            
            # STL files don't have scalar data, so disable scalar coloring
            self.stl_mesh_mapper.SetScalarVisibility(False)
            
            self.has_stl_mesh = True
            self.current_stl_file = file_path
            
            # Hide other mesh types when STL is loaded
            if self.has_generated_mesh and self.generated_mesh_actor:
                self.generated_mesh_actor.SetVisibility(False)
            if self.has_default_mesh and self.default_mesh_actor:
                self.default_mesh_actor.SetVisibility(False)
            
            # Hide VTU-based visualization elements since STL doesn't have scalar fields
            self.mesh_actor.SetVisibility(False)
            self.contour_actor.SetVisibility(False)
            
            # Update cube axes bounds for STL geometry
            self.cube_axes.SetBounds(self.stl_mesh_actor.GetBounds())
            
            # Reset camera to fit STL data
            self.renderer.ResetCamera()
            
            print(">>> VTK Pipeline: STL file loaded successfully")
            return True
        except Exception as e:
            print(f">>> VTK Pipeline: Error loading STL file: {e}")
            return False
    
    def set_mesh_visibility(self, visible):
        """Toggle visibility of mesh (generated, default, or STL)"""
        print(f">>> VTK Pipeline: [DEBUG] set_mesh_visibility called with visible={visible}")
        print(f">>> VTK Pipeline: [DEBUG] has_generated_mesh={self.has_generated_mesh}, has_default_mesh={self.has_default_mesh}, has_stl_mesh={self.has_stl_mesh}")
        
        # For STL files, the mesh visibility doesn't apply since STL is the primary content
        if self.has_stl_mesh:
            print(">>> VTK Pipeline: STL mesh is already visible (no additional mesh to toggle)")
            return
        
        if self.has_generated_mesh and self.generated_mesh_actor:
            # Show/hide generated mesh
            self.generated_mesh_actor.SetVisibility(visible)
            current_visibility = self.generated_mesh_actor.GetVisibility()
            print(f">>> VTK Pipeline: [DEBUG] Generated mesh actor visibility set to {visible}, current={current_visibility}")
            
            # Ensure default mesh is hidden when showing generated mesh
            if visible and self.has_default_mesh and self.default_mesh_actor:
                self.default_mesh_actor.SetVisibility(False)
                print(f">>> VTK Pipeline: [DEBUG] Default mesh hidden when showing generated mesh")
            print(f">>> VTK Pipeline: Generated mesh visibility set to {visible}")
        elif self.has_default_mesh and self.default_mesh_actor:
            # Fallback to default mesh
            self.default_mesh_actor.SetVisibility(visible)
            current_visibility = self.default_mesh_actor.GetVisibility()
            print(f">>> VTK Pipeline: [DEBUG] Default mesh actor visibility set to {visible}, current={current_visibility}")
            print(f">>> VTK Pipeline: Default mesh visibility set to {visible} (fallback)")
        else:
            print(">>> VTK Pipeline: [DEBUG] No mesh available to toggle - check if mesh was loaded properly")
            
    def has_mesh(self):
        """Check if any mesh (generated, default, or STL) is available"""
        return self.has_generated_mesh or self.has_default_mesh or self.has_stl_mesh
