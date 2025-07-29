from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import iframe, vuetify3

from khorium.app.config import FRONTEND_URL
from khorium.app.ui.components.toolbar import ToolbarComponent
from khorium.app.ui.components.viewport import ViewportComponent


class MainLayout:
    """Main application layout"""
    
    def __init__(self, app):
        self.app = app
        self.toolbar = ToolbarComponent(app)
        self.viewport = ViewportComponent(app)
    
    def build_ui(self, *_args, **_kwargs):
        """Build the main UI layout"""
        with SinglePageLayout(self.app.server) as layout:
            # Hide title and drawer
            layout.title.hide()
            # layout.drawer.hide()
            
            with layout.toolbar:
                self.toolbar.build()
                
            with layout.content:
                # Enable iframe communication for React frontend at the top level
                print(">>> MAIN_LAYOUT: [DEBUG] Setting up iframe.Communicator at layout level")
                iframe.Communicator(
                    target_origin=FRONTEND_URL, 
                    enable_rpc=True,
                    retry_connection=True,
                    retry_interval=500,  # 0.5 seconds
                    max_retries=10
                )
                print(">>> MAIN_LAYOUT: [DEBUG] iframe.Communicator setup complete")
                
                # content components
                with vuetify3.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    with vuetify3.VRow(classes="fill-height ma-0"):
                        with vuetify3.VCol(fluid=True, classes="pa-0 fill-height"):
                            self.viewport.build()

            # Footer
            # layout.footer.hide()

            return layout