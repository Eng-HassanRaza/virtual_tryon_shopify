from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import time
import random
from typing import List
from PIL import Image
import subprocess

app = FastAPI()

# Get base directory (directory where this script lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Absolute paths to directories
TEMP_INPUT_DIR = os.path.join(BASE_DIR, "temp_inputs")
FINAL_OUTPUT_DIR = os.path.join(BASE_DIR, "served_outputs")
OOTD_OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "images_output"))  # one level up
RUN_OOTD_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "run_ootd.py"))  # one level up

# Set to True if you want to simulate processing instead of running real OOTDiffusion
USE_FAKE_PROCESSING = False

# Create necessary directories
os.makedirs(TEMP_INPUT_DIR, exist_ok=True)
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)
os.makedirs(OOTD_OUTPUT_DIR, exist_ok=True)

# Mount static folder
app.mount("/served_outputs", StaticFiles(directory=FINAL_OUTPUT_DIR), name="served_outputs")


@app.post("/tryon/")
async def tryon(
    model_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...),
    sample: int = Form(1),
    scale: float = Form(2.0)
):
    uid = str(uuid.uuid4())
    session_output_dir = os.path.join(FINAL_OUTPUT_DIR, uid)
    os.makedirs(session_output_dir, exist_ok=True)

    # File paths
    model_path = os.path.join(TEMP_INPUT_DIR, f"model_{uid}.jpg")
    cloth_path = os.path.join(TEMP_INPUT_DIR, f"cloth_{uid}.jpg")

    # Save input files
    with open(model_path, "wb") as f:
        shutil.copyfileobj(model_image.file, f)
    with open(cloth_path, "wb") as f:
        shutil.copyfileobj(cloth_image.file, f)

    if USE_FAKE_PROCESSING:
        time.sleep(1)  # simulate processing
        for i in range(sample):
            img = Image.new("RGB", (512, 768), (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
            img.save(os.path.join(OOTD_OUTPUT_DIR, f"out_hd_{i}.png"))
    else:
        # Real OOTDiffusion subprocess
        cmd = [
            "/workspace/miniconda3/envs/ootd/bin/python",  # Replace with your conda env python path
            RUN_OOTD_PATH,
            "--model_path", model_path,
            "--cloth_path", cloth_path,
            "--scale", str(scale),
            "--sample", str(sample)
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Processing failed: {e}"}

    # Move outputs to result folder
    output_files = []
    for i in range(sample):
        original_path = os.path.join(OOTD_OUTPUT_DIR, f"out_hd_{i}.png")
        if os.path.exists(original_path):
            new_path = os.path.join(session_output_dir, f"result_{i}.png")
            shutil.copy(original_path, new_path)
            file_url = os.path.join("/served_outputs", uid, f"result_{i}.png")
            output_files.append(request_url(file_url))

    return {
        "status": "success",
        "results": output_files
    }


def request_url(path: str) -> str:
    """Generate full public URL based on where app is running (localhost or remote)."""
    import os
    # You can customize this based on your host (localhost or RunPod etc.)
    base_url = os.environ.get("PUBLIC_API_URL", "http://localhost:7860")
    return f"{base_url}{path}"
