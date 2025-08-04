from trame.decorators import change


class ViewController:
    """Controller for VTK view state management"""
    
    def __init__(self, app):
        self.app = app
        self._register_state_handlers()
    
    def _register_state_handlers(self):
        """Register state change handlers"""
        # Register new state manager handlers
        self.app.state.change("mesh_visible")(self.on_mesh_visible_change)
    
    @change("mesh_visible")
    def on_mesh_visible_change(self, mesh_visible, **kwargs):
        """Handle mesh visibility state changes via StateManager"""
        print(f">>> VIEW_CONTROLLER: [DEBUG] mesh_visible state changed to: {mesh_visible}")
        self._update_mesh_display()
    
    def _update_mesh_display(self):
        """Update VTK pipeline with current mesh state"""
        # Get current mesh state
        mesh_visible = self.app.state_manager.get("mesh_visible", False)
        
        print(f">>> VIEW_CONTROLLER: [DEBUG] Has generated mesh: {self.app.vtk_pipeline.has_generated_mesh}")
        print(f">>> VIEW_CONTROLLER: [DEBUG] Has default mesh: {self.app.vtk_pipeline.has_default_mesh}")
        
        # Update VTK pipeline
        self.app.vtk_pipeline.set_mesh_visibility(mesh_visible)
        
        # Apply mesh properties if visible
        if mesh_visible:
            # TODO: Add methods to VtkPipeline for opacity, wireframe, etc.
            pass
        
        # Update the view
        if hasattr(self.app.ctrl, "view_update"):
            self.app.ctrl.view_update()
            print(f">>> VIEW_CONTROLLER: [DEBUG] View updated after mesh changes")
        else:
            print(f">>> VIEW_CONTROLLER: [DEBUG] Warning: view_update not available")
    
    def setup_view_controllers(self, view):
        """Setup view-related controller methods"""
        self.app.ctrl.view_update = view.update
        self.app.ctrl.view_reset_camera = view.reset_camera