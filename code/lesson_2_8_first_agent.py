"""Lesson 2.8 - Task 2.8: Your First Agent for Sweet Crumbs bakery.

The model is the waiter: it decides which tool is needed and writes the order
slip. Our Python code is the kitchen: it runs the tool and sends the result
back. Four tools: read prices, read the FAQ file, check an order, and place an
order (only after the owner types "yes").
"""

import json

import httpx
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import ToolMessage
from pydantic import ValidationError

MAX_STEPS = 5  # safety: stop if the agent keeps calling tools without answering
FAQ_FILE = "faq.json"
ORDERS_FILE = "agent_orders.json"

PRICES = {"chocolate cake": 1500, "cupcake": 250, "brownie": 300}
ORDERS = {"A101": "baking", "A102": "out for delivery", "A103": "delivered"}


@tool(parse_docstring=True)
def get_price(item: str) -> str:
    """Get the price of one bakery item.

    Args:
        item: The item name, for example "cupcake".
    """
    name = item.lower().strip()
    if name in PRICES:
        return f"{name} costs {PRICES[name]} PKR"
    return f"{item} is not on the menu. Menu: {', '.join(PRICES)}"


@tool(parse_docstring=True)
def order_status(order_id: str) -> str:
    """Check the delivery status of an existing order.

    Args:
        order_id: The order number, for example "A101".
    """
    key = order_id.upper().strip()
    if key not in ORDERS:
        return f"Order {order_id} not found"
    return f"Order {key} is {ORDERS[key]}"


@tool(parse_docstring=True)
def place_order(item: str, quantity: int, customer: str) -> str:
    """Place a new order. Only use this when the customer clearly asks to order.

    Args:
        item: The item name, for example "cupcake".
        quantity: How many, for example 2.
        customer: The customer's name.
    """
    name = item.lower().strip()
    if name not in PRICES:
        return f"{item} is not on the menu"
    if quantity <= 0:
        return "Quantity must be at least 1"
    total = PRICES[name] * quantity  # Why: Python does the maths, never the AI

    # Why: a human approves every action that costs money, so a confused or
    # tricked model can never place an order on its own.
    answer = input(f"  [approve] {quantity} x {name} for {customer} = {total} PKR. Place it? (yes/no) ")
    if answer.strip().lower() != "yes":
        return "The owner did not approve this order"

    order_id = f"A{101 + len(ORDERS)}"
    ORDERS[order_id] = "received"
    with open(ORDERS_FILE, "a", encoding="utf-8") as f:
        record = {"id": order_id, "item": name, "quantity": quantity, "customer": customer, "total": total}
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return f"Order {order_id} placed: {quantity} x {name}, total {total} PKR"


@tool(parse_docstring=True)
def read_faq(topic: str) -> str:
    """Look up shop facts such as opening hours, delivery or payment from the owner's FAQ file.

    Args:
        topic: The fact to look up, for example "hours" or "delivery".
    """
    try:
        with open(FAQ_FILE, encoding="utf-8") as f:
            facts = json.load(f)
    except FileNotFoundError:
        return f"The FAQ file {FAQ_FILE} was not found"
    except json.JSONDecodeError:
        return f"The FAQ file {FAQ_FILE} is damaged"

    key = topic.lower().strip()
    if key in facts:
        return f"{key}: {json.dumps(facts[key], ensure_ascii=False)}"
    return f"No exact match. All facts: {json.dumps(facts, ensure_ascii=False)}"


# Why: a dictionary lets us find the right function from the name the model
# sends, and an unknown name is simply a missing key, not a crash.
TOOLS = {t.name: t for t in [get_price, order_status, place_order, read_faq]}

llm = init_chat_model("llama3.2", model_provider="ollama")
llm_with_tools = llm.bind_tools(list(TOOLS.values()))  # show the model which tools exist

SYSTEM = {
    "role": "system",
    "content": "You are the Sweet Crumbs bakery agent. Use the tools for prices, shop facts, "
    "order status and new orders. Never guess prices or statuses. Answer in 2 short lines.",
}

# Memory: one list for the whole chat, created before the loop so the agent
# remembers earlier questions (a name, an order id) until you type bye.
messages = [SYSTEM]

print("Sweet Crumbs Agent: ask about prices, orders, or place an order. Type 'bye' to exit.")

while True:
    text = input("You: ").strip()
    if text.lower() == "bye":
        break
    if text == "":
        continue

    turn_start = len(messages)  # remember where this turn began, to undo it on failure
    messages.append({"role": "user", "content": text})

    try:
        for step in range(MAX_STEPS):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:  # no tool needed: this is the final answer
                print(f"Agent: {response.text}")
                break

            for call in response.tool_calls:
                name = call["name"]
                if name not in TOOLS:
                    result = f"Error: there is no tool called '{name}'. Tools: {', '.join(TOOLS)}"
                else:
                    try:
                        result = TOOLS[name].invoke(call["args"])
                    except ValidationError as e:
                        result = f"Error: wrong arguments for {name} ({e.error_count()} problem(s)). Check the Args."
                print(f"  [tool] {name}({call['args']}) -> {result}")

                # Why: tool_call_id tells the model which request this result answers
                messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
        else:
            # The for loop used all MAX_STEPS without a break: the agent never answered
            print("Agent: Sorry, I could not finish that. A human will help you.")
    except httpx.ConnectError:
        print("Agent: I am offline right now. Please open the Ollama app and try again.")
        del messages[turn_start:]  # drop the unfinished turn so the chat stays valid