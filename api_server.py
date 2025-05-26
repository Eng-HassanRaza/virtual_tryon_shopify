from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.staticfiles import StaticFiles
import shutil
import os
import uuid
import time
import random
from PIL import Image
import subprocess

app = FastAPI()

# Configuration
TEMP_INPUT_DIR = "temp_inputs"
FINAL_OUTPUT_DIR = "served_outputs"
OOTD_OUTPUT_DIR = "images_output"  # original ootdiffusion output folder
USE_FAKE_PROCESSING = True  # Set to False to use real OOTDiffusion

# Create necessary directories
os.makedirs(TEMP_INPUT_DIR, exist_ok=True)
os.makedirs(FINAL_OUTPUT_DIR, exist_ok=True)
os.makedirs(OOTD_OUTPUT_DIR, exist_ok=True)

# Mount static folder for result access
app.mount("/served_outputs", StaticFiles(directory=FINAL_OUTPUT_DIR), name="served_outputs")


@app.post("/tryon/")
async def tryon(
    request: Request,
    model_image: UploadFile = File(...),
    cloth_image: UploadFile = File(...),
    sample: int = Form(1),
    scale: float = Form(2.0)
):
    uid = str(uuid.uuid4())
    session_output_dir = os.path.join(FINAL_OUTPUT_DIR, uid)
    os.makedirs(session_output_dir, exist_ok=True)

    model_path = os.path.join(TEMP_INPUT_DIR, f"model_{uid}.jpg")
    cloth_path = os.path.join(TEMP_INPUT_DIR, f"cloth_{uid}.jpg")

    # Save uploaded files
    with open(model_path, "wb") as f:
        shutil.copyfileobj(model_image.file, f)
    with open(cloth_path, "wb") as f:
        shutil.copyfileobj(cloth_image.file, f)

    if USE_FAKE_PROCESSING:
        # Simulate processing delay
        time.sleep(1)

        # Generate fake output images
        for i in range(sample):
            fake_img = Image.new(
                "RGB",
                (512, 768),
                (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            )
            fake_img_path = os.path.join(OOTD_OUTPUT_DIR, f"out_hd_{i}.png")
            fake_img.save(fake_img_path)
    else:
        # Real OOTDiffusion run
        cmd = [
            "python", "run_ootd.py",
            "--model_path", model_path,
            "--cloth_path", cloth_path,
            "--scale", str(scale),
            "--sample", str(sample)
        ]
        try:
            subprocess.run(cmd, check=True, cwd="run")
        except subprocess.CalledProcessError as e:
            return {"status": "error", "message": f"Processing failed: {e}"}

    # Build full base URL from request
    base_url = str(request.base_url).rstrip("/")

    # Collect and copy outputs to session folder, create full URLs
    output_files = []
    for i in range(sample):
        original_file = os.path.join(OOTD_OUTPUT_DIR, f"out_hd_{i}.png")
        if os.path.exists(original_file):
            new_name = os.path.join(session_output_dir, f"result_{i}.png")
            shutil.copy(original_file, new_name)
            output_files.append(f"{base_url}/served_outputs/{uid}/result_{i}.png")

    return {
        "status": "success",
        "results": output_files
    }
