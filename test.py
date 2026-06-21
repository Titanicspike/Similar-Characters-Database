import freetype
import numpy as np
import matplotlib.pyplot as plt

# 1. Prioritized Font Stack (Adjust paths if necessary)
FONT_STACK = [
    "NotoSerifSC-VF.otf",
    "NotoSerifTC-VF.otf",
    "NotoSerifHK-VF.otf",
    "HanaMinB.ttf",
    "BabelStoneHan.tff",
    "unifont-17.0.04.otf"
]

FONT_SIZE = 64
size = 64

# Pre-load and cache all font faces
loaded_faces = []
for font_path in FONT_STACK:
    try:
        face = freetype.Face(font_path)
        face.set_pixel_sizes(0, FONT_SIZE)
        loaded_faces.append(face)
        print(f"Successfully loaded: {font_path}")
    except Exception as e:
        print(f"Skipped font {font_path}: {e}")

print("-" * 50)

# Pre-allocate a single canvas matrix (White background)
canvas = np.full((size, size, 3), 255, dtype=np.uint8)


def gaussian_kernel1d(sigma, radius=None):
    if sigma <= 0:
        return np.array([1.0], dtype=np.float32)
    if radius is None:
        radius = int(3 * sigma + 0.5)
    x = np.arange(-radius, radius + 1, dtype=np.float32)
    kernel = np.exp(-0.5 * (x / float(sigma)) ** 2)
    kernel /= kernel.sum()
    return kernel


def gaussian_blur(image, sigma=1.5):
    """Apply a separable Gaussian blur to a HxWx3 uint8 image using numpy only."""
    if sigma <= 0:
        return image
    kernel = gaussian_kernel1d(sigma)
    pad = kernel.size // 2
    out = np.empty_like(image, dtype=np.float32)

    for c in range(image.shape[2]):
        channel = image[..., c].astype(np.float32)

        # Horizontal pass
        padded_h = np.pad(channel, ((0, 0), (pad, pad)), mode='reflect')
        horiz = np.apply_along_axis(lambda r: np.convolve(r, kernel, mode='valid'), axis=1, arr=padded_h)

        # Vertical pass
        padded_v = np.pad(horiz, ((pad, pad), (0, 0)), mode='reflect')
        blurred = np.apply_along_axis(lambda carr: np.convolve(carr, kernel, mode='valid'), axis=0, arr=padded_v)

        out[..., c] = blurred

    out = np.clip(out, 0, 255).astype(np.uint8)
    return out

def test_single_character():
    # Prompt user for input
    user_input = input("Enter a single CJK character to test: ").strip()
    
    if not user_input:
        print("No input detected.")
        return
        
    char = user_input[0] # Take only the first character
    code_point = ord(char)
    print(f"Character: {char} | Unicode Code Point: U+{code_point:04X}")
    
    # Fallback Font Stack matching logic
    selected_face = None
    selected_font_name = None
    
    for font_path, face in zip(FONT_STACK, loaded_faces):
        if face.get_char_index(code_point) != 0:
            selected_face = face
            selected_font_name = font_path
            break
            
    if selected_face is None:
        print("❌ Error: Character not supported by any font in your stack!")
        return
        
    print(f"🎯 Matched Font: {selected_font_name}")
    
    try:
        # Load and render the glyph mask
        selected_face.load_char(char, freetype.FT_LOAD_RENDER)
        bitmap = selected_face.glyph.bitmap
        h, w = bitmap.rows, bitmap.width
        
        # Reset master canvas
        canvas.fill(255)
        
        if h > 0 and w > 0:
            bitmap_array = np.array(bitmap.buffer, dtype=np.uint8).reshape(h, w)
            
            # Geometric centering math
            offset_y = max(0, (size - h) // 2)
            offset_x = max(0, (size - w) // 2)

            render_h = min(h, size - offset_y)
            render_w = min(w, size - offset_x)
            
            # Invert colors to match expected OCR input (Black text on White)
            inverted_glyph = 255 - bitmap_array[:render_h, :render_w]
            
            # Blit across all channels
            canvas[offset_y:offset_y+render_h, offset_x:offset_x+render_w, :] = inverted_glyph[:, :, np.newaxis]
            print(f"Rendered glyph footprint: {w}x{h} pixels (centered at x={offset_x}, y={offset_y})")
        else:
            print("⚠️ Warning: Character layout has no pixel footprint (whitespace character).")

        # --- Display to Computer Screen (apply small Gaussian blur) ---
        try:
            blurred_canvas = gaussian_blur(canvas, sigma=2)
        except NameError:
            # If the blur helper isn't present for any reason, fall back to raw canvas
            blurred_canvas = canvas

        plt.figure(figsize=(4, 4))
        plt.imshow(blurred_canvas)
        plt.title(f"Rendered Box (sizexsize)\nChar: {char} (U+{code_point:04X})")
        plt.axis('on')  # Shows pixel boundaries 0 to size
        plt.grid(color='gray', linestyle=':', linewidth=0.5)
        plt.show()

    except Exception as e:
        print(f"❌ Failed to render glyph: {e}")

if __name__ == "__main__":
    if not loaded_faces:
        print("❌ Critical Error: No fonts could be loaded. Place font files in the script folder.")
    else:
        test_single_character()