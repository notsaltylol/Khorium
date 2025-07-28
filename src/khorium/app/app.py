import os
import re
import shutil
import requests
import tempfile

from trame.app import get_server
from trame.app.file_upload import ClientFile
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, vtk, vuetify3, iframe

from khorium.app.core.constants import CURRENT_DIRECTORY
from khorium.app.core.vtk_pipeline import VtkPipeline
from khorium.app.config import FRONTEND_URL, MESH_GENERATE_API

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------


@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        self.vtk_pipeline = VtkPipeline()
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
            self._hot_reload()
        self.ui = self._build_ui()

        # Set state variable
        self.state.trame__title = "Khorium"
        self.state.resolution = 6
        self.state.show_mesh = False  # Toggle for showing generated mesh
        self.state.mesh_color = "blue"
        self.state.representation_mode = "surface"
        
        # Register state change handlers
        self.state.change("show_mesh")(self.on_show_mesh_change)
        self.ctrl.trigger("hello")(self.hello)

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @controller.set("reset_resolution")
    def reset_resolution(self):
        self.state.resolution = 6

    @controller.set("reset_camera")
    def reset_camera(self):
        """Reset camera view"""
        if hasattr(self.ctrl, "view_reset_camera"):
            self.ctrl.view_reset_camera()

    @controller.set("fit_to_window")
    def fit_to_window(self):
        """Fit view to window"""
        if hasattr(self.ctrl, "view_reset_camera"):
            self.ctrl.view_reset_camera()

    @controller.set("hello")
    def hello(self):
        return "hiiiii"

    @change("resolution")
    def on_resolution_change(self, resolution, **_kwargs):
        print(f">>> ENGINE(a): Slider updating resolution to {resolution}")

    @change("mesh_color")
    def on_mesh_color_change(self, mesh_color, **_kwargs):
        print(f">>> ENGINE(a): Updating mesh color to {mesh_color}")
        self._update_mesh_color(mesh_color)
        if hasattr(self.ctrl, "view_update"):
            self.ctrl.view_update()

    @change("representation_mode")
    def on_representation_mode_change(self, representation_mode, **_kwargs):
        print(f">>> ENGINE(a): Updating representation mode to {representation_mode}")
        self._update_representation_mode(representation_mode)
        if hasattr(self.ctrl, "view_update"):
            self.ctrl.view_update()

    # @change("show_mesh")  
    def on_show_mesh_change(self, show_mesh, **_kwargs):
        print(f">>> ENGINE(a): [DEBUG] show_mesh state changed to: {show_mesh}")
        print(f">>> ENGINE(a): [DEBUG] Has generated mesh: {self.vtk_pipeline.has_generated_mesh}")
        print(f">>> ENGINE(a): [DEBUG] Has default mesh: {self.vtk_pipeline.has_default_mesh}")
        
        # Update VTK pipeline to show/hide mesh
        self.vtk_pipeline.set_mesh_visibility(show_mesh)
        
        # Update the view
        if hasattr(self.ctrl, "view_update"):
            self.ctrl.view_update()
            print(f">>> ENGINE(a): [DEBUG] View updated after mesh visibility change")
        else:
            print(f">>> ENGINE(a): [DEBUG] Warning: view_update not available")

    @controller.set("widget_click")
    def widget_click(self):
        print(">>> ENGINE(a): Widget Click")

    @controller.set("widget_change")
    def widget_change(self):
        print(">>> ENGINE(a): Widget Change")

    @controller.set("generate_mesh")
    def generate_mesh(self):
        """Generate mesh from current VTU file via API"""
        print(">>> ENGINE(a): Generate Mesh button clicked")
        
        # Check if we have a valid VTU file loaded
        current_file = os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
        if not os.path.exists(current_file) or os.path.getsize(current_file) == 0:
            print(">>> ENGINE(a): No VTU file to process")
            return
            
        # Call API to generate mesh
        print(f">>> ENGINE(a): Calling mesh generation API with file: {current_file}")
        
        try:
            # Prepare the file for upload
            with open(current_file, 'rb') as f:
                files = {'file': (os.path.basename(current_file), f, 'application/octet-stream')}
                
                print(f">>> ENGINE(a): Sending request to {MESH_GENERATE_API}")
                response = requests.post(MESH_GENERATE_API, files=files, timeout=30)
                
                if response.status_code == 200:
                    # Save the VTK mesh file
                    mesh_file_path = os.path.join(CURRENT_DIRECTORY, "generated_mesh.vtk")
                    with open(mesh_file_path, 'wb') as mesh_file:
                        mesh_file.write(response.content)
                    
                    print(f">>> ENGINE(a): Mesh saved to {mesh_file_path}")
                    
                    # Load the generated mesh
                    if self.vtk_pipeline.load_file(mesh_file_path, is_generated_mesh=True):
                        # Update the view
                        if hasattr(self.ctrl, "view_update"):
                            self.ctrl.view_update()
                        if hasattr(self.ctrl, "view_reset_camera"):
                            self.ctrl.view_reset_camera()
                        
                        print(">>> ENGINE(a): Generated mesh loaded successfully")
                    else:
                        print(">>> ENGINE(a): Failed to load generated mesh")
                else:
                    print(f">>> ENGINE(a): API request failed with status {response.status_code}: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            print(f">>> ENGINE(a): API request error: {e}")
        except Exception as e:
            print(f">>> ENGINE(a): Error generating mesh: {e}")

    @controller.set("toggle_mesh")
    def toggle_mesh(self):
        """Toggle visibility of generated mesh (legacy controller method)"""
        # The actual work is now done in on_show_mesh_change via @change decorator
        # This method just toggles the state, which will trigger the change handler
        self.state.show_mesh = not self.state.show_mesh

    @controller.set("upload_file")
    def upload_file(self, files):
        """Handle .vtu file upload and reload VTK pipeline"""
        if not files or len(files) == 0:
            print(">>> ENGINE(a): No files selected for upload")
            return
        
        if len(files) > 1:
            print(">>> ENGINE(a): Multiple files detected, processing only the first one")
        
        # Process only the first file
        file = files[0]
        file_helper = ClientFile(file)
        print(f">>> ENGINE(a): Uploading file: {file_helper.info}")

        # Get filename - file_helper.info might be a string or dict
        filename = ""
        if isinstance(file_helper.info, dict):
            filename = file_helper.info.get("name", "")
        elif isinstance(file_helper.info, str):
            # If info is a string like "File: cad_378.vtu of size 5639377 and type "
            # Extract the filename from the string
            match = re.search(r"File: ([^\s]+)", file_helper.info)
            if match:
                filename = match.group(1)
            else:
                filename = file_helper.info
        else:
            # Try to get name attribute from the file object
            filename = getattr(file, "name", "")

        # Validate file extension
        if not filename.lower().endswith(".vtu"):
            print(f">>> ENGINE(a): Invalid file format. Expected .vtu, got: {filename}")
            return

        # Validate file content
        if not file_helper.content or len(file_helper.content) == 0:
            print(f">>> ENGINE(a): Error - Empty file: {filename}")
            return

        # Save the uploaded file temporarily
        if not file_helper.name:
            print(">>> ENGINE(a): Error - No temporary file name available")
            return

        try:
            with open(file_helper.name, "wb") as f:
                f.write(file_helper.content)
            temp_file_path = file_helper.name
            print(f">>> ENGINE(a): File saved temporarily to: {temp_file_path}")
        except IOError as e:
            print(f">>> ENGINE(a): Error saving temporary file: {e}")
            return

        # Replace the existing cad_000.vtu file
        target_file_path = os.path.join(CURRENT_DIRECTORY, "cad_000.vtu")
        try:
            shutil.copy2(temp_file_path, target_file_path)
            print(f">>> ENGINE(a): Replaced {target_file_path} with uploaded file")

            # Verify file was written correctly
            if not os.path.exists(target_file_path) or os.path.getsize(target_file_path) == 0:
                print(">>> ENGINE(a): Error - Target file not properly written")
                return

        except (IOError, OSError) as e:
            print(f">>> ENGINE(a): Error copying file to target: {e}")
            return

        # Clean up temporary file
        try:
            if temp_file_path:
                os.remove(temp_file_path)
            print(f">>> ENGINE(a): Cleaned up temporary file: {temp_file_path}")
        except OSError:
            pass  # Ignore if temp file cleanup fails

        # Reload VTK pipeline with new file
        if self.vtk_pipeline.load_file(target_file_path):
            # Update the view
            if hasattr(self.ctrl, "view_update"):
                self.ctrl.view_update()
            if hasattr(self.ctrl, "view_reset_camera"):
                self.ctrl.view_reset_camera()

            print(">>> ENGINE(a): VTK pipeline reloaded with uploaded file")
            
            # Hide any existing generated mesh when new file is uploaded
            self.state.show_mesh = False
            self.vtk_pipeline.set_mesh_visibility(False)
            
        else:
            print(">>> ENGINE(a): Failed to load uploaded VTU file - file may be corrupted")

    def _update_mesh_color(self, color):
        """Update mesh color based on string value"""
        color_map = {
            "blue": (0.7, 0.8, 1.0),
            "red": (1.0, 0.3, 0.3),
            "green": (0.3, 1.0, 0.3),
            "white": (1.0, 1.0, 1.0)
        }
        
        rgb = color_map.get(color, (0.7, 0.8, 1.0))  # Default to blue
        
        # Update main mesh actor
        self.vtk_pipeline.mesh_actor.GetProperty().SetColor(*rgb)
        
        # Update generated mesh actor if it exists
        if self.vtk_pipeline.has_generated_mesh and self.vtk_pipeline.generated_mesh_actor:
            self.vtk_pipeline.generated_mesh_actor.GetProperty().SetColor(*rgb)
            
        # Update default mesh actor if it exists
        if self.vtk_pipeline.has_default_mesh and self.vtk_pipeline.default_mesh_actor:
            self.vtk_pipeline.default_mesh_actor.GetProperty().SetColor(*rgb)
            
    def _update_representation_mode(self, mode):
        """Update mesh representation mode"""
        # Update main mesh actor
        if mode == "surface":
            self.vtk_pipeline.mesh_actor.GetProperty().SetRepresentationToSurface()
        elif mode == "wireframe":
            self.vtk_pipeline.mesh_actor.GetProperty().SetRepresentationToWireframe()
        elif mode == "points":
            self.vtk_pipeline.mesh_actor.GetProperty().SetRepresentationToPoints()
            
        # Update generated mesh actor if it exists
        if self.vtk_pipeline.has_generated_mesh and self.vtk_pipeline.generated_mesh_actor:
            if mode == "surface":
                self.vtk_pipeline.generated_mesh_actor.GetProperty().SetRepresentationToSurface()
            elif mode == "wireframe":
                self.vtk_pipeline.generated_mesh_actor.GetProperty().SetRepresentationToWireframe()
            elif mode == "points":
                self.vtk_pipeline.generated_mesh_actor.GetProperty().SetRepresentationToPoints()
                
        # Update default mesh actor if it exists
        if self.vtk_pipeline.has_default_mesh and self.vtk_pipeline.default_mesh_actor:
            if mode == "surface":
                self.vtk_pipeline.default_mesh_actor.GetProperty().SetRepresentationToSurface()
            elif mode == "wireframe":
                self.vtk_pipeline.default_mesh_actor.GetProperty().SetRepresentationToWireframe()
            elif mode == "points":
                self.vtk_pipeline.default_mesh_actor.GetProperty().SetRepresentationToPoints()

    def _build_ui(self, *_args, **_kwargs):
        with SinglePageLayout(self.server) as layout:
            # Hide title and drawer
            layout.title.hide()
            # layout.drawer.hide()
            with layout.toolbar:

                # File upload button
                with vuetify3.VBtn(icon=True, classes="mr-2"):
                    vuetify3.VIcon("mdi-upload")
                    html.Input(
                        type="file",
                        accept=".vtu",
                        style="position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer;",
                        change=(self.ctrl.upload_file, "[$event.target.files]"),
                        __events=["change"],
                    )
                
                # Generate Mesh button
                with vuetify3.VBtn(
                    "Generate Mesh",
                    color="primary",
                    classes="mr-2",
                    click=self.ctrl.generate_mesh,
                ):
                    vuetify3.VIcon("mdi-auto-fix", classes="mr-1")
                
                vuetify3.VSpacer()

            with layout.content:
                # Enable iframe communication for React frontend at the top level
                print(">>> ENGINE(a): [DEBUG] Setting up iframe.Communicator at layout level")
                iframe.Communicator(
                    target_origin=FRONTEND_URL, 
                    enable_rpc=True,
                    retry_connection=True,
                    retry_interval=500,  # 0.5 seconds
                    max_retries=10
                )
                print(">>> ENGINE(a): [DEBUG] iframe.Communicator setup complete")
                
                # content components
                with vuetify3.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    with vuetify3.VRow(classes="fill-height ma-0"):
                        with vuetify3.VCol(fluid=True, classes="pa-0 fill-height"):
                            # view = vtk.VtkRemoteView(renderWindow, interactive_ratio=1)
                            # view = vtk.VtkLocalView(renderWindow)
                            view = vtk.VtkRemoteLocalView(
                                self.vtk_pipeline.renderWindow,
                                namespace="view",
                                mode="local",
                                interactive_ratio=1,
                            )
                            self.ctrl.view_update = view.update
                            self.ctrl.view_reset_camera = view.reset_camera

            # Footer
            # layout.footer.hide()

            return layout

    def _hot_reload(self):
        try:
            import asyncio
            from pathlib import Path

            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            current_event_loop = asyncio.get_event_loop()

            def update_ui():
                with self.server.state:
                    self._build_ui()

            class UpdateUIOnChange(FileSystemEventHandler):
                def on_modified(self, event):
                    current_event_loop.call_soon_threadsafe(update_ui)

            observer = Observer()
            observer.schedule(
                UpdateUIOnChange(),
                str(Path(__file__).parent.absolute()),
                recursive=False,
            )
            observer.start()
        except ImportError:
            print("Watchdog not installed so skipping the auto monitoring")
