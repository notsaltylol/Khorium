import os
from dotenv import load_dotenv

load_dotenv()

MESH_GENERATE_API = os.getenv("MESH_GENERATE_API", "http://localhost:10000/optimize_mesh")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://www.app.khorium.ai")
