import boto3
from PIL import Image, ImageDraw
from io import BytesIO
import os
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox

# Your S3 bucket and region details
S3_REGION = 'us-east-1'
REKOGNITION_REGION = 'us-east-1'
BUCKET = 

def upload_image_to_s3(file_path, bucket, key):

    s3_client = boto3.client('s3', region_name=S3_REGION)
    try:
        s3_client.upload_file(file_path, bucket, key)
        print(f"File {file_path} uploaded to {bucket}/{key}")
        return True
    except Exception as e:
        messagebox.showerror("Upload Error", f"Error uploading file: {e}")
        return False

def detect_labels(bucket, key):

    client = boto3.client('rekognition', region_name=REKOGNITION_REGION)
    try:
        response = client.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10
        )
        return response['Labels']
    except Exception as e:
        messagebox.showerror("Rekognition Error", f"Error detecting labels: {e}")
        return None

def get_image_from_s3(bucket, key):
    """Downloads an image from S3 and opens it with PIL."""
    s3 = boto3.client('s3', region_name=S3_REGION)
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        image_bytes = obj['Body'].read()
        return Image.open(BytesIO(image_bytes))
    except Exception as e:
        messagebox.showerror("Download Error", f"Error downloading image from S3: {e}")
        return None

def draw_bounding_boxes(image, labels):
    """Draws bounding boxes on the image based on detected labels."""
    draw = ImageDraw.Draw(image)
    width, height = image.size

    for label in labels:
        if 'Instances' in label:
            for instance in label['Instances']:
                box = instance['BoundingBox']
                left = width * box['Left']
                top = height * box['Top']
                draw.rectangle(
                    (left, top, left + (width * box['Width']), top + (height * box['Height'])),
                    outline='red',
                    width=3
                )
                text = f"{label['Name']} ({instance['Confidence']:.2f}%)"
                draw.text((left, top - 20), text, fill='red')

    image.show()

def main():
    """Main function to handle file selection, upload, and processing."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Open file dialog to choose an image
    file_path = filedialog.askopenfilename(
        title="Select an image file",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
    )

    if not file_path:
        print("No file selected. Exiting.")
        return

    file_extension = os.path.splitext(file_path)[1]
    unique_key = f'user-uploads/{uuid.uuid4()}{file_extension}'


    if upload_image_to_s3(file_path, BUCKET, unique_key):
        # Detect labels on the uploaded image
        labels = detect_labels(BUCKET, unique_key)
        if labels:
            print("Detected labels:")
            for label in labels:
                print(f"{label['Name']} : {label['Confidence']:.2f}%")
            
            image = get_image_from_s3(BUCKET, unique_key)
            if image:

                draw_bounding_boxes(image, labels)
        else:
            print("No labels detected or an error occurred.")

if __name__ == '__main__':
    main()