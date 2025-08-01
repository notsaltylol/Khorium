from trame.app import get_server
from trame.decorators import TrameApp

from khorium.app.core.vtk_pipeline import VtkPipeline
from khorium.app.core.state_manager import StateManager
from khorium.app.controllers.file_controller import FileController
from khorium.app.controllers.mesh_controller import MeshController
from khorium.app.controllers.view_controller import ViewController
from khorium.app.ui.layouts.main_layout import MainLayout
from khorium.app.utils.hot_reload import setup_hot_reload

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------


@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        self.vtk_pipeline = VtkPipeline()
        
        # Initialize StateManager
        self.state_manager = StateManager(self.server.state)
        self.state_manager.initialize_state()
        
        # Initialize controllers
        self.view_controller = ViewController(self)
        self.file_controller = FileController(self)
        self.mesh_controller = MeshController(self)
        
        # Initialize UI layout
        self.main_layout = MainLayout(self)
        
        # Setup hot reload if enabled
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
            setup_hot_reload(self.server, self._build_ui)
            
        self.ui = self._build_ui()

        # Set Trame-specific state variables
        self.state.trame__title = "Khorium"

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller


    def _build_ui(self, *_args, **_kwargs):
        return self.main_layout.build_ui(*_args, **_kwargs)

