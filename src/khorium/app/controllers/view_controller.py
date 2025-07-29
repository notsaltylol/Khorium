from trame.decorators import change


class ViewController:
    """Controller for VTK view state management"""
    
    def __init__(self, app):
        self.app = app
        self._register_state_handlers()
    
    def _register_state_handlers(self):
        """Register state change handlers"""
        self.app.state.change("show_mesh")(self.on_show_mesh_change)
    
    @change("show_mesh")  
    def on_show_mesh_change(self, show_mesh, **_kwargs):
        """Handle mesh visibility state changes"""
        print(f">>> VIEW_CONTROLLER: [DEBUG] show_mesh state changed to: {show_mesh}")
        print(f">>> VIEW_CONTROLLER: [DEBUG] Has generated mesh: {self.app.vtk_pipeline.has_generated_mesh}")
        print(f">>> VIEW_CONTROLLER: [DEBUG] Has default mesh: {self.app.vtk_pipeline.has_default_mesh}")
        
        # Update VTK pipeline to show/hide mesh
        self.app.vtk_pipeline.set_mesh_visibility(show_mesh)
        
        # Update the view
        if hasattr(self.app.ctrl, "view_update"):
            self.app.ctrl.view_update()
            print(f">>> VIEW_CONTROLLER: [DEBUG] View updated after mesh visibility change")
        else:
            print(f">>> VIEW_CONTROLLER: [DEBUG] Warning: view_update not available")
    
    def setup_view_controllers(self, view):
        """Setup view-related controller methods"""
        self.app.ctrl.view_update = view.update
        self.app.ctrl.view_reset_camera = view.reset_camera