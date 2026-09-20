import os
import sys
import torch
import torchvision.models as models
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/test_images"))
bird_img = os.path.join(DATA_DIR, "birds/sparrow_distant.jpg")
insect_img = os.path.join(DATA_DIR, "insects/butterfly_monarch.jpg")

print("--- Testing Torchvision ResNet50 / MobileNetV3 Pretrained ImageNet Weights ---")

# Pretrained torchvision ResNet50 with ImageNet 1k (has bird species: house finch, indigo bunting, robin, jay, etc., and insect species: monarch, bee, ant, dragonfly, etc.)
weights = models.ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights).eval()
preprocess = weights.transforms()
categories = weights.meta["categories"]

def predict_img(img_path):
    img = Image.open(img_path).convert("RGB")
    tensor = preprocess(img).unsqueeze(0)
    with torch.no_grad():
        output = model(tensor)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
    
    top5_prob, top5_catid = torch.topk(probabilities, 5)
    results = []
    for i in range(top5_prob.size(0)):
        cat_name = categories[top5_catid[i]]
        score = top5_prob[i].item()
        results.append((cat_name, score))
    return results

print(f"\nBird image '{os.path.basename(bird_img)}':")
for label, score in predict_img(bird_img):
    print(f"  {label} -> {score*100:.1f}%")

print(f"\nInsect image '{os.path.basename(insect_img)}':")
for label, score in predict_img(insect_img):
    print(f"  {label} -> {score*100:.1f}%")
