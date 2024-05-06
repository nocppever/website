from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
from torchvision import transforms
from PIL import Image
from ocr import Enhanced_OCR_CNN  # Make sure this import points to your model's definition
import string

app = Flask(__name__)
CORS(app)  # Enable CORS if your frontend is served from a different origin

# Load your trained model
model = Enhanced_OCR_CNN()
model.load_state_dict(torch.load('model_ocr.pth', map_location=torch.device('cpu')))
model.eval()

# Define the transformations
transformations = transforms.Compose([
    transforms.Resize((28, 28)),          # Resize the image to 28x28 pixels
    transforms.ToTensor(),                # Convert the image to a PyTorch tensor
    transforms.Normalize((0.5,), (0.5,))  # Normalize the tensor
])

# Define label map as in test.py
label_map = list(string.digits) + list(string.ascii_uppercase) + list(string.ascii_lowercase)

def decode_label(label_index):
    """
    Decode the predicted class index into a character.
    """
    if label_index < len(label_map):
        return label_map[label_index]
    else:
        return "Character not recognized"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        image = Image.open(file.stream).convert('L')  # Convert to grayscale
        image_tensor = transformations(image).unsqueeze(0)  # Apply transformations and add batch dimension

        with torch.no_grad():
            prediction = model(image_tensor)
            _, predicted_idx = torch.max(prediction, 1)
            predicted_char = decode_label(predicted_idx.item())

        return jsonify({'text': predicted_char})
    except Exception as e:
        app.logger.error(f"Error processing the image: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)