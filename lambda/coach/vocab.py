# -*- coding: utf-8 -*-
"""Vocabulary upgrade drill: Alexa says a plain IELTS-style sentence, the
learner says it again with a stronger word, and Alexa models a band-7
version. Producing the word before hearing it is retrieval practice; misses
come back through coach/srs.py. All sentences are original.

Checked offline: an answer counts if it contains any accepted upgrade."""

import re

# Intensifiers worth dropping once a strong word is in place
_LEFTOVER = ("very", "really")


def _v(num, topic, plain, accept, model):
    return {"id": "V%02d" % num, "topic": topic, "plain": plain,
            "accept": accept, "model": model}


ITEMS = [
    _v(1, "weather", "The weather was very good.",
       ["pleasant", "glorious", "superb", "lovely", "gorgeous", "delightful",
        "perfect", "ideal", "fantastic", "marvellous", "marvelous",
        "splendid"],
       "We had glorious weather the whole week, warm but never too humid."),
    _v(2, "weather", "It was very hot in summer.",
       ["scorching", "sweltering", "boiling", "baking", "blistering",
        "roasting", "stifling"],
       "Summers in my city are sweltering, so I stay indoors in the "
       "afternoons."),
    _v(3, "weather", "It rains a lot in the monsoon.",
       ["pours", "pouring", "torrential", "heavy rain", "downpour",
        "downpours", "incessant", "relentless", "buckets"],
       "During the monsoon it pours almost every evening, and the streets "
       "flood quickly."),
    _v(4, "hometown", "My hometown is very big.",
       ["huge", "vast", "enormous", "sprawling", "massive", "immense",
        "gigantic"],
       "My hometown is a sprawling city of more than ten million people."),
    _v(5, "hometown", "My hometown is very crowded.",
       ["packed", "congested", "overcrowded", "jam packed", "bustling",
        "teeming", "densely populated", "heaving"],
       "The old part of town is packed with shoppers, especially during "
       "festivals."),
    _v(6, "hometown", "There are a lot of old buildings.",
       ["historic", "heritage", "ancient", "centuries old", "colonial",
        "historical"],
       "The centre is full of colonial-era buildings that have been "
       "beautifully restored."),
    _v(7, "work", "My job is very interesting.",
       ["fascinating", "rewarding", "stimulating", "absorbing", "engaging",
        "fulfilling", "intriguing", "gripping"],
       "My job is genuinely rewarding because I solve a new problem every "
       "day."),
    _v(8, "work", "My work is very difficult.",
       ["challenging", "demanding", "tough", "gruelling", "grueling",
        "taxing", "exhausting", "complex", "tricky"],
       "The work is demanding, but the deadlines push me to learn quickly."),
    _v(9, "work", "I am very busy at work.",
       ["swamped", "snowed under", "flat out", "overloaded", "hectic",
        "rushed off my feet", "stretched"],
       "This month I'm completely swamped, so I rarely leave the office "
       "before eight."),
    _v(10, "studies", "I learned a lot at university.",
       ["gained", "acquired", "developed", "broadened", "deepened",
        "picked up", "mastered"],
       "University broadened my thinking far more than I expected."),
    _v(11, "free time", "I like to relax at the weekend.",
       ["unwind", "recharge", "chill out", "put my feet up", "take it easy",
        "wind down", "decompress"],
       "At the weekend I like to unwind with a long walk and a good book."),
    _v(12, "free time", "Reading is a good hobby.",
       ["rewarding", "enriching", "worthwhile", "absorbing", "relaxing",
        "therapeutic", "satisfying", "fulfilling"],
       "Reading is a truly enriching hobby because it takes me into other "
       "lives."),
    _v(13, "food", "The food was very tasty.",
       ["delicious", "mouth watering", "flavourful", "flavorful",
        "scrumptious", "exquisite", "delectable", "superb", "sumptuous"],
       "The biryani was absolutely mouth-watering, rich but not too spicy."),
    _v(14, "food", "The food was very spicy.",
       ["fiery", "eye watering", "burning", "scorching", "blistering",
        "punchy", "fierce"],
       "The curry was fiery enough to make my eyes water."),
    _v(15, "food", "I eat a lot of junk food.",
       ["far too much", "a great deal", "plenty of", "an awful lot",
        "excessive", "heaps of", "loads of"],
       "I probably eat far too much processed food because of my long "
       "hours."),
    _v(16, "music", "I really like music.",
       ["love", "adore", "passionate", "fond of", "keen on", "big fan",
        "crazy about", "into"],
       "I'm passionate about music, especially old Hindi film songs."),
    _v(17, "music", "The concert was very good.",
       ["incredible", "outstanding", "phenomenal", "unforgettable",
        "electrifying", "superb", "spectacular", "magnificent",
        "sensational"],
       "The concert was electrifying, and the whole crowd sang along."),
    _v(18, "reading", "The book was very boring.",
       ["tedious", "dull", "monotonous", "uninspiring", "slow moving",
        "dreary", "mind numbing"],
       "I found the novel quite tedious because nothing happened for a "
       "hundred pages."),
    _v(19, "mobile phones", "I use my phone a lot.",
       ["constantly", "all the time", "heavily", "round the clock",
        "non stop", "glued", "addicted"],
       "I'm practically glued to my phone, mostly for work messages."),
    _v(20, "mobile phones", "Phones are very important today.",
       ["essential", "indispensable", "vital", "crucial", "integral",
        "invaluable"],
       "Smartphones have become indispensable for banking, travel and even "
       "ordering food."),
    _v(21, "technology", "Technology changed our lives a lot.",
       ["dramatically", "enormously", "radically", "profoundly",
        "significantly", "fundamentally", "transformed"],
       "Technology has transformed daily life dramatically in just ten "
       "years."),
    _v(22, "travel", "The trip was very nice.",
       ["memorable", "delightful", "unforgettable", "wonderful", "enjoyable",
        "magical", "idyllic", "fantastic"],
       "Our trip to the hills was unforgettable, especially the sunrise "
       "trek."),
    _v(23, "travel", "The view was very beautiful.",
       ["breathtaking", "stunning", "spectacular", "magnificent",
        "picturesque", "awe inspiring", "striking", "gorgeous"],
       "The view from the top was absolutely breathtaking."),
    _v(24, "travel", "The hotel was very bad.",
       ["dreadful", "awful", "terrible", "appalling", "shabby", "dire",
        "atrocious", "disappointing", "run down"],
       "The hotel was rather run-down, and the room smelled of damp."),
    _v(25, "friends", "My friend is very kind.",
       ["generous", "thoughtful", "considerate", "caring", "compassionate",
        "warm hearted", "big hearted", "selfless"],
       "My closest friend is incredibly thoughtful; she never forgets a "
       "birthday."),
    _v(26, "friends", "We are very close friends.",
       ["inseparable", "lifelong", "tight knit", "thick as thieves",
        "like family", "best friends", "like siblings"],
       "We've been inseparable since school and still talk every day."),
    _v(27, "sleep", "I was very tired.",
       ["exhausted", "worn out", "drained", "shattered", "fatigued",
        "knackered", "wiped out"],
       "After the night shift I was completely drained."),
    _v(28, "shopping", "It was very expensive.",
       ["overpriced", "pricey", "costly", "exorbitant", "extortionate",
        "steep", "a fortune", "sky high"],
       "The jacket was hugely overpriced, so I waited for the sale."),
    _v(29, "shopping", "It was very cheap.",
       ["affordable", "inexpensive", "bargain", "reasonable", "economical",
        "good value", "a steal"],
       "I found a pair of shoes that were a real bargain."),
    _v(30, "shopping", "The shop had a lot of choice.",
       ["wide range", "huge selection", "vast range", "extensive",
        "variety", "wide selection", "diverse"],
       "The market offers an extensive range of spices you can't find "
       "elsewhere."),
    _v(31, "health", "Exercise is good for you.",
       ["beneficial", "healthy", "advantageous", "vital", "essential",
        "valuable", "worthwhile", "wholesome"],
       "Regular exercise is hugely beneficial for both body and mind."),
    _v(32, "health", "I felt very happy after running.",
       ["elated", "euphoric", "energised", "energized", "uplifted",
        "thrilled", "content", "overjoyed", "buzzing", "refreshed"],
       "After a morning run I feel energised for the whole day."),
    _v(33, "environment", "Pollution is a big problem.",
       ["serious", "major", "pressing", "critical", "grave", "severe",
        "significant", "urgent"],
       "Air pollution is a pressing issue in most Indian cities."),
    _v(34, "environment", "The river is very dirty.",
       ["polluted", "filthy", "contaminated", "toxic", "murky", "grimy",
        "foul"],
       "The river has become badly polluted by industrial waste."),
    _v(35, "transport", "The traffic is very bad.",
       ["horrendous", "appalling", "chaotic", "gridlocked", "terrible",
        "nightmarish", "atrocious", "dreadful"],
       "Rush-hour traffic is horrendous; a short trip can take an hour."),
    _v(36, "transport", "The bus was very slow.",
       ["sluggish", "painfully slow", "crawled", "crawling", "snails pace",
        "leisurely", "dawdling"],
       "The bus crawled through the city at a snail's pace."),
    _v(37, "home", "My flat is very small.",
       ["tiny", "cramped", "compact", "poky", "pokey", "minuscule", "cosy",
        "cozy"],
       "My flat is fairly compact, but it's cosy and close to work."),
    _v(38, "home", "My neighbourhood is very quiet.",
       ["peaceful", "tranquil", "serene", "calm", "sleepy", "secluded"],
       "My neighbourhood is wonderfully tranquil, apart from the morning "
       "birds."),
    _v(39, "people", "My teacher was very good.",
       ["inspiring", "outstanding", "exceptional", "brilliant", "dedicated",
        "gifted", "talented", "remarkable"],
       "My maths teacher was truly inspiring; she made hard ideas feel "
       "simple."),
    _v(40, "festivals", "Diwali is a very happy festival.",
       ["joyful", "joyous", "cheerful", "festive", "jubilant", "uplifting",
        "vibrant", "lively"],
       "Diwali is a joyous festival, full of lights, sweets and family "
       "visits."),
    _v(41, "opinions", "I think it is a bad idea.",
       ["unwise", "misguided", "ill advised", "short sighted",
        "counterproductive", "flawed", "foolish", "reckless"],
       "Personally, I think banning phones in schools is rather "
       "short-sighted."),
    _v(42, "change", "My city has changed a lot.",
       ["dramatically", "considerably", "beyond recognition",
        "significantly", "enormously", "radically", "substantially",
        "transformed"],
       "My city has changed beyond recognition in the last decade."),
    _v(43, "films", "The film was very sad.",
       ["heartbreaking", "moving", "poignant", "tragic", "devastating",
        "heart wrenching", "tear jerking", "touching"],
       "The ending was so poignant that half the audience was in tears."),
    _v(44, "work", "My boss is very strict.",
       ["demanding", "exacting", "authoritarian", "uncompromising", "stern",
        "rigid", "tough", "firm"],
       "My manager is quite demanding, but she's always fair."),
]
BY_ID = {it["id"]: it for it in ITEMS}


def _norm(text):
    """Lowercase, hyphens to spaces, no apostrophes: 'snail's' -> 'snails'."""
    text = (text or "").lower().replace("-", " ").replace("'", "")
    return " ".join(re.findall(r"[a-z]+", text))


def check(item, text):
    """Return (upgraded, word_used, nudge)."""
    said = _norm(text)
    for word in item["accept"]:
        if re.search(r"\b%s\b" % re.escape(_norm(word)), said):
            left = [w for w in _LEFTOVER if re.search(r"\b%s\b" % w, said)]
            nudge = ("" if not left else
                     "You kept %s, though. One strong word works better on "
                     "its own." % left[0])
            return True, word, nudge
    return False, None, ""
