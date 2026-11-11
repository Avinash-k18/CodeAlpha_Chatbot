# FAQ Chatbot (ShopEase Help)

NLP pipeline: lowercase -> synonym/phrase map -> NLTK tokenize + stopwords -> typo correction -> Porter stemming
-> TF-IDF (word 1-2 grams + character 3-5 grams) -> cosine similarity -> best FAQ answer.

## Run
    python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    python app.py          # open http://localhost:5001
    python test_bot.py     # accuracy check

## Change the topic
Edit `faqs.json` (question, answer, keywords = alternative phrasings). No code change needed.

## API
- GET  /api/info
- POST /api/chat  {"message": "How do I track my order?"}
