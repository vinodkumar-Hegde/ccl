import fitz
import pytesseract
from PIL import Image


def extract_text_from_pdf(pdf_path: str):
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page in doc:
            text += page.get_text()

        doc.close()

        return text.strip()

    except Exception as e:
        print("PDF extraction error:", e)
        return ""


def extract_text_from_image(image_path: str):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)

        return text.strip()

    except Exception as e:
        print("Image OCR error:", e)
        return ""


def extract_text_with_fallback(file_path: str):
    if file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    return extract_text_from_image(file_path)