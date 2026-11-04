"""Lesson 2.5 - Task 2.5: AI Skills Toolkit for Sweet Crumbs bakery.

One menu, many reusable AI skills: summarize, translate and reply to reviews.
All skills are built on a single engine, ask_ai(), so every staff member
gets the same consistent prompts instead of writing their own.
"""

from langchain.chat_models import init_chat_model

BUSINESS = "Sweet Crumbs"

# Why: models are created once at the top. Building a model object is slow,
# so doing it inside ask_ai() would repeat that work on every single call.
# Low temperature = precise and repeatable; high temperature = varied and creative.
precise = init_chat_model("llama3.2", model_provider="ollama", temperature=0.2)
creative = init_chat_model("llama3.2", model_provider="ollama", temperature=0.8)


def estimate_tokens(text: str) -> int:
    """Estimate tokens: about 4 characters of English text per token."""
    return round(len(text) / 4)


def ask_ai(
    prompt: str,
    system: str = "You are a helpful assistant. Answer in 2 short lines.",
    creative_mode: bool = False,
) -> str:
    """Send one prompt to the AI and return its answer as text."""
    # Why: facts (summaries, translations) need the precise model, while
    # customer-facing replies sound better with some creative variety.
    if creative_mode:
        llm = creative
    else:
        llm = precise
    response = llm.invoke([
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ])
    return response.text


def summarize(text: str, max_words: int = 30) -> str:
    """Summarize text in at most max_words words."""
    return ask_ai(f"Summarize in at most {max_words} words:\n{text}")


def translate(text: str, language: str = "Urdu") -> str:
    """Translate text into another language (Urdu by default)."""
    return ask_ai(f"Translate into {language}. Reply with the translation only:\n{text}")


def reply_to_review(review: str, business: str) -> str:
    """Write a short, polite reply from the business to a customer review."""
    return ask_ai(
        f"Write a 2-line polite reply from {business} to this review:\n{review}",
        creative_mode=True,
    )


# Quick tests for the function that does not need the AI.
# Why: tests run every time the file starts, so if someone changes
# estimate_tokens later and breaks it, we find out immediately.
assert estimate_tokens("Hello AI") == 2
assert estimate_tokens("Explain Python to a beginner") == 7
assert estimate_tokens("") == 0

# Why: a dictionary maps each skill name to a count, so one structure
# tracks every skill and we can print the report with a single for loop.
usage = {"summarize": 0, "translate": 0, "reply": 0, "batch": 0}

# Sample reviews for /batch (stretch goal)
SAMPLE_REVIEWS = [
    "Cake was great but delivery was late.",
    "Best cupcakes in Lahore, my kids loved them!",
    "The bread was stale when it arrived.",
]

print(f"{BUSINESS} AI Toolkit. Commands: /summarize, /translate, /reply, /batch, bye")

while True:
    command = input("Command: ").strip().lower()

    if command == "bye":
        break
    elif command == "/summarize":
        text = input("Text to summarize: ")
        print(f"AI: {summarize(text)}")
        usage["summarize"] += 1
    elif command == "/translate":
        text = input("Text to translate: ")
        language = input("Language (Enter for Urdu): ").strip()
        # Why: an empty answer means "use the default", so we leave the
        # argument out and let the function's default value (Urdu) apply.
        if language == "":
            print(f"AI: {translate(text)}")
        else:
            print(f"AI: {translate(text, language)}")
        usage["translate"] += 1
    elif command == "/reply":
        review = input("Customer review: ")
        print(f"AI: {reply_to_review(review, BUSINESS)}")
        print(f"    (review was about {estimate_tokens(review)} tokens)")
        usage["reply"] += 1
    elif command == "/batch":
        # Why: one skill, many inputs. A for loop with enumerate numbers
        # each result (starting at 1) without a manual counter variable.
        for number, review in enumerate(SAMPLE_REVIEWS, start=1):
            print(f"{number}. Review: {review}")
            print(f"   AI: {reply_to_review(review, BUSINESS)}")
        usage["batch"] += 1
    else:
        print("Unknown command. Try /summarize, /translate, /reply, /batch or bye.")

print("Skills used today:")
for skill, count in usage.items():
    print(f"  {skill}: {count}")