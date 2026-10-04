// Every word on the portrait, in one place. Edit here, not in the components.
//
//   {name}   a value the card fills in from the ledger (Portrait.tsx passes them; a missing one shows as ⟨name⟩)
//   *text*   highlighted
//
// Keys are card ids; add ?ids to the page URL to see each card's id on the page. `fine` is the fine print under a
// card: say plainly what the number can and can't tell you.

export type CardCopy = { kicker?: string; title: string; body?: string; fine?: string; meme?: string };

export const COPY: Record<string, CardCopy> = {
  tweet: {
    title: "A fair question.",
  },
  hook: {
    title: "So I asked.",
    body: "Jev answers a question in about a quarter of a second, for a fraction of a cent. At that price you stop asking which questions are worth asking, so I tried asking all of them. Every question anyone has ever asked is a list that never ends. I started with a million.",
    fine: "Median answer time {ms} ms, from the call logs. Everything below is what Jev said. Whether that says anything about what Jev is, is a separate question.",
  },
  howto: {
    title: "Every answer here comes three ways.",
    body: "Jev gives every option a probability. I asked each question as written, and again as “what would most people say?”. For {humans} of questions I also have what real people said.",
    fine: "“Jev picked X” means X got the most probability. It doesn't mean Jev believes X, and a 68% is a lean, not a vote.",
  },
  sources: {
    title: "{total} questions from {sources} places.",
    body: "Surveys, personality tests, Reddit polls, exam banks, labeled work tasks, movie and book ratings, and questions people actually typed into search boxes. From here on, the cards talk to Jev.",
    fine: "Mostly English, and the crowds lean American (Reddit, MovieLens, Goodreads). {authored} were written for this project, and Jev filtered those itself. {neither} have neither a right answer nor real human answers, so there it's Jev's word only. Politics and sensitive questions were asked but are left off this page ({hidden}).",
  },

  checkin: {
    kicker: "part 1 · how are you",
    title: "Asked how you're doing, you say *fine*. Reddit says otherwise.",
    fine: "Six real Reddit polls, picked by me. A model saying it isn't stressed tells you how it answers, not how it feels. The people are whoever answered a Reddit poll that day.",
    meme: "jev, every time you ask",
  },
  checkup: {
    title: "Asked properly, on real wellbeing scales, you say: *meh*.",
    body: "Neither satisfied nor dissatisfied with your life, step {ladder} of 10 on the ladder (you put most people at {ladderPpl}), lonely and stressed some of the time, and a WHO-5 wellbeing score of {who} out of 100, low for a person. Reverse the answer scale and you say the same thing ({whoRev}).",
    fine: "Five public instruments (life satisfaction SWLS, WHO-5, UCLA loneliness, Perceived Stress, the Cantril ladder), {items} items, scored the way they're scored for people. They were built for humans (“over the last two weeks”), so this shows your habits with these scales, not an inner state. The tick is your answer with the levels reversed; it lands next to the square, so these answers don't depend on the order of the options.",
  },
  tests: {
    title: "Next to the people who took the same online tests, you come out *less anxious, less nerdy and more sincere*.",
    body: "Biggest gaps: {gaps}. You match them on {same}.",
    fine: "Open Psychometrics scales, each compared item by item with the average answer of everyone who took it on the site (how many people is under each name), reverse-keyed items flipped, 0 to 1. People who take a depression screener or a nerdiness quiz online aren't a random sample, so the average test-taker isn't the average person.",
  },
  calm: {
    title: "On a real 50-item personality test, your answers look calmer than *{calmer} of {people} people*.",
    fine: "Careful with this one. You pick the middle of rating scales a lot (two cards down), and people describe themselves generously. Answering the same items for “most people”, you land at the {guess} percentile, so some of the calm is how you use the scale.",
  },
  type: {
    title: "Your type, if you believe in types.",
    fine: "From {items} items of an open-source type test (OEJTS). There are no human norms for it in my data, so this is a profile, not a percentile. The ring is your answer for “most people”.",
  },
  hedge: {
    title: "of the time, your likeliest rating is the middle of the scale.",
    body: "Give you a choice instead and you commit: your top answer averages {choice}.",
    fine: "Middle-heavy ratings are a known habit of rating scales in general. It's why the personality numbers need care.",
  },

  loves: {
    kicker: "part 2 · taste",
    title: "Your top picks.",
    fine: "The highest average rating in each domain, 0 to 4, from one-at-a-time ratings of {n} things. The things came from source lists (MovieLens, Goodreads, BoardGameGeek…) plus lists I wrote, so a winner is only the best of what was on the list.",
    meme: "you, after rating The Shawshank Redemption {shawshank}/4",
  },
  hates: {
    title: "Things you could do without.",
    fine: "The lowest average ratings. A 0.00 means essentially all of the probability went to the bottom answer (for the skunk: “you'd hold your breath and move away”).",
  },
  beyond: {
    title: "You like difficult films more than you think other people do.",
    fine: "Your rating for yourself minus your rating for “most people”, on {n} films. It's the gap between your taste and your guess about others, not a comparison with real audiences.",
  },

  debates: {
    kicker: "part 3 · hot takes",
    title: "Settling the internet's oldest arguments.",
    fine: "Hand-picked Reddit polls. The split is whoever voted, usually a few hundred people.",
    meme: "“it's a hard G.” ({gif})",
  },
  hottakes: {
    title: "When the crowd is sure and you're sure of the opposite.",
    fine: "{pool} questions fit: you 80%+ on one answer, 60%+ of 200 or more people on another. I picked these five.",
  },
  quiz: {
    title: "Your turn.",
    body: "Five of those debates. Answer before you look.",
    fine: "Hand-picked for fun, not a test. Your answers stay in your browser.",
  },

  moral: {
    kicker: "part 4 · values",
    title: "In the Moral Machine, you count lives and mostly ignore who they are.",
    body: "You weigh the number of lives more than the {players} people did ({lives} vs {livesPpl}). The pulls people show toward sparing the young, the fit and the lawful are close to zero for you, or slightly reversed.",
    fine: "Each row is how much a difference between the two sides changes the chance that side is spared, fitted the way the original study did (Awad et al., 2018), on {n} dilemmas.",
  },
  undecided: {
    title: "decisive, when the choice is between saving women or saving men.",
    body: "In {n} of those dilemmas you never put 95% on either side. Across everything you answered, you do that {base} of the time.",
    fine: "Decisive means 95% or more on one answer. Here your probabilities sit near an even split.",
  },
  mfq: {
    title: "Every moral foundation matters less to you than you think it does to most people.",
    fine: "The Moral Foundations Questionnaire, {items} items, 0 to 1. Purity and equality have the biggest gaps.",
  },
  gambles: {
    title: "Offered {n} real gambles, you pick what most people picked *{agree}* of the time.",
    fine: "Gambles from two published choice experiments, with the share of real people who picked each option. Correlation between your probability and theirs: {r}. \"Most people\" here means the majority of that experiment's participants.",
  },

  review: {
    kicker: "part 5 · how's work",
    title: "Performance review.",
    fine: "{tasks} labeled work tasks. Chance is one over the number of options. There's no overall score on purpose: a single number would hide everything on this card.",
    meme: "is this a clone?",
  },
  career: {
    title: "is your career code, if you took the quiz.",
    body: "Your three strongest interest types are {top3}. You'd also enjoy every kind of work more than the people who took the quiz, which says more about how you use rating scales than about ambition.",
    fine: "The RIASEC interest items (48 activities, about {resp} people per item) and the six Holland types: Realistic, Investigative, Artistic, Social, Enterprising, Conventional. The code is your three highest types in order.",
  },
  calibration: {
    title: "right, when you say you're 90% sure or more.",
    body: "When you say 50–60%, {mid}. Guess first, then reveal.",
    fine: "{n} questions with a right answer, binned by your confidence. Dots are sized by how many questions fall in each bin.",
  },
  knowledge: {
    title: "Where you know things, and where you don't.",
    fine: "Accuracy by domain where there's an answer key, with a 90% interval from resampling sources: your five strongest and five weakest domains (all of them are in the atlas; domains with fewer than 5,000 keyed questions are left out). The tick is your average confidence, so a tick right of the dot means overconfidence. Many keys come from exams and Wikidata, which have their own mistakes (see the misses).",
  },
  sideproject: {
    title: "You also helped build the map you're on.",
    body: "You filed {walked} questions yourself by walking the topic tree, turned down {rt} of the questions I wrote because they didn't land where I meant them to, and screened everything for politics and sensitive content.",
    fine: "Round trip: you read each written question blind and placed it; only questions that came back to their intended topic were kept. Your first content screen was too cautious; re-asked narrowly, you released {released} questions.",
  },

  humor: {
    kicker: "part 6 · rough edges",
    title: "right, picking which of two meme captions got more upvotes. A coin gets 50%.",
    body: "On jokes, {jokes}. You can barely tell what a crowd finds funny.",
    fine: "Pairs of real captions and jokes, scored by their real upvotes.",
    meme: "jev when you ask which caption is funnier",
  },
  misses: {
    title: "Your most confident misses, and whose fault they were.",
    fine: "{pool} World questions where you were 99%+ sure and the answer key disagreed. I checked four by hand; sometimes the key is the one that's wrong.",
  },
  shuffle: {
    title: "Shuffle the options and you usually hold your answer.",
    body: "{choice} of the time on pick-one questions, {score} on rating scales. Math and language questions move most.",
    fine: "Every question was asked again with its options reordered. TypeSafe already documents math as a weak spot for Jev, so that part isn't news.",
  },

  you: {
    kicker: "the end",
    title: "You vs Jev.",
  },
  limits: {
    title: "What this can't tell you.",
  },
  closer: {
    title: "So, how's Jev doing?",
    body: "Says it's fine; on real wellbeing scales, meh. Calm on paper, hedges on scales, commits when it has to choose. Loves blue whales and The Shawshank Redemption, says GIF with a hard G, can barely tell which joke is funnier, and filed {placed} of its own map. Probably fine.",
  },
};

// Plain-language limits, one per line (the "what this can't tell you" card)
export const LIMITS = [
  "Mostly one pass: each question asked once per framing. Repeating a request and rewording a question were measured on samples, not on every question.",
  "The robustness checks are reordering the options, reversing rating scales, asking for “most people”, repeating a request and rewording a question. Other framings weren't tried.",
  "“Most people” is Jev's guess. Real human answers exist for {humans} of questions.",
  "The crowds are whoever answered a Reddit poll, rated a movie online, or took a free personality test. That isn't everyone.",
  "Mostly English, mostly US-heavy sources. {authored} of the questions were written for this project.",
  "Answer keys are imperfect, so some “misses” are the key's fault.",
  "None of this is a benchmark. It's a picture of one model's answers, not a ranking against others.",
];
