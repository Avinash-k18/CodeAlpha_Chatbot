"""FAQ matching engine: NLTK preprocessing + TF-IDF (word + character) + cosine similarity."""
import difflib, json, re
import numpy as np
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import linear_kernel

# Stopwords: use NLTK's list; download it if missing; fall back to scikit-learn's list when offline.
try:
    import nltk
    from nltk.corpus import stopwords
    try:
        STOP = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords", quiet=True)
        STOP = set(stopwords.words("english"))
except Exception:
    STOP = set(ENGLISH_STOP_WORDS)
STOP -= {"not", "no"}          # negations carry meaning ("not working")

TOKENIZER = RegexpTokenizer(r"[a-z0-9]+")
STEMMER = PorterStemmer()

ANSWER_T, SUGGEST_T, MARGIN = 0.30, 0.14, 0.08   # confident answer / "did you mean" / gap needed over 2nd best

# Phrase and synonym normalisation (applied before tokenizing)
PHRASES = [
    (r"\b(send|sent|give|take) (it |them |the \w+ )?back\b", " return "),
    (r"\bmoney back\b|\bpaid back\b", " refund "),
    (r"\b(talk|speak|chat) (to|with)\b", " contact "),
    (r"\b(google ?pay|gpay|phone ?pe|paytm|bhim)\b", " upi "),
    (r"\b(parcel|package|shipment|consignment)\b", " order "),
    (r"\b(usa|america|uk|canada|dubai|abroad|overseas|foreign|outside india)\b", " international "),
    (r"\b(human|agent|representative|real person|phone number|helpline)\b", " contact support "),
    (r"\b(buy|purchase|bought|purchased)\b", " order "),
]

SMALL_TALK = [
    (r"^(hi+|hello+|hey+|hola|namaste|good (morning|afternoon|evening))\b",
     "Hello! I can answer questions about orders, shipping, returns, payments and your account. What would you like to know?"),
    (r"^(thanks?|thank you|thx|ty|great|awesome|ok(ay)?)\b",
     "You're welcome! Ask me anything else if you need."),
    (r"^(bye|goodbye|see you|good night|exit|quit)\b",
     "Goodbye! Have a great day."),
    (r"\b(who are you|what are you|your name|what can you do|help)\b",
     "I'm an FAQ assistant. Ask me about orders, delivery, returns, refunds, payments or your account, and I'll find the best answer."),
]


VOCAB = set()


def normalize(text):
    text = text.lower().replace("'", "")
    for pat, rep in PHRASES:
        text = re.sub(pat, rep, text)
    return [t for t in TOKENIZER.tokenize(text) if t not in STOP and (len(t) > 1 or t.isdigit())]


def preprocess(text, correct=False):
    """lowercase -> phrase/synonym map -> tokenize -> drop stopwords -> (fix typos) -> stem"""
    out = []
    for t in normalize(text):
        if correct and len(t) > 3 and t not in VOCAB:
            m = difflib.get_close_matches(t, VOCAB, n=1, cutoff=0.75)
            t = m[0] if m else t
        out.append(STEMMER.stem(t))
    return " ".join(out)


class FAQBot:
    def __init__(self, path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        self.name = data.get("bot_name", "FAQ Bot")
        self.faqs = data["faqs"]
        texts = [f["question"] + " " + " ".join(f.get("keywords", [])) + " " + f["answer"] for f in self.faqs]
        for t in texts:
            VOCAB.update(normalize(t))
        docs = [preprocess(t) for t in texts]
        self.word = TfidfVectorizer(ngram_range=(1, 2)).fit(docs)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit(docs)   # helps with typos
        self.W, self.C = self.word.transform(docs), self.char.transform(docs)

    def scores(self, query):
        q = preprocess(query, correct=True)
        if not q:
            return None
        return 0.6 * linear_kernel(self.word.transform([q]), self.W)[0] + \
               0.4 * linear_kernel(self.char.transform([q]), self.C)[0]

    def reply(self, message):
        words = message.split()
        if len(words) <= 5:
            for pattern, text in SMALL_TALK:
                if re.search(pattern, message.lower().strip(" !.?")):
                    return {"type": "smalltalk", "reply": text}
        s = self.scores(message)
        if s is None:
            return self._fallback("I couldn't find any meaningful words in that. Could you rephrase your question?")
        order = np.argsort(s)[::-1]
        best = order[0]
        runner = s[order[1]] if len(order) > 1 else 0
        if s[best] >= ANSWER_T and (s[best] - runner >= MARGIN or s[best] >= 0.5):
            f = self.faqs[best]
            return {"type": "answer", "reply": f["answer"], "matched": f["question"], "confidence": round(float(s[best]), 2)}
        if s[best] >= SUGGEST_T:
            sugg = [self.faqs[i]["question"] for i in order[:3] if s[i] >= SUGGEST_T]
            return {"type": "suggest", "reply": "I'm not fully sure I understood. Did you mean one of these?", "suggestions": sugg}
        return self._fallback("Sorry, I don't have an answer for that yet.")

    def _fallback(self, text):
        return {"type": "fallback", "reply": text + " You can contact support at support@shopease.example.",
                "suggestions": [f["question"] for f in self.faqs[:3]]}
