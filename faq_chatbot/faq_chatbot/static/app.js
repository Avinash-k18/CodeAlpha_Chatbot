(() => {
  const chat = document.getElementById("chat"), form = document.getElementById("form"),
        msg = document.getElementById("msg"), send = document.getElementById("send");
  let info = {name: "Help Centre", suggestions: []}, busy = false;

  const scroll = () => chat.scrollTo({top: chat.scrollHeight});
  function add(who, text, opts = {}) {
    const row = document.createElement("div"); row.className = `row ${who}${opts.error ? " error" : ""}`;
    const b = document.createElement("div"); b.className = "bubble"; b.textContent = text; row.append(b);
    if (opts.matched) { const m = document.createElement("div"); m.className = "meta"; m.textContent = `Matched: ${opts.matched} (${Math.round(opts.confidence * 100)}% match)`; row.append(m); }
    if (opts.suggestions?.length) {
      const c = document.createElement("div"); c.className = "chips";
      opts.suggestions.forEach(s => { const x = document.createElement("button"); x.type = "button"; x.className = "chip"; x.textContent = s; x.onclick = () => ask(s); c.append(x); });
      row.append(c);
    }
    chat.append(row); scroll(); return row;
  }
  function typing() {
    const r = document.createElement("div"); r.className = "row bot typing";
    r.innerHTML = '<div class="bubble"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>';
    chat.append(r); scroll(); return r;
  }
  function welcome() {
    add("bot", `Hi! I'm the ${info.name} assistant. Ask me a question or pick one below.`, {suggestions: info.suggestions});
  }

  async function ask(text) {
    text = text.trim();
    if (busy || !text) return;
    busy = true; send.disabled = true; msg.value = "";
    add("user", text);
    const t = typing();
    try {
      const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 15000);
      const res = await fetch("/api/chat", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({message: text}), signal: ctl.signal});
      clearTimeout(timer);
      let d = {}; try { d = await res.json(); } catch {}
      t.remove();
      if (!res.ok) add("bot", d.error || `Server error (${res.status}). Please try again.`, {error: true});
      else add("bot", d.reply, d);
    } catch (e) {
      t.remove();
      add("bot", e.name === "AbortError" ? "The server took too long to respond. Please try again." : "Cannot reach the server. Check that it is running and your connection is working.", {error: true});
    } finally { busy = false; send.disabled = false; msg.focus(); }
  }

  form.addEventListener("submit", e => { e.preventDefault(); ask(msg.value); });
  document.getElementById("reset").onclick = () => { chat.replaceChildren(); welcome(); msg.focus(); };

  (async () => {
    try { const r = await fetch("/api/info"); if (r.ok) info = await r.json(); } catch {}
    document.getElementById("title").textContent = info.name; document.title = info.name;
    welcome();
  })();
})();
