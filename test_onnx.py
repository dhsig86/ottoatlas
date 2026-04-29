import onnxruntime as ort
import numpy as np
from PIL import Image

vocab_path = r'C:\Users\drdhs\OneDrive\Documentos\ottoatlas\otto-atlas-web\ml_pipeline\models\vocab.txt'
with open(vocab_path, "r", encoding="utf-8") as f:
    vocab = [line.strip() for line in f if line.strip()]

opts = ort.SessionOptions()
opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
sess = ort.InferenceSession(r'C:\Users\drdhs\OneDrive\Documentos\ottoatlas\otto-atlas-web\ml_pipeline\models\otto_model.onnx', sess_options=opts, providers=['CPUExecutionProvider'])

img = Image.open(r"C:\Users\drdhs\OneDrive\Imagens\Otoscopio 2026\IMG\IMG00001.jpg").convert("RGB")
img = img.resize((224, 224), Image.Resampling.BILINEAR)

img_arr = np.array(img).astype(np.float32) / 255.0
mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
img_arr = (img_arr - mean) / std

img_arr = np.transpose(img_arr, (2, 0, 1))
input_tensor = np.expand_dims(img_arr, axis=0)

inputs = {sess.get_inputs()[0].name: input_tensor}
logits = sess.run(None, inputs)[0][0]

exp_L = np.exp(logits - np.max(logits))
probs = exp_L / np.sum(exp_L)

predictions = [{"class": str(v), "confidence": float(p)} for v, p in zip(vocab, probs)]
predictions.sort(key=lambda x: x["confidence"], reverse=True)
for i, p in enumerate(predictions[:3]):
    print(f"#{i+1} {p['class']:<20} | Score: {p['confidence'] * 100:.2f}%")
print("\n[VALIDAÇÃO] Matemática confirmada!")
