import os, time
from collections import defaultdict, deque
from flask import Flask, jsonify, request
from bot import FAQBot

app = Flask(__name__, static_folder="static", static_url_path="")
bot = FAQBot(os.path.join(os.path.dirname(__file__), "faqs.json"))
MAX_LEN, LIMIT, WINDOW = 500, 40, 60
_hits = defaultdict(deque)

def limited(ip):
    now, q = time.time(), _hits[ip]
    while q and now - q[0] > WINDOW: q.popleft()
    if len(q) >= LIMIT: return True
    q.append(now); return False

@app.get("/")
def index(): return app.send_static_file("index.html")

@app.get("/api/info")
def info():
    return jsonify(name=bot.name, suggestions=[f["question"] for f in bot.faqs[:6]], total=len(bot.faqs))

@app.post("/api/chat")
def chat():
    if limited(request.remote_addr):
        return jsonify(error="You're sending messages too fast. Please wait a moment."), 429
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("message"), str):
        return jsonify(error="Send a JSON body with a text 'message'."), 400
    msg = " ".join(body["message"].split())          # collapse whitespace/newlines
    if not msg: return jsonify(error="Type a question first."), 400
    if len(msg) > MAX_LEN: return jsonify(error=f"Message is too long. Limit is {MAX_LEN} characters."), 413
    try:
        return jsonify(bot.reply(msg))
    except Exception:
        app.logger.exception("chat failed")
        return jsonify(error="Something went wrong on the server."), 500

@app.errorhandler(404)
def nf(_): return jsonify(error="Not found."), 404
@app.errorhandler(405)
def na(_): return jsonify(error="Method not allowed."), 405

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)))
