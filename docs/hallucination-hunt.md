# Hallucination Hunt: Order Extractor (Lesson 2.7, Section 7)

**How to run it:** in `lesson_2_7_extractor.py` set `RUN_HUNT = True`, run
`uv run lesson_2_7_extractor.py`, and fill in the two right-hand columns for each
message below. Then set `RUN_HUNT` back to `False`.

Score 1 point for every mistake your checks caught, and 1 point for every
mistake that slipped through and needs a new check.

| Message | Trap | What the AI returned | Caught by a check? |
|---|---|---|---|
| `do cupcakes bhej dein` | "do" means 2 in Urdu. Did the AI get quantity 2? | _fill in_ | _fill in_ |
| `1 pizza and 2 brownies, Bilal, Model Town` | Pizza is not on the menu. Was it flagged? | _fill in_ | _fill in_ |
| `same as last time please` | No items at all. Did the AI invent an order? | _fill in_ | _fill in_ |
| `Bilal: 2 cakes, Model Town` | "cakes" could mean chocolate cake. Did it guess? | _fill in_ | _fill in_ |
| `I want five brownies` | Number in words. Is quantity 5? | _fill in_ | _fill in_ |

## Mistakes my checks caught

_fill in after running_

## Mistakes that slipped through

_fill in after running_

## New check I would add

_fill in after running (share the best one with the class)_

## Score

Caught: _ / Slipped through: _