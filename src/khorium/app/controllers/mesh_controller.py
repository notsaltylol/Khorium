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
        self.app.ctrl.generate_mesh = self.generate_mesh_gmsh
    
    @controller.set("generate_mesh")
    def generate_mesh_gmsh(self):
        """Generate mesh from currently loaded 3D model using GMSH"""
        print(">>> MESH_CONTROLLER: GMSH mesh generation started")
        
        # Generate mesh using GMSH service
        mesh_file_path = self.mesh_service.generate_mesh_with_gmsh(self.app.vtk_pipeline)
        
        if mesh_file_path:
            # Load the generated mesh
            if self.app.vtk_pipeline.load_file(mesh_file_path, is_generated_mesh=True):
                # Update the view
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
                if hasattr(self.app.ctrl, "view_reset_camera"):
                    self.app.ctrl.view_reset_camera()
                
                print(">>> MESH_CONTROLLER: GMSH generated mesh loaded successfully")
                
                # Show the generated mesh
                print(">>> MESH_CONTROLLER: Setting show_mesh state to True")
                self.app.state.show_mesh = True  
                self.app.vtk_pipeline.set_mesh_visibility(True)
                
                # Force a render update
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
                    print(">>> MESH_CONTROLLER: View updated after mesh generation")
            else:
                print(">>> MESH_CONTROLLER: Failed to load GMSH generated mesh")
        else:
            print(">>> MESH_CONTROLLER: GMSH mesh generation failed")


    def generate_mesh_gnn(self):
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
                
                # Show the generated mesh
                print(">>> MESH_CONTROLLER: Setting show_mesh state to True")
                self.app.state.show_mesh = True  
                self.app.vtk_pipeline.set_mesh_visibility(True)
                
                # Force a render update
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
                    print(">>> MESH_CONTROLLER: View updated after mesh generation")
            else:
                print(">>> MESH_CONTROLLER: Failed to load generated mesh")
    
    def update_mesh_color(self, color: str):
        """Update mesh color using mesh service"""
        self.mesh_service.update_mesh_color(self.app.vtk_pipeline, color)
    
    def update_representation_mode(self, mode: str):
        """Update mesh representation mode using mesh service"""
        self.mesh_service.update_representation_mode(self.app.vtk_pipeline, mode)