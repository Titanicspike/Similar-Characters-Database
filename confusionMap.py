from collections import defaultdict

# confusion_map[source_char][predicted_char] = {"count": int, "score_sum": float}
#
# source_char:    the true character we rendered/augmented
# predicted_char: what OCR actually returned for that augmented image
# count:          how many times this (source -> predicted) pair occurred
# score_sum:      running total of OCR confidence scores for this pair
#                 (divide by count to get the average confidence)
confusion_map = defaultdict(lambda: defaultdict(lambda: {"count": 0, "score_sum": 0.0}))


def add_confusion(source_char, predicted_char, score=1.0):
    """Record one OCR prediction result into the confusion map.

    source_char:    the character you rendered (ground truth)
    predicted_char: the character OCR returned (pred['rec_text'])
    score:          OCR confidence for this prediction (pred['rec_score'] if available, else 1.0)
    """
    entry = confusion_map[source_char][predicted_char]
    entry["count"] += 1
    entry["score_sum"] += score


def get_average_confusion(source_char, predicted_char):
    """Convenience lookup: average OCR confidence for a specific source->predicted pair."""
    entry = confusion_map.get(source_char, {}).get(predicted_char)
    if entry is None or entry["count"] == 0:
        return None
    return entry["score_sum"] / entry["count"]


def to_plain_dict(cm):
    """Convert the defaultdict structure into a plain dict (needed before JSON serialization,
    since defaultdicts with lambda factories aren't directly JSON-serializable)."""
    return {
        src: {tgt: dict(stats) for tgt, stats in targets.items()}
        for src, targets in cm.items()
    }