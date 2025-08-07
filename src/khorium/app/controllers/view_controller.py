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
        
        # Register mesh code execution state handlers
        self.app.state.change("mesh_code_status")(self.on_mesh_code_status_change)
        self.app.state.change("mesh_code_error_message")(self.on_mesh_code_error_change)
    
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
    
    @change("mesh_code_status")
    def on_mesh_code_status_change(self, mesh_code_status, **kwargs):
        """Handle mesh code execution status changes"""
        print(f">>> VIEW_CONTROLLER: [DEBUG] mesh_code_status changed to: {mesh_code_status}")
        
        # Get current execution state
        current_code = self.app.state_manager.get("mesh_code_current", "")
        error_message = self.app.state_manager.get("mesh_code_error_message", "")
        execution_time = self.app.state_manager.get("mesh_code_execution_duration", 0.0)
        
        # Log execution state change
        if mesh_code_status == "running":
            print(f">>> VIEW_CONTROLLER: [DEBUG] Started executing code ({len(current_code)} chars)")
        elif mesh_code_status == "completed":
            print(f">>> VIEW_CONTROLLER: [DEBUG] Code execution completed successfully in {execution_time:.2f}s")
            # Trigger view update if mesh-related code was executed
            if any(keyword in current_code.lower() for keyword in ['mesh', 'vtk', 'generate', 'load', 'update']):
                print(">>> VIEW_CONTROLLER: [DEBUG] Mesh-related code executed, triggering view update")
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
        elif mesh_code_status == "failed":
            print(f">>> VIEW_CONTROLLER: [DEBUG] Code execution failed: {error_message}")
    
    @change("mesh_code_error_message")
    def on_mesh_code_error_change(self, mesh_code_error_message, **kwargs):
        """Handle mesh code execution error message changes"""
        if mesh_code_error_message:
            print(f">>> VIEW_CONTROLLER: [DEBUG] mesh_code_error_message updated: {mesh_code_error_message}")

    def setup_view_controllers(self, view):
        """Setup view-related controller methods"""
        self.app.ctrl.view_update = view.update
        self.app.ctrl.view_reset_camera = view.reset_camera