# -*- coding: utf-8 -*-
"""Practice content: IELTS Speaking question banks, cue cards, German lessons.

All questions and cue cards are original, written in the style of the public
IELTS Speaking test format (Part 1 interview, Part 2 long turn, Part 3
discussion). Edit freely - the skill picks them up on the next deploy.
"""

# ---------------------------------------------------------------------------
# IELTS Speaking Part 1 - familiar topics, 4 questions each
# ---------------------------------------------------------------------------
PART1_TOPICS = [
    {"topic": "your hometown", "questions": [
        "Where is your hometown?",
        "What do you like most about living there?",
        "Has your hometown changed much since you were a child?",
        "Would you recommend it to a tourist? Why?",
    ]},
    {"topic": "work or studies", "questions": [
        "Do you work, or are you a student?",
        "Why did you choose that job or subject?",
        "What is the most difficult part of it?",
        "What would you like to do in the future?",
    ]},
    {"topic": "free time", "questions": [
        "What do you usually do in your free time?",
        "Do you prefer spending free time alone or with other people?",
        "Did you have the same hobbies when you were younger?",
        "Is there a new hobby you would like to try?",
    ]},
    {"topic": "food", "questions": [
        "What kind of food do you like to eat?",
        "Do you cook at home?",
        "Is there any food you disliked as a child but enjoy now?",
        "Do you think people eat more healthily now than in the past?",
    ]},
    {"topic": "music", "questions": [
        "What kind of music do you listen to?",
        "When do you usually listen to music?",
        "Have you ever learned to play a musical instrument?",
        "Do you prefer live music or recorded music?",
    ]},
    {"topic": "the weather", "questions": [
        "What is the weather usually like where you live?",
        "What is your favourite kind of weather?",
        "Does the weather ever change your plans?",
        "Would you like to live somewhere with a very different climate?",
    ]},
    {"topic": "reading", "questions": [
        "Do you enjoy reading?",
        "What did you like to read when you were a child?",
        "Do you prefer printed books or reading on a screen?",
        "Is there a book you would like to read again?",
    ]},
    {"topic": "mobile phones", "questions": [
        "How often do you use your mobile phone?",
        "What do you mainly use it for?",
        "Could you live without your phone for a week?",
        "Do you think children should have mobile phones?",
    ]},
    {"topic": "travel", "questions": [
        "Do you like travelling?",
        "Where was the last place you visited?",
        "Do you prefer travelling alone or with others?",
        "Where would you like to go in the future?",
    ]},
    {"topic": "friends", "questions": [
        "Do you have many close friends?",
        "How do you usually spend time with your friends?",
        "Is it easy to make new friends as an adult?",
        "What makes someone a good friend?",
    ]},
    {"topic": "sleep", "questions": [
        "How many hours do you usually sleep?",
        "Do you ever take a nap during the day?",
        "What do you do when you can't fall asleep?",
        "Do you think people today get enough sleep?",
    ]},
    {"topic": "shopping", "questions": [
        "Do you enjoy shopping?",
        "Do you prefer shopping online or in shops?",
        "What was the last thing you bought?",
        "Has the way people shop changed in your country?",
    ]},
]

