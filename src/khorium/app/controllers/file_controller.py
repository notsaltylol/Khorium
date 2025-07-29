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
        """Handle .vtu file upload and reload VTK pipeline"""
        target_file_path = self.file_service.process_uploaded_files(files)
        
        if not target_file_path:
            return
        
        # Reload VTK pipeline with new file
        if self.app.vtk_pipeline.load_file(target_file_path):
            # Update the view
            if hasattr(self.app.ctrl, "view_update"):
                self.app.ctrl.view_update()
            if hasattr(self.app.ctrl, "view_reset_camera"):
                self.app.ctrl.view_reset_camera()

            print(">>> FILE_CONTROLLER: VTK pipeline reloaded with uploaded file")
            
            # Hide any existing generated mesh when new file is uploaded
            self.app.state.show_mesh = False
            self.app.vtk_pipeline.set_mesh_visibility(False)
            
        else:
            print(">>> FILE_CONTROLLER: Failed to load uploaded VTU file - file may be corrupted")