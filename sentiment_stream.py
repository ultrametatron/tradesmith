"""
DistilBERT streaming sentiment: headlines processed one-by-one.
"""
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from functools import lru_cache

MODEL = "distilbert-base-uncased-finetuned-sst-2-english"

@lru_cache(maxsize=None)
def _pipeline():
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    return pipeline("sentiment-analysis", model=model, tokenizer=tokenizer,
                    batch_size=1, device=-1, return_all_scores=False)

def score(text: str) -> float:
    """Return sentiment score (+/-)."""
    try:
        r = _pipeline()(text)[0]
        return r["score"] if r["label"] == "POSITIVE" else -r["score"]
    except:
        return 0.0
