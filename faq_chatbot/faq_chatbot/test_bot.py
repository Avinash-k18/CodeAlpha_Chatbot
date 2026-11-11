"""Quick accuracy check: python test_bot.py"""
from bot import FAQBot
bot = FAQBot("faqs.json")
cases = [
 ("where is my parcel", "track"), ("i want to cancel what i ordered", "cancel"), ("can i send the product back", "return"),
 ("how many days for money to come back", "refund"), ("do you deliver to usa", "intl"), ("can i pay with google pay upi", "payment"),
 ("i forgot my passwrod", "password"), ("my coupon code is not working", "promo"), ("received a broken phone", "damaged"),
 ("how to talk to a human", "contact"), ("is there free delivery", "shipcost"), ("traking my ordr", "track"),
]
ok = 0
for q, exp in cases:
    r = bot.reply(q); got = next((f["id"] for f in bot.faqs if f["question"] == r.get("matched")), r["type"])
    ok += got == exp; print(("PASS" if got == exp else "FAIL"), f"{q!r} -> {got} (expected {exp})")
print(f"\n{ok}/{len(cases)} correct")
for q in ["hello", "thanks", "???", "the is a", "asdfgh qwerty", "what is the capital of france", "hi how do i track my order"]:
    r = bot.reply(q); print(f"{q!r}: {r['type']}")
