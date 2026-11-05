"""Task 2.2: Personal Tutor with Memory.

A chat loop with a local Ollama model (through LangChain) that remembers the
conversation using a list of messages. Commands: /reset clears the memory,
/count shows how many messages are stored, bye exits. Memory is trimmed to
the system message plus the last 8 messages, and the tokens sent are shown
after every answer. Stretch: a second list keeps the user's questions, and
on bye the tutor prints how many were asked, plus the first and last one.
"""

from langchain.chat_models import init_chat_model

# Why a limit: every call re-sends the whole history, so without a cap the
# chat gets slower and more expensive with each turn.


# Why create the model once, before the loop: every turn reuses it, and the
# slow model loading happens only on the first call.
llm = init_chat_model("llama3.2", model_provider="ollama", temperature=0.2)

# Why the lists live outside the loop: if they were re-created inside it,
# the tutor would forget everything on every turn.
messages = [
    {"role": "system", "content": "You are a friendly personal tutor. Explain simply and answer in 2 short lines."},
]
questions = []  # stretch: only the user's questions

print("Tutor: Ask me anything. Commands: /reset, /count, bye")

while True:
    text = input("You: ").strip()

    if text.lower() == "bye":
        print("Tutor: Goodbye!")
        if questions:
            print(f"Tutor: You asked {len(questions)} question(s).")
            print(f"       First: {questions[0]}")
            print(f"       Last:  {questions[-1]}")
        break
    elif text.lower() == "/reset":
        messages = [messages[0]]  # forget the chat, keep the rules
        print("Tutor: Memory cleared.")
    elif text.lower() == "/count":
        print(f"Tutor: {len(messages)} messages in memory.")
    elif text == "":
        print("Tutor: Please type a question.")
    else:
        questions.append(text)
        messages.append({"role": "user", "content": text})

        # Why [messages[0]] + ...: trimming must never cut off the system
        # message, or the tutor loses its role and answer length.
        messages = [messages[0]] + messages[1:][-8:]

        response = llm.invoke(messages)
        answer = response.text

        # Why save the reply too: the AI only knows what we send it, so
        # without its own answers in the list it forgets what it said.
        messages.append({"role": "assistant", "content": answer})

        print(f"Tutor: {answer}")
        print(f"       (tokens sent: {response.usage_metadata['input_tokens']})")