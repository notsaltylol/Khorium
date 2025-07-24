import os
import re
import shutil

from trame.app import get_server
from trame.app.file_upload import ClientFile
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import html, vtk, vuetify3

from khorium.app.core.constants import CURRENT_DIRECTORY
from khorium.app.core.vtk_pipeline import VtkPipeline

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

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    @controller.set("reset_resolution")
    def reset_resolution(self):
        self.state.resolution = 6

    @change("resolution")
    def on_resolution_change(self, resolution, **_kwargs):
        print(f">>> ENGINE(a): Slider updating resolution to {resolution}")

    @controller.set("widget_click")
    def widget_click(self):
        print(">>> ENGINE(a): Widget Click")

    @controller.set("widget_change")
    def widget_change(self):
        print(">>> ENGINE(a): Widget Change")

    # @controller.set("upload_file")
    # def upload_file(self, files):
    #     """Handle .vtu file upload and reload VTK pipeline"""
    #     return

    def _build_ui(self, *_args, **_kwargs):
        with SinglePageLayout(self.server) as layout:
            # Toolbar
            layout.title.set_text("Khorium")
            with layout.toolbar:
                vuetify3.VSpacer()

                # # File upload button
                # with vuetify3.VBtn(icon=True, classes="mr-2"):
                #     vuetify3.VIcon("mdi-upload")
                #     html.Input(
                #         type="file",
                #         accept=".vtu",
                #         style="position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer;",
                #         change=(self.ctrl.upload_file, "[$event.target.files]"),
                #         __events=["change"],
                #     )
                # my_widgets.CustomWidget(
                #     attribute_name="Hello",
                #     py_attr_name="World",
                #     click=self.ctrl.widget_click,
                #     change=self.ctrl.widget_change,
                # )
                # vuetify3.VSpacer()
                # vuetify3.VSlider(                    # Add slider
                #     v_model=("resolution", 6),      # bind variable with an initial value of 6
                #     min=3, max=60, step=1,          # slider range
                #     dense=True, hide_details=True,  # presentation setup
                # )
                # with vuetify3.VBtn(icon=True, click=self.ctrl.reset_camera):
                #     vuetify3.VIcon("mdi-crop-free")
                # with vuetify3.VBtn(icon=True, click=self.reset_resolution):
                #     vuetify3.VIcon("mdi-undo")

            # with layout.drawer as drawer:
            #     # drawer components
            #     drawer.width = 325
            #     def actives_change(ids):
            #         _id = ids[0]
            #         if _id == "1":  # Mesh
            #             self.state.active_ui = "mesh"
            #         elif _id == "2":  # Contour
            #             self.state.active_ui = "contour"
            #         else:
            #             self.state.active_ui = "nothing"
            #     def visibility_change(event):
            #         _id = event["id"]
            #         _visibility = event["visible"]

            #         if _id == "1":  # Mesh
            #             self.vtk_pipeline.mesh_actor.SetVisibility(_visibility)
            #         elif _id == "2":  # Contour
            #             self.vtk_pipeline.contour_actor.SetVisibility(_visibility)
            #         self.ctrl.view_update()
            #     trame.GitTree(
            #         sources=(
            #             "pipeline",
            #             [
            #                 {"id": "1", "parent": "0", "visible": 1, "name": "Mesh"},
            #                 {"id": "2", "parent": "1", "visible": 1, "name": "Contour"},
            #             ],
            #         ),
            #         actives_change=(actives_change, "[$event]"),
            #         visibility_change=(visibility_change, "[$event]"),
            #     )
            #     vuetify3.VDivider(classes="mb-2")
            #     mesh_card(dataset_arrays=self.vtk_pipeline.dataset_arrays)
            #     contour_card(
            #         dataset_arrays=self.vtk_pipeline.dataset_arrays,
            #         contour_value=self.vtk_pipeline.contour_value,
            #         default_min=self.vtk_pipeline.default_min,
            #         default_max=self.vtk_pipeline.default_max,
            #     )

            # Main content
            # with layout.content:
            #     with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
            #         with vtk.VtkLocalView() as vtk_view:                # vtk.js view for local rendering
            #             self.ctrl.reset_camera = vtk_view.reset_camera  # Bind method to controller
            #             with vtk.VtkGeometryRepresentation():      # Add representation to vtk.js view
            #                 vtk.VtkAlgorithm(                      # Add ConeSource to representation
            #                     vtk_class="vtkConeSource",          # Set attribute value with no JS eval
            #                     state=("{ resolution }",)          # Set attribute value with JS eval
            #                 )

            with layout.content:
                # content components
                with vuetify3.VContainer(
                    fluid=True,
                    classes="pa-0 fill-height",
                ):
                    with vuetify3.VRow(classes="fill-height ma-0"):
                        # with vuetify3.VCol(classes="pa-0 fill-height max-width-325"):
                        #     # drawer components
                        #     # drawer.width = 325
                        #     def actives_change(ids):
                        #         _id = ids[0]
                        #         if _id == "1":  # Mesh
                        #             self.state.active_ui = "mesh"
                        #         elif _id == "2":  # Contour
                        #             self.state.active_ui = "contour"
                        #         else:
                        #             self.state.active_ui = "nothing"
                        # def visibility_change(event):
                        #     _id = event["id"]
                        #     _visibility = event["visible"]

                        #     if _id == "1":  # Mesh
                        #         self.vtk_pipeline.mesh_actor.SetVisibility(_visibility)
                        #     elif _id == "2":  # Contour
                        #         self.vtk_pipeline.contour_actor.SetVisibility(_visibility)
                        #     self.ctrl.view_update()
                        # trame.GitTree(
                        #     sources=(
                        #         "pipeline",
                        #         [
                        #             {"id": "1", "parent": "0", "visible": 1, "name": "Mesh"},
                        #             {"id": "2", "parent": "1", "visible": 1, "name": "Contour"},
                        #         ],
                        #     ),
                        #     actives_change=(actives_change, "[$event]"),
                        #     visibility_change=(visibility_change, "[$event]"),
                        # )
                        # vuetify3.VDivider(classes="mb-2")
                        # mesh_card(dataset_arrays=self.vtk_pipeline.dataset_arrays)
                        # contour_card(
                        #     dataset_arrays=self.vtk_pipeline.dataset_arrays,
                        #     contour_value=self.vtk_pipeline.contour_value,
                        #     default_min=self.vtk_pipeline.default_min,
                        #     default_max=self.vtk_pipeline.default_max,
                        # )
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
