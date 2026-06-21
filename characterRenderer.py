import freetype
import numpy as np
from paddleocr import PaddleOCR

# 1. Initialize PaddleOCR targeting ONLY the recognition submodule
ocr = PaddleOCR(
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_recognition_batch_size=128,   # High batch throughput
    device="gpu:0",
)

# 2. Prioritized Font Stack
FONT_STACK = [
    "NotoSerifSC-VF.otf",
    "NotoSerifTC-VF.otf",
    "NotoSerifHK-VF.otf",
    "HanaMinB.ttf",
    "BabelStoneHan.tff",
    "unifont-17.0.04.otf"
]

FONT_SIZE = 48
pixel_size = 64

# Pre-load and cache all font faces to maximize performance
loaded_faces = []
for font_path in FONT_STACK:
    try:
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, FONT_SIZE)
        loaded_faces.append(face)
    except Exception as e:
        print(f"Warning: Missing font file or failed to load {font_path}: {e}")

# Pre-allocate a single canvas matrix to avoid memory thrashing
canvas = np.full((pixel_size, pixel_size, 3), 255, dtype=np.uint8)

# All target CJK ranges
cjk_ranges = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # Extension A
    (0x20000, 0x2A6DF),  # Extension B
    (0x2A700, 0x2B73F),  # Extension C
    (0x2B740, 0x2B81F),  # Extension D
    (0x2B820, 0x2CEAF),  # Extension E
    (0x2CEB0, 0x2EBEF),  # Extension F
    (0x30000, 0x3134F),  # Extension G
    (0x31350, 0x323AF),  # Extension H
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
]

def run_font_stack_ocr_pipeline(batch_size=128):
    batch_images = []
    batch_chars = []
    
    for start, end in cjk_ranges:
        for code_point in range(start, end + 1):
            
            # --- FONT STACK FALLBACK LOGIC ---
            selected_face = None
            for face in loaded_faces:
                # get_char_index() instantly reads the font's internal cmap table.
                # It returns 0 if the glyph does not exist in this font face.
                if face.get_char_index(code_point) != 0:
                    selected_face = face
                    break  # Found a valid font! Break out of the stack loop.
            
            # If all fonts in your stack lack this character, skip it entirely
            if selected_face is None:
                continue
            
            char = chr(code_point)
            
            try:
                # Render using the successfully matched fallback font
                selected_face.load_char(char, freetype.FT_LOAD_RENDER)
                bitmap = selected_face.glyph.bitmap
                h, w = bitmap.rows, bitmap.width
                
                # Reset master canvas
                canvas.fill(255)
                
                if h > 0 and w > 0:
                    bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape(h, w)
                    
                    # Compute perfect pixel_sizexpixel_size centering
                    offset_y = max(0, (pixel_size - h) // 2)
                    offset_x = max(0, (pixel_size - w) // 2)
                    
                    render_h = min(h, pixel_size - offset_y)
                    render_w = min(w, pixel_size - offset_x)
                    
                    inverted_glyph = 255 - bitmap_array[:render_h, :render_w]
                    
                    # Blit across all channels
                    canvas[offset_y:offset_y+render_h, offset_x:offset_x+render_w, :] = inverted_glyph[:, :, np.newaxis]
                
                batch_images.append(canvas.copy())
                batch_chars.append(char)
                
            except Exception:
                continue
            
            # Fire batch inference
            if len(batch_images) == batch_size:
                predictions = ocr.predict(batch_images)
                for original, pred in zip(batch_chars, predictions):
                    print(original)
                    print(pred['rec_texts'])
                    # Process results here (e.g., print or log mismatches)
                    # print(f"Char: {original} -> OCR: {pred_text} ({confidence:.2f})")
                
                batch_images.clear()
                batch_chars.clear()
                
    # Flush remaining data in the final partial batch
    if batch_images:
        predictions = ocr.predict(batch_images)
        for original, pred in zip(batch_chars, predictions):
            pred_text, confidence = pred
            # print(f"Char: {original} -> OCR: {pred_text} ({confidence:.2f})")

if __name__ == "__main__":
    run_font_stack_ocr_pipeline(batch_size=128)