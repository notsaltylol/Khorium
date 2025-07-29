import os
import requests

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
    
    def update_representation_mode(self, vtk_pipeline, mode: str):
        """Update mesh representation mode"""
        actors = [vtk_pipeline.mesh_actor]
        
        # Add other actors if they exist
        if vtk_pipeline.has_generated_mesh and vtk_pipeline.generated_mesh_actor:
            actors.append(vtk_pipeline.generated_mesh_actor)
        if vtk_pipeline.has_default_mesh and vtk_pipeline.default_mesh_actor:
            actors.append(vtk_pipeline.default_mesh_actor)
        
        # Apply representation to all actors
        for actor in actors:
            if mode == "surface":
                actor.GetProperty().SetRepresentationToSurface()
            elif mode == "wireframe":
                actor.GetProperty().SetRepresentationToWireframe()
            elif mode == "points":
                actor.GetProperty().SetRepresentationToPoints()