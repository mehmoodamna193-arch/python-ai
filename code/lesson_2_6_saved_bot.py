"""Lesson 2.6 - Task 2.6: Saved Bot for Sweet Crumbs bakery.

Loads business facts from faq.json, remembers yesterday's chat in
chat_history.json, and turns every crash into a friendly message plus a
line in errors.log. Run it from the folder that holds faq.json.
"""

import json
from datetime import datetime

import httpx
import ollama
from langchain.chat_models import init_chat_model

FAQ_FILE = "faq.json"
HISTORY_FILE = "chat_history.json"
LOG_FILE = "errors.log"
TRANSCRIPT_FILE = "transcript.txt"
MODEL = "llama3.2"


def log_error(message: str) -> None:
    """Append one timestamped error line to the log file."""
    # Why: "a" (append) keeps old errors, so the owner can see every problem
    # over time. "w" would erase the log each time something went wrong.
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}\n")


def save_history(messages: list) -> None:
    """Save the chat (without the system message) to the history file."""
    # Why: ensure_ascii=False keeps Urdu readable in the file, and we only
    # save plain dictionaries because response objects cannot become JSON.
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages[1:], f, indent=2, ensure_ascii=False)


def export_transcript(messages: list) -> int:
    """Write the chat to transcript.txt, one line per message. Return the line count."""
    count = 0
    with open(TRANSCRIPT_FILE, "w", encoding="utf-8") as f:
        for message in messages[1:]:  # skip the system message
            f.write(f"{message['role']}: {message['content']}\n")
            count += 1
    return count


# Why: facts live in a file, so the owner can change prices without
# editing code or calling the developer.
try:
    with open(FAQ_FILE, encoding="utf-8") as f:
        facts = json.load(f)
except FileNotFoundError:
    raise SystemExit(f"Missing {FAQ_FILE}. Create it first (Lesson 2.6, Section 5).")
except json.JSONDecodeError as e:
    raise SystemExit(f"{FAQ_FILE} is damaged on line {e.lineno}: {e.msg}. Please fix it.")

llm = init_chat_model(MODEL, model_provider="ollama")

system = {
    "role": "system",
    "content": f"You are the assistant of {facts['name']} in {facts['city']}. "
    f"Facts: {json.dumps(facts, ensure_ascii=False)}. Only use these facts. Answer in 2 short lines.",
}

# Why: the system message is rebuilt from fresh facts on every start and never
# saved, so a price changed in faq.json applies even to an old conversation.
messages = [system]
try:
    with open(HISTORY_FILE, encoding="utf-8") as f:
        old = json.load(f)
    if not isinstance(old, list):
        raise json.JSONDecodeError("History must be a list", "", 0)
    messages = [system] + old
    print(f"Loaded {len(old)} old messages.")
except FileNotFoundError:
    pass  # first run: no history yet, nothing to do
except json.JSONDecodeError:
    print("History file was damaged. Starting a fresh chat.")

print(f"{facts['name']} Bot: Ask me anything. Commands: /reset, /export, bye")

while True:
    text = input("You: ").strip()

    if text.lower() == "bye":
        print("Bot: Goodbye! Your chat is saved.")
        break
    if text == "":
        continue  # empty Enter: just ask again
    if text.lower() == "/export":
        lines = export_transcript(messages)
        print(f"Bot: Saved {lines} lines to {TRANSCRIPT_FILE}.")
        continue
    if text.lower() == "/reset":
        messages = [system]
        save_history(messages)
        print("Bot: Memory cleared.")
        continue

    messages.append({"role": "user", "content": text})
    try:
        # Only the last 6 messages are sent, so long chats stay fast and cheap
        response = llm.invoke([system] + messages[1:][-6:])
    except httpx.ConnectError:
        print("Bot: I am offline right now. Please open the Ollama app and try again.")
        messages.pop()  # remove the question that got no answer
        log_error("ConnectError: Ollama not running")
        continue
    except ollama.ResponseError as e:
        print("Bot: Sorry, something went wrong on my side.")
        messages.pop()
        log_error(f"ResponseError: {e.error}")
        continue

    answer = response.text
    messages.append({"role": "assistant", "content": answer})
    print(f"Bot: {answer}")

    # Why: saving after every turn means nothing is lost if the laptop shuts down
    save_history(messages)