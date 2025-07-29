from trame.widgets import vtk


class ViewportComponent:
    """VTK viewport component for 3D visualization"""
    
    def __init__(self, app):
        self.app = app
    
    def build(self):
        """Build the VTK viewport"""
        # view = vtk.VtkRemoteView(renderWindow, interactive_ratio=1)
        # view = vtk.VtkLocalView(renderWindow)
        view = vtk.VtkRemoteLocalView(
            self.app.vtk_pipeline.renderWindow,
            namespace="view",
            mode="local",
            interactive_ratio=1,
        )
        
        # Setup view controllers via the view controller
        if hasattr(self.app, 'view_controller'):
            self.app.view_controller.setup_view_controllers(view)
        else:
            # Fallback for backward compatibility
            self.app.ctrl.view_update = view.update
            self.app.ctrl.view_reset_camera = view.reset_camera
        
        return view