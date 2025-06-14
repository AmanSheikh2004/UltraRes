import os
import cv2
import numpy as np
import torch
from flask import Flask, request, jsonify, render_template
import RRDBNet_arch as arch
from io import BytesIO
from PIL import Image
import base64
import subprocess

from collections import OrderedDict

app = Flask(__name__, static_folder='static')

# Model path
model_ESRGAN_path = 'models/RRDB_ESRGAN_x4.pth'

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load ESRGAN model
model_ESRGAN = arch.RRDBNet(3, 3, 64, 23, gc=32)
model_ESRGAN.load_state_dict(torch.load(model_ESRGAN_path, map_location=device), strict=True)
model_ESRGAN.eval()
model_ESRGAN = model_ESRGAN.to(device)

def interpolate_model(alpha):
    """
    Calls net_interp.py to generate an interpolated model using alpha,
    then loads and returns the interpolated model.
    """
    interp_model_path = f'models/interp_{int(alpha * 10):02d}.pth'

    # Run net_interp.py as a subprocess
    try:
        subprocess.run(['python', 'net_interp.py', str(alpha)], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Interpolation script failed: {e}")

    # Load the interpolated model
    model_interp = arch.RRDBNet(3, 3, 64, 23, gc=32)
    model_interp.load_state_dict(torch.load(interp_model_path, map_location=device), strict=True)
    model_interp.eval()
    model_interp = model_interp.to(device)
    return model_interp


def process_image_in_chunks(img, model, chunk_size=512, overlap=32):
    """Process the image in chunks to reduce memory usage."""
    h, w = img.shape[2:]
    chunks = []

    for i in range(0, h, chunk_size - overlap):
        for j in range(0, w, chunk_size - overlap):
            chunk = img[:, :, i:min(i + chunk_size, h), j:min(j + chunk_size, w)]
            with torch.no_grad():
                upscaled_chunk = model(chunk).cpu()
            chunks.append((i, j, upscaled_chunk))

    # Stitch chunks back together
    output = torch.zeros((1, 3, h * 4, w * 4))
    for i, j, chunk in chunks:
        output[:, :, i * 4:min((i + chunk_size) * 4, h * 4), 
               j * 4:min((j + chunk_size) * 4, w * 4)] = chunk

    return output

def process_image(img, model):
    img = img * 1.0 / 255
    img = torch.from_numpy(np.transpose(img[:, :, [2, 1, 0]], (2, 0, 1))).float()
    img_LR = img.unsqueeze(0).to(device)

    output = process_image_in_chunks(img_LR, model)

    output = output.data.squeeze().float().cpu().clamp_(0, 1).numpy()
    output = np.transpose(output[[2, 1, 0], :, :], (1, 2, 0))
    output = (output * 255.0).round().astype(np.uint8)
    return output

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upscale', methods=['POST'])
def upscale():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    alpha = float(request.form.get('alpha', 1.0))  # Default to 1.0 if not provided
    resolution = request.form.get('resolution', '1080p')

    # Define resolution presets
    resolution_map = {
        '1080p': (1920, 1080),
        '4K': (3840, 2160)
    }

    try:
        target_resolution = resolution_map.get(resolution)
        if not target_resolution:
            return jsonify({'error': 'Invalid resolution selected'}), 400

        img = Image.open(file.stream)
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Interpolate model with alpha
        model_interp = interpolate_model(alpha)
        output = process_image(img, model_interp)

        # Resize output to target resolution (preserving aspect ratio)
        scale_factor = 2 if resolution == '1080p' else 4
        new_w = output.shape[1] * scale_factor
        new_h = output.shape[0] * scale_factor
        output = cv2.resize(output, (new_w, new_h), interpolation=cv2.INTER_CUBIC)


        # Prepare image for web
        output_img = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
        buffered = BytesIO()
        output_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({'image': img_str})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
