from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)


def extract_text_paddle(image_path: str):
    result = ocr.ocr(image_path)

    extracted_lines = []

    if result:
        for block in result:
            if block:
                for line in block:
                    try:
                        text = line[1][0]
                        extracted_lines.append(text)
                    except:
                        pass

    return "\n".join(extracted_lines)
