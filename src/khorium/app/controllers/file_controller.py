from trame.decorators import controller

from khorium.app.services.file_service import FileService


class FileController:
    """Controller for file upload operations"""
    
    def __init__(self, app):
        self.app = app
        self.file_service = FileService()
        self._register_controllers()
    
    def _register_controllers(self):
        """Register controller methods with Trame"""
        self.app.ctrl.upload_file = self.upload_file
    
    @controller.set("upload_file")
    def upload_file(self, files):
        """Handle .vtu or .stl file upload and reload VTK pipeline"""
        target_file_path = self.file_service.process_uploaded_files(files)
        
        if not target_file_path:
            return
        
        # Check if uploaded file is STL
        is_stl = target_file_path.lower().endswith('.stl')
        
        # Reload VTK pipeline with new file
        if self.app.vtk_pipeline.load_file(target_file_path):
            # Center the camera on all visible actors
            self.app.vtk_pipeline.center_camera_on_all_actors()
            
            # Update the view and ensure proper centering
            if hasattr(self.app.ctrl, "view_update"):
                self.app.ctrl.view_update()
            if hasattr(self.app.ctrl, "view_reset_camera"):
                self.app.ctrl.view_reset_camera()
                print(">>> FILE_CONTROLLER: Camera reset to center the uploaded model")

            if is_stl:
                print(">>> FILE_CONTROLLER: STL file loaded and rendered successfully")
                # For STL files, we don't use the mesh toggle functionality
                self.app.state_manager.show_mesh(False)
            else:
                print(">>> FILE_CONTROLLER: VTK pipeline reloaded with uploaded VTU file")
                # Hide any existing generated mesh when new VTU file is uploaded
                self.app.state_manager.show_mesh(False)
            
        else:
            file_type = "STL" if is_stl else "VTU"
            print(f">>> FILE_CONTROLLER: Failed to load uploaded {file_type} file - file may be corrupted")