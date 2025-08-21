from trame.widgets import html, vuetify3


class ToolbarComponent:
    """Toolbar component with file upload and mesh generation buttons"""
    
    def __init__(self, app):
        self.app = app
    
    def build(self):
        """Build the toolbar UI components"""
        # File upload button
        with vuetify3.VBtn(icon=True, classes="mr-2"):
            vuetify3.VIcon("mdi-upload")
            html.Input(
                type="file",
                accept=".vtu,.stl",
                style="position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer;",
                change=(self.app.ctrl.upload_file, "[$event.target.files]"),
                __events=["change"],
            )
        
        # # Generate Mesh button
        # with vuetify3.VBtn(
        #     "Generate Mesh",
        #     color="primary",
        #     classes="mr-2",
        #     click=self.app.ctrl.generate_mesh,
        # ):
        #     vuetify3.VIcon("mdi-auto-fix", classes="mr-1")
        
        vuetify3.VSpacer()