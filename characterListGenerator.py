import itertools

# Define the Unicode blocks as (start, end) tuples
cjk_ranges = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs (Common)
    (0x3400, 0x4DBF),    # CJK Unified Ideographs Extension A (Rare)
    (0x20000, 0x2A6DF),  # CJK Unified Ideographs Extension B (Rare, historic)
    (0x2A700, 0x2B73F),  # CJK Unified Ideographs Extension C (Rare, historic)
    (0x2B740, 0x2B81F),  # CJK Unified Ideographs Extension D (Uncommon, some in current use)
    (0x2B820, 0x2CEAF),  # CJK Unified Ideographs Extension E (Rare, historic)
    (0x2CEB0, 0x2EBEF),  # CJK Unified Ideographs Extension F (Rare, historic)
    (0x30000, 0x3134F),  # CJK Unified Ideographs Extension G (Rare, historic)
    (0x31350, 0x323AF),  # CJK Unified Ideographs Extension H (Rare, historic)
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs (Duplicates, unifiable variants...)
#    (0x2F800, 0x2FA1F),  # CJK Compatibility Ideographs Supplement (Unifiable variants)
]

# Loops through every character code point sequentially
for code_point in itertools.chain.from_iterable(range(start, end + 1) for start, end in cjk_ranges):
    print(chr(code_point))