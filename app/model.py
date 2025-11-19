from typing import Dict, List, Optional
#import union functionality
from typing import Union

from transformers import pipeline

# Zero-shot classifier (multilingual MiniLM)
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/multilingual-MiniLMv2-L6-mnli-xnli",
)


def classify_text_tags(
    text: str,
    tags: List[str],
    *,
    multi_label: bool = False,
    hypothesis_template: Optional[str] = None,
) -> Dict[str, float]:
    """
    Classify a text against a list of tags and return probabilities.

    Args:
        text: The input text (e.g., extracted from a PDF).
        tags: Candidate labels to score.
        multi_label: If True, independent probabilities per tag; if False, softmax over tags.
        hypothesis_template: Optional template for NLI prompts (e.g., "This text is about {}.").

    Returns:
        Mapping tag -> probability (score) as floats.
    """
    if not tags:
        raise ValueError("'tags' must be a non-empty list of labels")

    if hypothesis_template:
        result = classifier(
            text,
            tags,
            multi_label=multi_label,
            hypothesis_template=hypothesis_template,
        )
    else:
        result = classifier(text, tags, multi_label=multi_label)

    labels = result.get("labels", [])
    scores = result.get("scores", [])
    return {label: float(score) for label, score in zip(labels, scores)}


# a function that calls the classify_text_tags from app/model.py on all extracted texts
def classify_documents_texts(
    texts: Dict[str, str],
    tags: list[str],
    multi_label: bool = False,
    hypothesis_template: Union[None, str] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Classify multiple documents' texts against a list of tags.

    Args:
        texts: Mapping of document name to extracted text.
        tags: Candidate labels to score.
        multi_label: If True, independent probabilities per tag; if False, softmax over tags.
        hypothesis_template: Optional template for NLI prompts.

    Returns:
        Mapping of document name to tag probabilities.
    """
    from model import classify_text_tags

    results: Dict[str, Dict[str, float]] = {}
    for doc_name, content in texts.items():
        probs = classify_text_tags(
            content,
            tags,
            multi_label=multi_label,
            hypothesis_template=hypothesis_template,
        )
        results[doc_name] = probs
    return results

# define which functions are available for import
__all__ = ["classifier", "classify_text_tags", "classify_documents_texts"]


if __name__ == "__main__":
    demo_text = "Angela Merkel ist eine Politikerin in Deutschland und Vorsitzende der CDU"
    demo_labels = ["politics", "economy", "entertainment", "environment"]
    probs = classify_text_tags(demo_text, demo_labels, multi_label=False)
    print(probs)


