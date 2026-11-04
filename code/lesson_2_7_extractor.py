"""Lesson 2.7 - Task 2.7: Order Extractor for Sweet Crumbs bakery.

Turns messy WhatsApp orders (English and Roman Urdu) into checked JSON orders.
The AI only reads the message and fills a form; Python checks the data,
calculates the totals with our own prices, and saves the result.
"""

import json

from langchain.chat_models import init_chat_model

PRICES = {"chocolate cake": 1500, "cupcake": 250, "brownie": 300}

# Set to True to also run the Hallucination Hunt messages (Lesson 2.7, Section 7)
RUN_HUNT = False

MESSAGES = [
    "Hi, 1 chocolate cake please. Sara, DHA phase 5",                          # normal order
    "Salam! 2 cupcakes aur 1 chocolate cake chahiye. Ali, house 12 Gulberg",  # 2+ items
    "1 pizza and 2 brownies, Bilal, Model Town",                               # item not on the menu
    "hi do you deliver to Johar Town?",                                        # not an order
    "Bhai 3 brownies bhej dein, Hina, Johar Town block B",                     # Roman Urdu
]

HUNT_MESSAGES = [
    "do cupcakes bhej dein",
    "same as last time please",
    "Bilal: 2 cakes, Model Town",
    "I want five brownies",
]

ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "customer": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["name", "quantity"],
            },
        },
        "address": {"type": "string"},
    },
    "required": ["customer", "items", "address"],
}

# Why: format=ORDER_SCHEMA forces the exact shape we need, and temperature 0
# makes the same message give the same result every time (no random variety).
extractor = init_chat_model("llama3.2", model_provider="ollama", temperature=0, format=ORDER_SCHEMA)

SYSTEM = (
    "Extract the bakery order from the WhatsApp message. "
    f"Item names must be one of: {', '.join(PRICES)}. "
    "If the customer name or address is not in the message, use an empty string. "
    "If it is not an order, return an empty items list. Never invent details."
)

messages_in = MESSAGES + HUNT_MESSAGES if RUN_HUNT else MESSAGES

saved = []        # orders that had items, with totals and problems
total_value = 0   # money across all saved orders
check_count = 0   # how many CHECK warnings we raised

for message in messages_in:
    response = extractor.invoke([
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": message},
    ])

    # Check 1: is the reply valid JSON at all?
    try:
        order = json.loads(response.text)
    except json.JSONDecodeError:
        print(f"\nMessage: {message}")
        print("  CHECK: could not read the AI reply")
        check_count += 1
        continue

    print(f"\nMessage: {message}")

    # Check 2: read keys with .get() so a missing key gives a default, not a crash
    items = order.get("items", [])
    if len(items) == 0:
        print("  Not an order: needs a human reply.")
        continue

    # Why: Python does the maths with OUR prices. The AI can misread or
    # invent numbers, so it never calculates a total.
    total = 0
    problems = []
    lines = []
    for item in items:
        name = str(item.get("name", "")).lower()
        quantity = item.get("quantity", 0)

        # Check 3: is the item real (on our menu) and the quantity a whole number?
        if name not in PRICES:
            problems.append(f"'{name}' is not on the menu")
            continue
        if not isinstance(quantity, int) or quantity <= 0:
            problems.append(f"quantity for '{name}' is not a positive whole number")
            continue

        line_total = PRICES[name] * quantity
        total += line_total
        lines.append({"name": name, "quantity": quantity, "line_total": line_total})
        print(f"  {quantity} x {name} = {line_total} PKR")

    # Check 4: a customer name that is not in the message was probably invented
    customer = order.get("customer", "")
    if customer != "" and customer.lower() not in message.lower():
        problems.append(f"customer '{customer}' is not in the message (invented?)")

    address = order.get("address", "")
    order["lines"] = lines
    order["total"] = total
    order["problems"] = problems
    saved.append(order)
    total_value += total
    check_count += len(problems)

    print(f"  Customer: {customer or '(missing)'}, Address: {address or '(missing)'}")
    print(f"  Total: {total} PKR")
    for problem in problems:
        print(f"  CHECK: {problem}")

with open("orders.json", "w", encoding="utf-8") as f:
    json.dump(saved, f, indent=2, ensure_ascii=False)

# Stretch: one CSV line per item, ready to open in Excel or Google Sheets
with open("orders.csv", "w", encoding="utf-8") as f:
    f.write("customer,item,quantity,line_total\n")
    for order in saved:
        for line in order["lines"]:
            f.write(f"{order.get('customer', '')},{line['name']},{line['quantity']},{line['line_total']}\n")

print("\n" + "=" * 50)
print(f"Orders found: {len(saved)} | Total value: {total_value:,} PKR | Checks: {check_count}")
print(f"Saved {len(saved)} orders to orders.json and orders.csv")