# ---------------------------------------------------------------------------
# IELTS Speaking Part 2 cue cards, each with linked Part 3 questions
# ---------------------------------------------------------------------------
CUE_CARDS = [
    {
        "title": "Describe a skill you learned that took a long time.",
        "points": ["what the skill is", "when you started learning it",
                   "how you learned it"],
        "explain": "why it took you so long to learn",
        "part3": [
            "Which skills do you think young people should learn at school?",
            "Is it better to learn a skill from a teacher or from the internet?",
            "Why do some adults stop learning new things?",
        ],
    },
    {
        "title": "Describe a place in your city where you like to relax.",
        "points": ["where it is", "how often you go there",
                   "what you do there"],
        "explain": "why you find it relaxing",
        "part3": [
            "Why do people in cities find it hard to relax?",
            "Should governments spend more money on parks and public spaces?",
            "How might cities change in the next twenty years?",
        ],
    },
    {
        "title": "Describe a person who has inspired you.",
        "points": ["who this person is", "how you know them",
                   "what they have done"],
        "explain": "why they inspire you",
        "part3": [
            "What kind of people do young people admire today?",
            "Do famous people have a responsibility to be good role models?",
            "Are role models more important for children or for adults?",
        ],
    },
    {
        "title": "Describe a piece of technology you find useful.",
        "points": ["what it is", "when you got it", "how you use it"],
        "explain": "why it is useful to you",
        "part3": [
            "How has technology changed the way people communicate?",
            "Do you think older people find new technology difficult? Why?",
            "Could technology ever replace teachers?",
        ],
    },
    {
        "title": "Describe a memorable journey you have made.",
        "points": ["where you went", "who you went with",
                   "how you travelled"],
        "explain": "why the journey was memorable",
        "part3": [
            "Why do people enjoy travelling to other countries?",
            "What are the negative effects of tourism on a place?",
            "Will people travel more or less in the future?",
        ],
    },
    {
        "title": "Describe a time you helped someone.",
        "points": ["who you helped", "what the problem was",
                   "how you helped them"],
        "explain": "how you felt afterwards",
        "part3": [
            "Do people help their neighbours less than they used to?",
            "Should children be taught to do volunteer work?",
            "Who should help poor people: the government or individuals?",
        ],
    },
    {
        "title": "Describe a book or film that made you think.",
        "points": ["what it was", "when you read or watched it",
                   "what it was about"],
        "explain": "why it made you think",
        "part3": [
            "Do films influence the way young people behave?",
            "Why do some people prefer books to films?",
            "Should governments control what films people can watch?",
        ],
    },
    {
        "title": "Describe a goal you hope to achieve in the next few years.",
        "points": ["what the goal is", "when you decided on it",
                   "what you are doing to achieve it"],
        "explain": "why this goal matters to you",
        "part3": [
            "Is it important for young people to set long-term goals?",
            "Do people today have more choices about their future than in the past?",
            "What stops people from achieving their goals?",
        ],
    },
    {
        "title": "Describe a time you had to make an important decision.",
        "points": ["what the decision was", "when you made it",
                   "what choices you had"],
        "explain": "how you felt about the result",
        "part3": [
            "Do young people make decisions differently from older people?",
            "Should parents make important decisions for their children?",
            "Why do some people find it hard to make decisions?",
        ],
    },
    {
        "title": "Describe an outdoor activity you enjoy.",
        "points": ["what the activity is", "where you do it",
                   "who you do it with"],
        "explain": "why you enjoy it",
        "part3": [
            "Why do fewer children play outside today?",
            "Should schools spend more time on sport?",
            "How does the environment affect the activities people choose?",
        ],
    },
    {
        "title": "Describe a festival or celebration that is important in your country.",
        "points": ["what it is", "when it takes place",
                   "what people do during it"],
        "explain": "why it is important",
        "part3": [
            "Are traditional festivals losing their meaning?",
            "Has globalisation changed how people celebrate?",
            "Should festivals be used to attract tourists?",
        ],
    },
    {
        "title": "Describe a time you learned something from a mistake.",
        "points": ["what the mistake was", "when it happened",
                   "what happened as a result"],
        "explain": "what you learned from it",
        "part3": [
            "Is it acceptable for leaders to admit their mistakes?",
            "Do schools punish mistakes too much?",
            "How can workplaces encourage people to learn from failure?",
        ],
    },
]

# ---------------------------------------------------------------------------
# German A1 foundation - 20 lessons, 5 phrases each.
# Each phrase: (german, english meaning, list of accepted keyword groups).
# An answer is correct if ALL words of ANY keyword group appear in it.
# ---------------------------------------------------------------------------
def _p(de, en, *groups):
    return {"de": de, "en": en,
            "accept": [g.split() if isinstance(g, str) else list(g) for g in groups]}


