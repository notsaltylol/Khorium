import os
import tempfile
import requests
import gmsh

from khorium.app.core.constants import CURRENT_DIRECTORY
from khorium.app.config import MESH_GENERATE_API


class MeshService:
    """Service for handling mesh generation and related operations"""
    
    def __init__(self):
        pass
    
    def generate_mesh_from_file(self, file_path: str) -> str | None:
        """
        Generate mesh from VTU file via API
        
        Args:
            file_path: Path to the VTU file to process
            
        Returns:
            Path to generated mesh file if successful, None otherwise
        """
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            print(f">>> MESH_SERVICE: No valid VTU file at {file_path}")
            return None
            
        print(f">>> MESH_SERVICE: Calling mesh generation API with file: {file_path}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
                
                print(f">>> MESH_SERVICE: Sending request to {MESH_GENERATE_API}")
                response = requests.post(MESH_GENERATE_API, files=files, timeout=30)
                
                if response.status_code == 200:
                    # Save the VTK mesh file
                    mesh_file_path = os.path.join(CURRENT_DIRECTORY, "generated_mesh.vtk")
                    with open(mesh_file_path, 'wb') as mesh_file:
                        mesh_file.write(response.content)
                    
                    print(f">>> MESH_SERVICE: Mesh saved to {mesh_file_path}")
                    return mesh_file_path
                else:
                    print(f">>> MESH_SERVICE: API request failed with status {response.status_code}: {response.text}")
                    return None
                    
        except requests.exceptions.RequestException as e:
            print(f">>> MESH_SERVICE: API request error: {e}")
            return None
        except Exception as e:
            print(f">>> MESH_SERVICE: Error generating mesh: {e}")
            return None
    
    def generate_mesh_with_gmsh(self, vtk_pipeline) -> str | None:
        """
        Generate mesh from currently loaded 3D model using GMSH
        
        Args:
            vtk_pipeline: VTK pipeline containing the current 3D model
            
        Returns:
            Path to generated mesh file if successful, None otherwise
        """
        print(">>> MESH_SERVICE: Starting GMSH mesh generation")
        
        # Determine what type of model is currently loaded
        current_model_info = self._get_current_model_info(vtk_pipeline)
        if not current_model_info:
            print(">>> MESH_SERVICE: No valid 3D model loaded for mesh generation")
            return None
        
        model_type, model_data = current_model_info
        print(f">>> MESH_SERVICE: Processing {model_type} model for mesh generation")
        
        try:
            # Initialize GMSH
            gmsh.initialize()
            gmsh.model.add("mesh_generation")
            
            # Process based on model type
            if model_type == "STL":
                temp_stl_file = self._export_stl_to_temp_file(model_data)
                if not temp_stl_file:
                    return None
                success = self._generate_mesh_from_stl(temp_stl_file)
            elif model_type == "VTU":
                temp_stl_file = self._convert_vtu_to_stl(model_data)
                if not temp_stl_file:
                    return None
                success = self._generate_mesh_from_stl(temp_stl_file)
            else:
                print(f">>> MESH_SERVICE: Unsupported model type: {model_type}")
                return None
            
            if not success:
                return None
            
            # Export mesh as VTK
            output_file = os.path.join(CURRENT_DIRECTORY, "gmsh_generated_mesh.vtk")
            gmsh.write(output_file)
            
            # Verify the file was created and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f">>> MESH_SERVICE: GMSH mesh saved to {output_file} (size: {os.path.getsize(output_file)} bytes)")
                return output_file
            else:
                print(f">>> MESH_SERVICE: GMSH mesh file was not created properly")
                return None
            
        except Exception as e:
            print(f">>> MESH_SERVICE: Error in GMSH mesh generation: {e}")
            return None
        finally:
            # Clean up GMSH
            try:
                gmsh.finalize()
            except:
                pass
    
    def _get_current_model_info(self, vtk_pipeline):
        """Get information about the currently loaded model"""
        # Check STL mesh first (most recent upload type)
        if vtk_pipeline.has_stl_mesh and vtk_pipeline.stl_mesh_actor:
            if vtk_pipeline.stl_mesh_actor.GetVisibility():
                return ("STL", vtk_pipeline.stl_mesh_actor)
        
        # Check main VTU mesh
        if vtk_pipeline.mesh_actor and vtk_pipeline.mesh_actor.GetVisibility():
            if hasattr(vtk_pipeline, 'reader') and vtk_pipeline.reader:
                return ("VTU", vtk_pipeline.reader)
        
        # Check if we have any STL data even if not visible
        if vtk_pipeline.has_stl_mesh and vtk_pipeline.stl_mesh_actor:
            return ("STL", vtk_pipeline.stl_mesh_actor)
        
        # Check if we have any VTU data even if not visible
        if hasattr(vtk_pipeline, 'reader') and vtk_pipeline.reader:
            return ("VTU", vtk_pipeline.reader)
        
        return None
    
    def _export_stl_to_temp_file(self, stl_actor):
        """Export STL actor data to temporary STL file"""
        try:
            from vtkmodules.vtkIOGeometry import vtkSTLWriter
            
            # Get the polydata from the actor
            mapper = stl_actor.GetMapper()
            if not mapper:
                print(">>> MESH_SERVICE: No mapper found for STL actor")
                return None
            
            polydata = mapper.GetInput()
            if not polydata:
                print(">>> MESH_SERVICE: No polydata found for STL actor")
                return None
            
            # Write to temporary STL file
            temp_file = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
            temp_file.close()
            
            writer = vtkSTLWriter()
            writer.SetFileName(temp_file.name)
            writer.SetInputData(polydata)
            writer.Write()
            
            print(f">>> MESH_SERVICE: STL data exported to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f">>> MESH_SERVICE: Error exporting STL: {e}")
            return None
    
    def _convert_vtu_to_stl(self, vtu_reader):
        """Convert VTU data to STL format for GMSH processing"""
        try:
            from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
            from vtkmodules.vtkIOGeometry import vtkSTLWriter
            
            # Extract surface geometry from VTU
            geometry_filter = vtkGeometryFilter()
            geometry_filter.SetInputConnection(vtu_reader.GetOutputPort())
            geometry_filter.Update()
            
            # Write to temporary STL file
            temp_file = tempfile.NamedTemporaryFile(suffix=".stl", delete=False)
            temp_file.close()
            
            writer = vtkSTLWriter()
            writer.SetFileName(temp_file.name)
            writer.SetInputConnection(geometry_filter.GetOutputPort())
            writer.Write()
            
            print(f">>> MESH_SERVICE: VTU surface extracted to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f">>> MESH_SERVICE: Error converting VTU to STL: {e}")
            return None
    
    def _generate_mesh_from_stl(self, stl_file_path):
        """Generate 3D tetrahedral mesh from STL file using GMSH"""
        try:
            # Import STL geometry
            gmsh.merge(stl_file_path)
            
            # Get model bounds to calculate appropriate mesh size
            bbox = gmsh.model.getBoundingBox(-1, -1)
            dx = bbox[3] - bbox[0]
            dy = bbox[4] - bbox[1] 
            dz = bbox[5] - bbox[2]
            max_dim = max(dx, dy, dz)
            
            # Set mesh size based on model dimensions
            mesh_size = max_dim / 20  # Reasonable default
            gmsh.model.mesh.setSize(gmsh.model.getEntities(0), mesh_size)
            
            print(f">>> MESH_SERVICE: Model bounds: {bbox}")
            print(f">>> MESH_SERVICE: Using mesh size: {mesh_size}")
            
            # Create surface mesh first
            gmsh.model.mesh.generate(2)
            
            # Create volume from surface
            surfaces = gmsh.model.getEntities(2)
            if surfaces:
                try:
                    # Create a surface loop and volume
                    surface_tags = [s[1] for s in surfaces]
                    surface_loop_tag = gmsh.model.geo.addSurfaceLoop(surface_tags)
                    volume_tag = gmsh.model.geo.addVolume([surface_loop_tag])
                    gmsh.model.geo.synchronize()
                    
                    # Generate 3D tetrahedral mesh
                    gmsh.model.mesh.generate(3)
                    print(">>> MESH_SERVICE: 3D tetrahedral mesh generated successfully")
                except Exception as e:
                    print(f">>> MESH_SERVICE: Failed to create 3D mesh, using 2D surface mesh: {e}")
                    # If 3D mesh fails, at least we have the 2D surface mesh
            else:
                print(">>> MESH_SERVICE: No surfaces found, using 2D surface mesh only")
            
            # Count mesh elements for debugging
            try:
                nodes = gmsh.model.mesh.getNodes()
                elements = gmsh.model.mesh.getElements()
                print(f">>> MESH_SERVICE: Generated mesh has {len(nodes[0])} nodes and {len(elements[1])} element groups")
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f">>> MESH_SERVICE: Error in GMSH mesh generation: {e}")
            return False
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(stl_file_path):
                    os.unlink(stl_file_path)
            except:
                pass
    
    def update_mesh_color(self, vtk_pipeline, color: str):
        """Update mesh color based on string value"""
        color_map = {
            "blue": (0.7, 0.8, 1.0),
            "red": (1.0, 0.3, 0.3),
            "green": (0.3, 1.0, 0.3),
            "white": (1.0, 1.0, 1.0)
        }
        
        rgb = color_map.get(color, (0.7, 0.8, 1.0))  # Default to blue
        
        # Update main mesh actor
        vtk_pipeline.mesh_actor.GetProperty().SetColor(*rgb)
        
        # Update generated mesh actor if it exists
        if vtk_pipeline.has_generated_mesh and vtk_pipeline.generated_mesh_actor:
            vtk_pipeline.generated_mesh_actor.GetProperty().SetColor(*rgb)
            
        # Update default mesh actor if it exists
        if vtk_pipeline.has_default_mesh and vtk_pipeline.default_mesh_actor:
            vtk_pipeline.default_mesh_actor.GetProperty().SetColor(*rgb)
            
        # Update STL mesh actor if it exists
        if vtk_pipeline.has_stl_mesh and vtk_pipeline.stl_mesh_actor:
            vtk_pipeline.stl_mesh_actor.GetProperty().SetColor(*rgb)
    
    def update_representation_mode(self, vtk_pipeline, mode: str):
        """Update mesh representation mode"""
        actors = [vtk_pipeline.mesh_actor]
        
        # Add other actors if they exist
        if vtk_pipeline.has_generated_mesh and vtk_pipeline.generated_mesh_actor:
            actors.append(vtk_pipeline.generated_mesh_actor)
        if vtk_pipeline.has_default_mesh and vtk_pipeline.default_mesh_actor:
            actors.append(vtk_pipeline.default_mesh_actor)
        if vtk_pipeline.has_stl_mesh and vtk_pipeline.stl_mesh_actor:
            actors.append(vtk_pipeline.stl_mesh_actor)
        
        # Apply representation to all actors
        for actor in actors:
            if mode == "surface":
                actor.GetProperty().SetRepresentationToSurface()
            elif mode == "wireframe":
                actor.GetProperty().SetRepresentationToWireframe()
            elif mode == "points":
                actor.GetProperty().SetRepresentationToPoints()
    
    def set_mesh_size_factor(self, factor: float):
        """
        Set the global mesh size factor for GMSH mesh generation
        
        Args:
            factor: Mesh size factor (typically between 0.1 and 10.0)
                   - Values < 1.0 create finer meshes
                   - Values > 1.0 create coarser meshes
                   - Default is 1.0
        """
        try:
            # Clamp factor to reasonable range
            factor = max(0.01, min(100.0, factor))
            
            # Set the global mesh size factor option in GMSH
            gmsh.option.setNumber("Mesh.MeshSizeFactor", factor)
            
            print(f">>> MESH_SERVICE: Mesh size factor set to {factor}")
            
        except Exception as e:
            print(f">>> MESH_SERVICE: Error setting mesh size factor: {e}")