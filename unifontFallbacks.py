import freetype

# Prioritized Font Stack — the LAST entry is treated as the "fallback" font.
# Any character that isn't covered by any font BEFORE the last one, but IS
# covered by the last one, counts as a "unicode fallback" character.
FONT_STACK = [
    "NotoSerifSC-VF.otf",
    "NotoSerifTC-VF.otf",
    "NotoSerifHK-VF.otf",
    "HanaMinB.ttf",
    "BabelStoneHan.ttf",
    "unifont-17.0.04.otf"
]

FONT_SIZE = 48

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
    (0xF900, 0xFA6D),    # CJK Compatibility Ideographs
    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement
]


def load_faces(font_stack):
    """Load and cache all font faces. Returns list of (font_path, face) for fonts that loaded successfully."""
    loaded = []
    for font_path in font_stack:
        try:
            face = freetype.Face(font_path)
            face.set_pixel_sizes(0, FONT_SIZE)
            loaded.append((font_path, face))
        except Exception as e:
            print(f"Warning: Missing font file or failed to load {font_path}: {e}")
    return loaded


def find_fallback_characters(loaded_faces, ranges, fallback_font_name=None):
    """
    Walk every code point in `ranges` and determine which font in the stack
    covers it. Returns a list of (code_point, char) tuples for every
    character whose ONLY coverage comes from the fallback font
    (by default, the last font in the stack).
    """
    if not loaded_faces:
        return []

    if fallback_font_name is None:
        fallback_font_name, fallback_face = loaded_faces[-1]
    else:
        fallback_face = None
        for name, face in loaded_faces:
            if name == fallback_font_name:
                fallback_face = face
                break
        if fallback_face is None:
            raise ValueError(f"fallback_font_name '{fallback_font_name}' not found in loaded_faces")

    fallback_chars = []

    for start, end in ranges:
        for code_point in range(start, end + 1):
            selected_font_name = None

            for font_path, face in loaded_faces:
                if face.get_char_index(code_point) != 0:
                    selected_font_name = font_path
                    break  # first font in stack that covers this code point wins

            if selected_font_name == fallback_font_name:
                fallback_chars.append((code_point, chr(code_point)))

    return fallback_chars


if __name__ == "__main__":
    loaded_faces = load_faces(FONT_STACK)

    if not loaded_faces:
        print("❌ Critical Error: No fonts could be loaded. Place font files in the script folder.")
    else:
        print(f"Loaded {len(loaded_faces)} / {len(FONT_STACK)} fonts.")
        print(f"Fallback font (last in stack): {loaded_faces[-1][0]}")
        print("-" * 50)

        fallback_chars = find_fallback_characters(loaded_faces, cjk_ranges)

        print(f"\n{len(fallback_chars)} characters fell back to {loaded_faces[-1][0]}:\n")
        for code_point, char in fallback_chars:
            print(f"U+{code_point:05X}  {char}")

        # Also write to a file for easier downstream use
        out_path = "fallback_characters.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for code_point, char in fallback_chars:
                f.write(f"U+{code_point:05X}\t{char}\n")
        print(f"\nWrote {len(fallback_chars)} entries to {out_path}")