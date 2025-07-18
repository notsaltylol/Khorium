import os


class Representation:
    """
    Enum for different VTK actor representation modes.
    """

    Points = 0
    Wireframe = 1
    Surface = 2
    SurfaceWithEdges = 3


class LookupTable:
    """
    Enum for predefined color map presets for VTK lookup tables.
    """

    Rainbow = 0
    Inverted_Rainbow = 1
    Greyscale = 2
    Inverted_Greyscale = 3


CURRENT_DIRECTORY = os.path.abspath(os.path.dirname(__file__))
