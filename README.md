# CJK OCR Confusion Map

A dataset mapping which CJK characters a specific OCR model tends to misread as
which other characters — generated synthetically by rendering individual
characters with font fallback, applying blur/noise augmentations, and running
them through OCR many times to see what comes out.

It was originally built to support fuzzy-matching and human-review
prioritization when transcribing Japanese-colonial-era Taiwanese household
registration documents (日治時期戶籍謄本) for genealogy research, but the
underlying confusion data may be useful for anyone working with OCR on rare,
archaic, or visually similar CJK characters.

## What's in the data

`confusion_map.json` is a nested object:

```json
{
  "橓": {
    "橇": { "count": 5,  "score_sum": 0.91 },
    "瞬": { "count": 13, "score_sum": 3.23 },
    "橛": { "count": 1,  "score_sum": 0.13 }
  }
}
```

- **Top-level key**: the "true" character that was rendered and fed to OCR.
- **Second-level key**: a character OCR actually returned for some rendering
  of the true character.
- **count**: how many of the rendered/augmented variants of the true
  character produced this particular OCR output.
- **score_sum**: the sum of OCR confidence scores (`rec_score`) across those
  `count` predictions. Divide by `count` to get the average confidence for
  that specific (true → predicted) pair.

A character that OCR reads correctly nearly all the time will show a single
entry mapping to itself with a high count and a confidence average close to
1.0. A character OCR struggles with will show multiple entries — including,
often, itself — splitting the count across several plausible-looking
alternatives, frequently at lower confidence.

## How it was generated

1. **Character set**: Unicode CJK Unified Ideographs plus Extensions A–H and
   the CJK Compatibility Ideographs (and supplement) blocks — roughly 98,000
   code points total before filtering, of which a substantial portion are
   genuinely rare/archaic and unassigned reserved code points were excluded.
2. **Rendering**: each character was rendered to a 64×64 grayscale glyph using
   a prioritized font fallback stack (Noto Serif CJK variants, HanaMin,
   BabelStone Han, with Unifont as a last-resort fallback), choosing the
   first font in the stack whose cmap table actually contains the glyph.
3. **Augmentation**: each rendered glyph was put through several
   configurations of Gaussian blur and additive grayscale Gaussian noise
   (e.g. clean, light/heavy blur, light/medium/heavy noise, combined
   blur+noise), with noisy configurations repeated multiple times (since
   noise is randomized per run) to get a more stable read on how OCR behaves
   under that condition rather than relying on a single noisy draw.
4. **OCR**: each augmented image was passed through PaddleOCR's
   `PP-OCRv5_server_rec` text recognition model (GPU inference), and the
   predicted character plus confidence score was recorded against the true
   character.

## Known limitations

- **Single-model, synthetic data.** This reflects the failure modes of one
  specific OCR model (`PP-OCRv5_server_rec`) on synthetically rendered and
  augmented glyphs — not on real scanned documents. Real-world scans have
  ink bleed, paper aging, handwriting, stamps, and scanner artifacts that
  this dataset doesn't simulate. Confusions seen here are a reasonable proxy
  but won't perfectly match what you'd see on an actual historical document.
- **Model-specific, not universal.** A different OCR engine (Tesseract,
  Google Vision, a different PaddleOCR model variant, etc.) may have
  different confusion patterns. This dataset is most directly useful if
  you're also using PP-OCRv5_server_rec or an architecturally similar
  CTC/attention-based CJK recognizer.
- **Font-coverage dependent.** Characters not covered by any font in the
  rendering stack were skipped entirely and don't appear in this dataset.
- **Low-count entries are noisier.** An entry with `count: 1` reflects a
  single OCR run and may not be a stable or meaningful confusion — treat
  high-count entries as more reliable signal than low-count ones.
- **Not a substitute for human review** of historical documents — this is
  meant to help prioritize which characters deserve a closer look or
  support fuzzy search, not to silently "correct" OCR output.

## Suggested uses

- Fuzzy-matching/typo-tolerant search over OCR'd CJK text (e.g. "did this
  document actually say 橫 or 横?").
- Prioritizing which OCR'd characters in a large batch of scanned documents
  are most likely to need manual verification, based on how often a
  character fails to self-recognize across augmented variants.
- As a starting point for building a similar dataset against your own OCR
  model or document conditions.

## License

MIT License

Copyright (c) [2026] [Noah Wang]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

Generated using [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
(`PP-OCRv5_server_rec`), with rendering support from FreeType and the Noto
Serif CJK, HanaMin, BabelStone Han, and Unifont font projects.