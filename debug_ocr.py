import pytesseract
from PIL import Image
import io
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def debug_ocr():
    print("=== OCR Debug Test ===")
    
    # Test 1: Check if Tesseract works
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract Version: {version}")
    except Exception as e:
        print(f"✗ Tesseract Error: {e}")
        return
    
    # Test 2: Create a simple test image
    try:
        img = Image.new('RGB', (400, 200), color='white')
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        
        # Use default font
        draw.text((50, 80), "ELECTRICITY 850 kWh", fill='black')
        draw.text((50, 110), "DIESEL 150 liters", fill='black')
        
        # Save test image
        img.save('debug_test.png')
        print("✓ Test image created: debug_test.png")
        
        # Test 3: Try OCR on the test image
        text = pytesseract.image_to_string(img)
        print("✓ OCR Test Result:")
        print(f"Extracted: '{text.strip()}'")
        
    except Exception as e:
        print(f"✗ Image processing error: {e}")

if __name__ == "__main__":
    debug_ocr()