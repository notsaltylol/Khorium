import os
import time
from typing import Optional
from trame.decorators import controller

from khorium.app.services.mesh_service import MeshService
from khorium.app.services.file_service import FileService
from khorium.app.services.code_execution_service import CodeExecutionService


class MeshController:
    """Controller for mesh generation and visualization operations"""
    
    def __init__(self, app):
        self.app = app
        self.mesh_service = MeshService()
        self.file_service = FileService()
        self.code_service = CodeExecutionService(default_timeout=120)  # 2 minutes for mesh operations
        self._register_controllers()
        self._register_state_handlers()  # Register state change handlers

    def _register_state_handlers(self):
        """Register state change handlers"""
        # Register new state manager handlers
        self.app.state.change("set_mesh_size_factor")(self.set_mesh_size_factor)
        self.app.state.change("execute_mesh_code")(self._handle_execute_mesh_code_state_change)
    
    def _handle_execute_mesh_code_state_change(self, **kwargs):
        """Handle state change for execute_mesh_code"""
        code = self.app.state_manager.get("execute_mesh_code", "")
        if code and code.strip():
            self.execute_mesh_code(code)
    
    def _register_controllers(self):
        """Register controller methods with Trame"""
        @controller.set("load_generated_mesh")
        def load_generated_mesh():
            """Manually load generated mesh files"""
            print(">>> MESH_CONTROLLER: Manual load_generated_mesh triggered")
            self._handle_post_execution_mesh_loading()
            if hasattr(self.app.ctrl, "view_update"):
                self.app.ctrl.view_update()
        self.app.ctrl.generate_mesh = self.generate_mesh_gmsh
    
    @controller.set("generate_mesh")
    def generate_mesh_gmsh(self):
        """Generate mesh from currently loaded 3D model using GMSH"""
        print(">>> MESH_CONTROLLER: GMSH mesh generation started")
        
        # Set mesh size factor from state before generating
        mesh_size_factor = self.app.state_manager.get("mesh_size_factor", 1.0)
        self.mesh_service.set_mesh_size_factor(mesh_size_factor)
        
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
                
                # Show the generated mesh using StateManager
                print(">>> MESH_CONTROLLER: Setting mesh visible via StateManager")
                self.app.state_manager.show_mesh(True)
                
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
                
                # Show the generated mesh using StateManager
                print(">>> MESH_CONTROLLER: Setting mesh visible via StateManager")
                self.app.state_manager.show_mesh(True)
                
                # Force a render update
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
                    print(">>> MESH_CONTROLLER: View updated after mesh generation")
            else:
                print(">>> MESH_CONTROLLER: Failed to load generated mesh")
    
    def execute_mesh_code(self, code: str, timeout: Optional[int] = None):
        """
        Execute Python code for mesh operations
        
        Args:
            code: Python code string to execute
            timeout: Optional timeout in seconds (default: 120s for mesh operations)
        """
        print(f">>> MESH_CONTROLLER: Executing mesh code ({len(code)} chars)")
        
        # Initialize execution state using StateManager
        self.app.state_manager.start_mesh_code_execution(code)
        
        # Execute the code with mesh context (STL/VTU files automatically available)
        result = self.code_service.execute_mesh_code(
            code=code,
            timeout=timeout
        )
        
        # Convert result to dictionary for Trame state
        result_dict = {
            'success': result.success,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.exit_code,
            'execution_time': result.execution_time,
            'error_message': result.error_message
        }
        
        # Update comprehensive state with results using StateManager
        error_message = result.error_message or result.stderr or 'Execution failed' if not result.success else ""
        self.app.state_manager.complete_mesh_code_execution(result.success, result_dict, error_message)
        
        if result.success:
            print(f">>> MESH_CONTROLLER: Mesh code executed successfully in {result.execution_time:.2f}s")
            
            # Check for generated mesh files and auto-load them (with small delay)
            import time
            time.sleep(0.5)  # Give time for file system to sync
            self._handle_post_execution_mesh_loading()
            
            # If the code might have modified mesh data, trigger a view update
            if any(keyword in code.lower() for keyword in ['mesh', 'vtk', 'generate', 'load', 'update']):
                print(">>> MESH_CONTROLLER: Code contains mesh keywords, triggering view update")
                if hasattr(self.app.ctrl, "view_update"):
                    self.app.ctrl.view_update()
        else:
            print(f">>> MESH_CONTROLLER: Mesh code execution failed: {result.error_message}")
        
        return result_dict

    def get_mesh_code_execution_state(self):
        """
        Get the current mesh code execution state
        
        Returns:
            Dictionary containing current execution state
        """
        return self.app.state_manager.get_mesh_code_execution_summary()

    def clear_mesh_code_state(self):
        """Clear all mesh code execution state"""
        self.app.state_manager.clear_mesh_code_execution()
        print(">>> MESH_CONTROLLER: Cleared mesh code execution state")

    def is_mesh_code_running(self):
        """Check if mesh code is currently executing"""
        return self.app.state_manager.is_mesh_code_running()

    def get_mesh_code_error_message(self):
        """Get the current error message if any"""
        return self.app.state_manager.get("mesh_code_error_message", "")
    
    def _handle_post_execution_mesh_loading(self):
        """Check for generated mesh files and auto-load them into VTK pipeline"""
        from khorium.app.core.constants import CURRENT_DIRECTORY
        import glob
        import time
        
        print(f">>> MESH_CONTROLLER: Checking for generated mesh files in: {CURRENT_DIRECTORY}")
        
        # List all files in the directory first for debugging
        try:
            all_files = os.listdir(CURRENT_DIRECTORY)
            print(f">>> MESH_CONTROLLER: All files in directory: {all_files}")
        except Exception as e:
            print(f">>> MESH_CONTROLLER: Error listing directory: {e}")
            return
        
        # Common mesh file patterns that might be generated
        mesh_patterns = [
            "*.vtk",
            "generated_mesh.msh",
            "generated_mesh.vtk", 
            "*.vtu",
            "output.msh",
            "mesh.vtk",
            "cube_mesh.msh",
            "cylinder_mesh.msh",
            "sphere_mesh.msh",
            "rectangle_mesh.msh",
            "circle_mesh.msh",
            "stl_mesh.msh",
            "stl_mesh.vtk"
        ]
        
        generated_files = []
        
        # Search for generated mesh files
        for pattern in mesh_patterns:
            if '*' in pattern:
                # Use glob for wildcard patterns
                file_pattern = os.path.join(CURRENT_DIRECTORY, pattern)
                matches = glob.glob(file_pattern)
                generated_files.extend(matches)
                if matches:
                    print(f">>> MESH_CONTROLLER: Found files matching {pattern}: {matches}")
            else:
                # Check specific file
                file_path = os.path.join(CURRENT_DIRECTORY, pattern)
                if os.path.exists(file_path):
                    generated_files.append(file_path)
                    print(f">>> MESH_CONTROLLER: Found specific file: {file_path}")
        
        if generated_files:
            print(f">>> MESH_CONTROLLER: Found {len(generated_files)} generated mesh files: {generated_files}")
            
            # Load the most recently modified file
            latest_file = max(generated_files, key=os.path.getmtime)
            file_age = time.time() - os.path.getmtime(latest_file)
            print(f">>> MESH_CONTROLLER: Loading latest generated mesh: {os.path.basename(latest_file)} (age: {file_age:.1f}s)")
            
            try:
                # Use VTK pipeline to load the generated mesh
                if hasattr(self.app, 'vtk_pipeline') and self.app.vtk_pipeline:
                    if latest_file.endswith('.vtk') or latest_file.endswith('.vtu'):
                        # Load VTK/VTU files as generated mesh
                        print(f">>> MESH_CONTROLLER: Loading VTK/VTU file as generated mesh: {latest_file}")
                        self.app.vtk_pipeline.load_file(latest_file, is_generated_mesh=True)
                        
                        # Enable mesh visibility
                        self.app.state_manager.show_mesh(True)
                        print(f">>> MESH_CONTROLLER: Successfully loaded VTK file and enabled visibility: {latest_file}")
                        
                    elif latest_file.endswith('.msh'):
                        # Convert MSH to VTK for visualization
                        print(f">>> MESH_CONTROLLER: Converting MSH file: {latest_file}")
                        converted_vtk = self._convert_msh_to_vtk(latest_file)
                        if converted_vtk:
                            print(f">>> MESH_CONTROLLER: Loading converted VTK file as generated mesh: {converted_vtk}")
                            self.app.vtk_pipeline.load_file(converted_vtk, is_generated_mesh=True)
                            # Enable mesh visibility
                            self.app.state_manager.show_mesh(True)
                            print(f">>> MESH_CONTROLLER: Successfully loaded converted MSH file and enabled visibility: {latest_file}")
                        else:
                            print(f">>> MESH_CONTROLLER: Failed to convert MSH file: {latest_file}")
                
            except Exception as e:
                print(f">>> MESH_CONTROLLER: Error loading generated mesh: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(">>> MESH_CONTROLLER: No generated mesh files found to auto-load")
    
    def _convert_msh_to_vtk(self, msh_file_path: str) -> Optional[str]:
        """Convert Gmsh MSH file to VTK format for visualization"""
        try:
            print(f">>> MESH_CONTROLLER: Attempting to convert MSH file: {msh_file_path}")
            
            # Check if file exists and has content
            if not os.path.exists(msh_file_path):
                print(f">>> MESH_CONTROLLER: MSH file does not exist: {msh_file_path}")
                return None
            
            file_size = os.path.getsize(msh_file_path)
            print(f">>> MESH_CONTROLLER: MSH file size: {file_size} bytes")
            
            if file_size == 0:
                print(f">>> MESH_CONTROLLER: MSH file is empty: {msh_file_path}")
                return None
            
            try:
                import meshio
                print(">>> MESH_CONTROLLER: meshio imported successfully")
                
                # Read MSH file
                print(f">>> MESH_CONTROLLER: Reading MSH file...")
                mesh = meshio.read(msh_file_path)
                print(f">>> MESH_CONTROLLER: MSH file read successfully, cells: {len(mesh.cells) if mesh.cells else 0}, points: {len(mesh.points) if mesh.points is not None else 0}")
                
                # Generate VTK file path
                vtk_path = msh_file_path.replace('.msh', '_converted.vtk')
                
                # Write as VTK
                print(f">>> MESH_CONTROLLER: Writing VTK file: {vtk_path}")
                meshio.write(vtk_path, mesh)
                
                # Verify VTK file was created
                if os.path.exists(vtk_path) and os.path.getsize(vtk_path) > 0:
                    print(f">>> MESH_CONTROLLER: Successfully converted {msh_file_path} to {vtk_path}")
                    return vtk_path
                else:
                    print(f">>> MESH_CONTROLLER: VTK file was not created or is empty: {vtk_path}")
                    return None
                    
            except ImportError as ie:
                print(f">>> MESH_CONTROLLER: meshio not available for MSH conversion: {ie}")
                # Try alternative approach using gmsh itself
                return self._convert_msh_to_vtk_with_gmsh(msh_file_path)
                
        except Exception as e:
            print(f">>> MESH_CONTROLLER: Error converting MSH to VTK: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _convert_msh_to_vtk_with_gmsh(self, msh_file_path: str) -> Optional[str]:
        """Convert MSH to VTK using gmsh itself"""
        try:
            import gmsh
            print(">>> MESH_CONTROLLER: Attempting MSH to VTK conversion using gmsh")
            
            gmsh.initialize()
            gmsh.open(msh_file_path)
            
            # Generate VTK file path
            vtk_path = msh_file_path.replace('.msh', '_converted.vtk')
            
            # Write as VTK
            gmsh.write(vtk_path)
            gmsh.finalize()
            
            # Verify VTK file was created
            if os.path.exists(vtk_path) and os.path.getsize(vtk_path) > 0:
                print(f">>> MESH_CONTROLLER: Successfully converted {msh_file_path} to {vtk_path} using gmsh")
                return vtk_path
            else:
                print(f">>> MESH_CONTROLLER: Gmsh VTK file was not created or is empty: {vtk_path}")
                return None
                
        except Exception as e:
            print(f">>> MESH_CONTROLLER: Error converting MSH to VTK with gmsh: {e}")
            return None

    @controller.set("set_mesh_size_factor")
    def set_mesh_size_factor(self, factor: float):
        """Update mesh size factor in state"""
        self.app.state_manager.set_mesh_size_factor(factor)
        print(f">>> MESH_CONTROLLER: Mesh size factor updated to {factor}")