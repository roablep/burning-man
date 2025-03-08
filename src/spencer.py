from PIL import Image, ImageFilter, ImageOps
import numpy as np
import cv2

image_path = "/Users/peter/Downloads/"
image = Image.open(image_path + "7D1A9004.jpg")

# Convert image to grayscale
gray_image = ImageOps.grayscale(image)

# Convert PIL image to numpy array for OpenCV processing
image_np = np.array(gray_image)

# Apply edge detection to extract strong contours for an angular, high-contrast style
thre1=50
thre2=150
edges = cv2.Canny(image_np, threshold1=thre1, threshold2=thre2)

# Convert edges back to PIL image
edges_pil = Image.fromarray(edges)

# Save processed image for preview
processed_path = f"{image_path}spencer_edges_{thre1}_{thre2}.jpg"
edges_pil.save(processed_path)

print(processed_path)



# ----

import cv2
import matplotlib.pyplot as plt

# Reload Spencer's image
image = cv2.imread(image_path + "7D1A9004.jpg", cv2.IMREAD_GRAYSCALE)


# Apply a stronger edge detection with adjusted thresholds for a bolder look
edges_strong = cv2.Canny(image, threshold1=150, threshold2=250)

# Convert edges to a black-and-white silhouette
_, binary_silhouette = cv2.threshold(edges_strong, 128, 255, cv2.THRESH_BINARY_INV)

# Save the processed image
silhouette_path = f"{image_path}spencer_silhouette.jpg"
cv2.imwrite(silhouette_path, binary_silhouette)

# Display the processed image for user feedback
silhouette_path