GERMAN_LESSONS = [
    # ---- Week 1: sounds, greetings, introducing yourself
    {"title": "Greetings", "tip": (
        "The u with two dots, as in Tschüss, sounds like ee said with "
        "rounded lips."),
     "phrases": [
         _p("Hallo", "hello", "hello", "hi"),
         _p("Guten Morgen", "good morning", "morning"),
         _p("Guten Tag", "good day, or hello", "day", "hello", "afternoon"),
         _p("Guten Abend", "good evening", "evening"),
         _p("Tschüss", "bye", "bye", "goodbye", "see you"),
     ]},
    {"title": "How are you?", "tip": (
        "German sentences often drop little words in speech: Wie geht's is "
        "short for Wie geht es."),
     "phrases": [
         _p("Wie geht's?", "how are you?", "how are you", "how is it going",
            "how are things", "how"),
         _p("Mir geht's gut, danke.", "I'm fine, thanks.", "fine", "good",
            "well", "okay"),
         _p("Und dir?", "and you?", "and you", "you"),
         _p("Nicht so gut.", "not so good.", "not good", "not so good", "bad",
            "not great"),
         _p("Super!", "great!", "great", "super", "excellent", "awesome"),
     ]},
    {"title": "Names and where you're from", "tip": (
        "E I sounds like the English word eye, as in heißt. I E sounds like "
        "ee, as in Sie."),
     "phrases": [
         _p("Wie heißt du?", "what's your name?", "name", "called"),
         _p("Ich heiße Anna.", "my name is Anna.", "name", "called", "anna"),
         _p("Freut mich.", "nice to meet you.", "nice", "meet", "pleased",
            "pleasure"),
         _p("Woher kommst du?", "where are you from?", "where from",
            "where come"),
         _p("Ich komme aus Indien.", "I come from India.", "india"),
     ]},
    {"title": "About me", "tip": (
        "The German W sounds like an English V. Wohne sounds like vohne."),
     "phrases": [
         _p("Ich wohne in Bangalore.", "I live in Bangalore.", "live"),
         _p("Ich bin Student.", "I am a student.", "student"),
         _p("Ich arbeite als Ingenieur.", "I work as an engineer.",
            "engineer"),
         _p("Ich spreche Englisch.", "I speak English.", "speak"),
         _p("Ich lerne Deutsch.", "I am learning German.", "learn",
            "learning", "study", "studying"),
     ]},
    {"title": "Polite words", "tip": (
        "C H after e or i is a soft hiss, like a cat, as in nicht. "
        "It is never a hard k."),
     "phrases": [
         _p("Bitte", "please, or you're welcome", "please", "welcome"),
         _p("Danke schön", "thank you very much", "thank", "thanks"),
         _p("Entschuldigung", "excuse me, or sorry", "excuse", "sorry",
            "pardon"),
         _p("Ja, gern.", "yes, gladly.", "yes", "gladly", "sure",
            "with pleasure"),
         _p("Ich verstehe nicht.", "I don't understand.", "understand"),
     ]},
    # ---- Week 2: numbers, days, time
    {"title": "Numbers one to five", "tip": (
        "Drei has a rolled or throaty R. Don't worry if yours sounds "
        "English for now."),
     "phrases": [
         _p("eins", "one", "one", "1"),
         _p("zwei", "two", "two", "2"),
         _p("drei", "three", "three", "3"),
         _p("vier", "four", "four", "4"),
         _p("fünf", "five", "five", "5"),
     ]},
    {"title": "Numbers six to ten", "tip": (
        "S at the start of a word sounds like an English Z: sechs, sieben."),
     "phrases": [
         _p("sechs", "six", "six", "6"),
         _p("sieben", "seven", "seven", "7"),
         _p("acht", "eight", "eight", "8"),
         _p("neun", "nine", "nine", "9"),
         _p("zehn", "ten", "ten", "10"),
     ]},
    {"title": "Bigger numbers and age", "tip": (
        "German says the ones before the tens: einundzwanzig is one and "
        "twenty."),
     "phrases": [
         _p("zwanzig", "twenty", "twenty", "20"),
         _p("dreißig", "thirty", "thirty", "30"),
         _p("einundzwanzig", "twenty-one", "twenty one", "21"),
         _p("hundert", "one hundred", "hundred", "100"),
         _p("Wie alt bist du?", "how old are you?", "old", "age"),
     ]},
    {"title": "Days of the week", "tip": (
        "Every German noun starts with a capital letter, including days: "
        "Montag, Freitag."),
     "phrases": [
         _p("Montag", "Monday", "monday"),
         _p("Mittwoch", "Wednesday", "wednesday"),
         _p("Freitag", "Friday", "friday"),
         _p("das Wochenende", "the weekend", "weekend"),
         _p("heute", "today", "today"),
     ]},
    {"title": "Telling the time", "tip": (
        "Careful: halb vier means half past three, not half past four. "
        "It is half way to four."),
     "phrases": [
         _p("Wie spät ist es?", "what time is it?", "time"),
         _p("Es ist drei Uhr.", "it is three o'clock.", "three", "3"),
         _p("halb vier", "half past three", "half past three",
            "three thirty", "330", "3:30"),
         _p("morgen", "tomorrow", "tomorrow"),
         _p("am Abend", "in the evening", "evening"),
     ]},
    # ---- Week 3: cafe, food, shopping
    {"title": "At the cafe", "tip": (
        "Ich möchte means I would like. It is the polite way to order."),
     "phrases": [
         _p("Ich möchte einen Kaffee, bitte.", "I would like a coffee, please.",
            "coffee"),
         _p("Ein Wasser, bitte.", "a water, please.", "water"),
         _p("Die Speisekarte, bitte.", "the menu, please.", "menu"),
         _p("Ich habe Hunger.", "I am hungry.", "hungry", "hunger"),
         _p("Lecker!", "tasty!", "tasty", "delicious", "yummy"),
     ]},
    {"title": "Food words", "tip": (
        "Der, die and das all mean the. Learn each noun together with its "
        "word for the."),
     "phrases": [
         _p("das Brot", "the bread", "bread"),
         _p("der Käse", "the cheese", "cheese"),
         _p("das Gemüse", "the vegetables", "vegetable", "vegetables"),
         _p("das Hähnchen", "the chicken", "chicken"),
         _p("Ich bin Vegetarier.", "I am vegetarian.", "vegetarian"),
     ]},
    {"title": "Paying", "tip": (
        "Z sounds like ts in German: zahlen sounds like tsahlen."),
     "phrases": [
         _p("Die Rechnung, bitte.", "the bill, please.", "bill", "check"),
         _p("Wie viel kostet das?", "how much does that cost?", "how much",
            "cost", "price"),
         _p("Das ist zu teuer.", "that is too expensive.", "expensive"),
         _p("Kann ich mit Karte zahlen?", "can I pay by card?", "card"),
         _p("Zusammen oder getrennt?", "together or separately?",
            "together", "separate", "separately"),
     ]},
    {"title": "Shopping", "tip": (
        "Sie with a capital S is the polite you. Use it with shop staff "
        "and strangers."),
     "phrases": [
         _p("Ich suche eine Jacke.", "I'm looking for a jacket.", "jacket"),
         _p("Haben Sie das in Blau?", "do you have this in blue?", "blue"),
         _p("Ich nehme das.", "I'll take it.", "take"),
         _p("Das ist zu klein.", "that is too small.", "small"),
         _p("billig", "cheap", "cheap", "inexpensive"),
     ]},
    {"title": "Useful classroom phrases", "tip": (
        "Langsamer, bitte is the most useful sentence a beginner can know."),
     "phrases": [
         _p("Guten Appetit!", "enjoy your meal!", "enjoy", "meal",
            "appetite", "appetit"),
         _p("Prost!", "cheers!", "cheers"),
         _p("Noch einmal, bitte.", "once more, please.", "again", "once more",
            "one more time"),
         _p("Langsamer, bitte.", "slower, please.", "slower", "slow"),
         _p("Können Sie das wiederholen?", "can you repeat that?", "repeat"),
     ]},
    # ---- Week 4: directions, transport, review
    {"title": "Directions", "tip": (
        "Links is left and rechts is right. Geradeaus is straight ahead."),
     "phrases": [
         _p("Wo ist der Bahnhof?", "where is the train station?", "station"),
         _p("links", "left", "left"),
         _p("rechts", "right", "right"),
         _p("geradeaus", "straight ahead", "straight"),
         _p("Wo ist die Toilette?", "where is the toilet?", "toilet",
            "bathroom", "restroom", "washroom"),
     ]},
    {"title": "Transport", "tip": (
        "Fahren means to travel by vehicle. Gehen means to go on foot."),
     "phrases": [
         _p("der Bus", "the bus", "bus"),
         _p("der Zug", "the train", "train"),
         _p("die U-Bahn", "the underground, or metro", "underground",
            "metro", "subway", "tube"),
         _p("die Fahrkarte", "the ticket", "ticket"),
         _p("Wann fährt der Zug?", "when does the train leave?", "when"),
     ]},
    {"title": "Getting around", "tip": (
        "Nach means to, for cities and countries: nach Berlin, nach Indien."),
     "phrases": [
         _p("Ich fahre nach Berlin.", "I am travelling to Berlin.", "berlin"),
         _p("Wie weit ist das?", "how far is that?", "far"),
         _p("in der Nähe", "nearby", "near", "nearby", "close"),
         _p("Ich habe mich verlaufen.", "I am lost.", "lost"),
         _p("Können Sie mir helfen?", "can you help me?", "help"),
     ]},
    {"title": "Review: weeks one and two", "review": [0, 9], "tip": (
        "Say each phrase out loud before I give the meaning."),
     "phrases": []},
    {"title": "Review: weeks three and four", "review": [10, 17], "tip": (
        "You have learned about ninety phrases. Gut gemacht: well done."),
     "phrases": []},
]

# ---------------------------------------------------------------------------
# Listening drill data
# ---------------------------------------------------------------------------
SURNAMES = [
    "Thornton", "Whitaker", "Pemberton", "Ashworth", "Gallagher", "Henderson",
    "Prescott", "Lockwood", "Bramley", "Ellison", "Hartley", "Crossland",
    "Winslow", "Radcliffe", "Holloway", "Kingsley", "Marlowe", "Fenwick",
    "Barrington", "Caldwell",
]

FIRST_NAMES = ["Sarah", "James", "Emily", "Daniel", "Laura", "Michael",
               "Rachel", "Thomas", "Hannah", "Oliver"]
