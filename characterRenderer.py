import freetype
import numpy as np
from scipy.ndimage import gaussian_filter
from paddleocr import TextRecognition
import time

# 1. Initialize PaddleOCR targeting ONLY the recognition submodule
ocr = TextRecognition(model_name="PP-OCRv5_server_rec", device="gpu:0")

# 2. Prioritized Font Stack
FONT_STACK = [
    "NotoSerifSC-VF.otf",
    "NotoSerifTC-VF.otf",
    "NotoSerifHK-VF.otf",
    "HanaMinB.ttf",
    "BabelStoneHan.ttf",
    "unifont-17.0.04.otf"
]

FONT_SIZE = 48
pixel_size = 64

# 3. Augmentation settings list — each dict is one variant applied to every glyph.
#    blur_sigma: stddev for gaussian blur (0 = no blur)
#    noise_std:  stddev of additive Gaussian noise in pixel intensity (0 = no noise)
#    label:      tag appended to output so you can tell variants apart
#    repeats:    how many independent times to run this config per character
#                (deterministic configs only need 1; noisy configs benefit from more)
AUGMENTATION_CONFIGS = [
    {"label": "clean",        "blur_sigma": 0.0, "noise_std": 0,  "repeats": 1},
    {"label": "light_blur",   "blur_sigma": 0.5, "noise_std": 0,  "repeats": 1},
    {"label": "heavy_blur",   "blur_sigma": 1.5, "noise_std": 0,  "repeats": 1},
    {"label": "light_noise",  "blur_sigma": 0.0, "noise_std": 8,  "repeats": 2},
    {"label": "medium_noise",  "blur_sigma": 0.0, "noise_std": 20, "repeats": 4},
    {"label": "heavy_noise",  "blur_sigma": 0.0, "noise_std": 50, "repeats": 6},
    {"label": "blur_noise",   "blur_sigma": 0.8, "noise_std": 12, "repeats": 5},
]

# Pre-load and cache all font faces to maximize performance
loaded_faces = []
for font_path in FONT_STACK:
    try:
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, FONT_SIZE)
        loaded_faces.append(face)
    except Exception as e:
        print(f"Warning: Missing font file or failed to load {font_path}: {e}")

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



def render_base_glyph(face, char):
    """Render one char to a clean (pixel_size, pixel_size) grayscale canvas (uint8, white bg)."""
    face.load_char(char, freetype.FT_LOAD_RENDER)
    bitmap = face.glyph.bitmap
    h, w = bitmap.rows, bitmap.width

    canvas = np.full((pixel_size, pixel_size), 255, dtype=np.uint8)

    if h > 0 and w > 0:
        bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape(h, w)

        offset_y = max(0, (pixel_size - h) // 2)
        offset_x = max(0, (pixel_size - w) // 2)

        render_h = min(h, pixel_size - offset_y)
        render_w = min(w, pixel_size - offset_x)

        inverted_glyph = 255 - bitmap_array[:render_h, :render_w]
        canvas[offset_y:offset_y + render_h, offset_x:offset_x + render_w] = inverted_glyph

    return canvas


def apply_augmentation(base_canvas, blur_sigma=0.0, noise_std=0.0):
    """Apply blur and/or noise to a single-channel base canvas, return a 3-channel uint8 image."""
    img = base_canvas.astype(np.float32)

    if blur_sigma > 0:
        img = gaussian_filter(img, sigma=blur_sigma)

    if noise_std > 0:
        noise = np.random.normal(0, noise_std, img.shape).astype(np.float32)
        img = img + noise

    img = np.clip(img, 0, 255).astype(np.uint8)
    return np.repeat(img[:, :, np.newaxis], 3, axis=2)


def run_font_stack_ocr_pipeline(batch_size=128, augmentations=AUGMENTATION_CONFIGS):
    t0 = time.time()
    batch_images = []
    batch_meta = []  # (char, augmentation_label) pairs, parallel to batch_images

    def flush_batch():
        nonlocal t0
        if not batch_images:
            return
        t1 = time.time()
        predictions = ocr.predict(input=batch_images, batch_size=batch_size)
        t2 = time.time()
        print(f"augment: {t1-t0:.3f}s | predict: {t2-t1:.3f}s")
        for (original_char, aug_label), pred in zip(batch_meta, predictions):
            print(f"{original_char} [{aug_label}]")
            print(pred['rec_text'])
        batch_images.clear()
        batch_meta.clear()
        t0 = time.time()

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
                base_canvas = render_base_glyph(selected_face, char)
            except Exception:
                continue

            # Generate every augmented variant for this character
            for cfg in augmentations:
                for rep in range(cfg.get("repeats", 1)):
                    try:
                        aug_img = apply_augmentation(
                            base_canvas,
                            blur_sigma=cfg.get("blur_sigma", 0.0),
                            noise_std=cfg.get("noise_std", 0.0),
                        )
                    except Exception:
                        continue

                    batch_images.append(aug_img)
                    batch_meta.append((char, cfg.get("label", "variant")))

                    # Fire batch inference whenever the batch fills up
                    if len(batch_images) == batch_size:
                        flush_batch()

    # Flush remaining data in the final partial batch
    flush_batch()


if __name__ == "__main__":
    run_font_stack_ocr_pipeline(batch_size=512)