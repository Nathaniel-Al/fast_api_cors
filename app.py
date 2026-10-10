import os
import re
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

POSITIVE = set("""
love loved loves loving like liked likes enjoy enjoyed enjoying great good best better amazing awesome
fantastic wonderful excellent perfect happy happier happiest glad joy joyful delighted delight delightful
pleased pleasant nice beautiful brilliant superb terrific fabulous incredible outstanding impressive
fun funny exciting excited thrilled thankful grateful thanks thank blessed proud cheerful celebrate
celebrating celebrated congratulations congrats win won winning success successful smile smiling smiled
laugh laughing laughed lovely adore adored cool yay hooray wow stunning gorgeous marvelous magnificent
satisfied satisfying enjoyable favorite recommend recommended breathtaking ecstatic overjoyed elated
upbeat optimistic hopeful relieved comfortable peaceful calm lucky fortunate bliss blissful sweet
charming helpful kind generous friendly supportive positive strong smooth easy rocks rocking
""".split())

NEGATIVE = set("""
hate hated hates hating dislike disliked terrible awful horrible bad worse worst sad sadder saddest
unhappy depressed depressing miserable upset angry angrier furious mad annoyed annoying irritated
frustrated frustrating disappointed disappointing disappointment disgusting disgusted gross nasty
cry cried crying tears lonely alone heartbroken heartbreaking grief grieving grieve mourn mourning
suffer suffering pain painful hurt hurts hurting hopeless worthless useless pathetic poor broken
fail failed failure failing lost lose losing loss die died dying death dead tragic tragedy sorry
regret regretted ugly boring bored tired exhausted worried worry anxious nervous scared afraid fear
terrified hopeless dreadful dismal gloomy glum sorrow sorrowful bitter rude cruel mean stupid dumb
waste wasted trash garbage junk crap sucks sucked awful rotten lousy mediocre unfortunately unfortunate
negative weak slow stuck ruined ruin devastated devastating miss missed missing
""".split())

NEGATORS = {"not", "no", "never", "none", "nobody", "nothing", "neither", "nor", "hardly", "barely",
            "without", "cannot", "cant", "dont", "doesnt", "didnt", "isnt", "wasnt", "arent",
            "werent", "wont", "wouldnt", "shouldnt", "couldnt", "hasnt", "havent", "hadnt", "aint"}
BOOSTERS = {"very", "really", "so", "extremely", "absolutely", "totally", "incredibly", "truly",
            "super", "deeply", "utterly", "completely"}

POS_EMOJI = set("😀😃😄😁😆😊🙂😍🥰😘😎🤩🎉❤💖💕👍🥳😂🤣☺😻✨🙌👏")
NEG_EMOJI = set("😢😭😞😔😟😠😡🤬😩😫😖😣☹🙁💔👎😿😤😰😨😱😓")

PHRASES_POS = ["can't wait", "cant wait", "looking forward", "thank you", "so proud", "made my day",
               "best day", "love it", "a blast", "top notch", "well done", "can't complain"]
PHRASES_NEG = ["fed up", "give up", "gave up", "let down", "broke my heart", "worst day", "no good",
               "waste of", "falling apart", "want to cry", "feel empty", "can't stop crying"]


def classify(sentence: str) -> str:
    text = sentence.lower().replace("’", "'")
    score = 0.0

    for p in PHRASES_POS:
        if p in text:
            score += 1.5
    for p in PHRASES_NEG:
        if p in text:
            score -= 1.5

    score += sum(1 for ch in sentence if ch in POS_EMOJI)
    score -= sum(1 for ch in sentence if ch in NEG_EMOJI)

    cleaned = text.replace("n't", "nt").replace("'", "")
    tokens = re.findall(r"[a-z]+", cleaned)
    for i, tok in enumerate(tokens):
        if tok in POSITIVE:
            val = 1.0
        elif tok in NEGATIVE:
            val = -1.0
        else:
            continue
        window = tokens[max(0, i - 3):i]
        if any(w in BOOSTERS for w in window[-1:]):
            val *= 1.5
        if any(w in NEGATORS for w in window):
            val *= -0.8
        score += val

    if score > 0:
        return "happy"
    if score < 0:
        return "sad"
    return "neutral"


class SentimentRequest(BaseModel):
    sentences: List[str]


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/sentiment")
async def sentiment(req: SentimentRequest):
    return {"results": [{"sentence": s, "sentiment": classify(s)} for s in req.sentences]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
