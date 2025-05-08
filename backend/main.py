import io
import os
import uvicorn
import numpy as np
import tensorflow as tf
from PIL import Image
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Membuat instance FastAPI
app = FastAPI()

# Izinkan request dari Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Load model
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / 'model' / 'best_transfer.h5'

if os.path.exists(MODEL_PATH):
    model = tf.keras.models.load_model(str(MODEL_PATH))
else:
    raise FileNotFoundError(f"Model tidak ditemukan di {MODEL_PATH}")

# Mapping indeks : label
labels = ["paper", "rock", "scissors"]
UNKNOWN_LABEL = "unknown"

# Threshold confidence minimum
THRESHOLD = 0.6

def preprocess_pipeline(image: Image.Image, IMG_SIZE=(224, 224)) -> np.ndarray:
    """
    Fungsi untuk melakukan preprocessing pada gambar input.
    - Melakukan resize gambar ke IMG_SIZE.
    - Mengubah gambar menjadi array bertipe float32.
    - Melakukan rescaling pixel dari [0,255] ke [0,1].
    """
    # Resize gambar ke 224x224
    image = image.resize(IMG_SIZE)
    
    # Ubah ke array numpy dan konversi ke float32
    arr = np.array(image, dtype=np.float32)
    
    # Rescale pixel dari [0,255] ke [0,1]
    arr = arr / 255.0
    
    return arr

# Endpoint untuk menerima input dan menghasilkan prediksi
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    try:
        # Baca file gambar
        contents = await file.read()
        
        # Buka dan konversi gambar ke RGB
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        
        # Preprocessing gambar
        x = preprocess_pipeline(image)
        x = np.expand_dims(x, axis=0)
        
        # Prediksi menggunakan model
        predictions = model.predict(x)
        best_index = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][best_index])
        
        # Tentukan label berdasarkan threshold
        if confidence < THRESHOLD:
            label = UNKNOWN_LABEL
        else:
            label = labels[best_index]
        
        return {"label": label, "confidence": confidence}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
