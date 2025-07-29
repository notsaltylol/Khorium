from trame.decorators import controller

from khorium.app.services.mesh_service import MeshService
from khorium.app.services.file_service import FileService


class MeshController:
    """Controller for mesh generation and visualization operations"""
    
    def __init__(self, app):
        self.app = app
        self.mesh_service = MeshService()
        self.file_service = FileService()
        self._register_controllers()
    
    def _register_controllers(self):
        """Register controller methods with Trame"""
        self.app.ctrl.generate_mesh = self.generate_mesh
    
    @controller.set("generate_mesh")
    def generate_mesh(self):
        """Generate mesh from current VTU file via API"""
        print(">>> MESH_CONTROLLER: Generate Mesh button clicked")
        
        # Get current VTU file
        current_file = self.file_service.get_current_vtu_file()
        
        # Generate mesh via service
        mesh_file_path = self.mesh_service.generate_mesh_from_file(current_file)
        
        if mesh_file_path:
            # Load the generated mesh
            if self.app.vtk_pipeline.load_file(mesh_file_path, is_generated_mesh=True):
                # Update the view
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
                if hasattr(self.app.ctrl, "view_reset_camera"):
                    self.app.ctrl.view_reset_camera()
                
                print(">>> MESH_CONTROLLER: Generated mesh loaded successfully")
            else:
                print(">>> MESH_CONTROLLER: Failed to load generated mesh")
    
    def update_mesh_color(self, color: str):
        """Update mesh color using mesh service"""
        self.mesh_service.update_mesh_color(self.app.vtk_pipeline, color)
    
    def update_representation_mode(self, mode: str):
        """Update mesh representation mode using mesh service"""
        self.mesh_service.update_representation_mode(self.app.vtk_pipeline, mode)