import sys; sys.path.insert(0,'/Users/junzhang/Projects/askjev/scratchpad/phase6_mind1'); from lib import *; node("thought_experiments")

# ---------- Experience machine variants ----------
C("An experience machine can give you any life you want, but you would know it was simulated the whole time. Which life would you ask it for?",
  [("adventurer", "exploring, danger, discovery"), ("great_artist", None), ("famous_leader", None), ("quiet_family_life", None), ("scientist_who_solves_everything", None), ("romance", "a perfect love story"), ("would_not_use_it", None), ("other", None)], "values")
S("Your closest friend tells you they have decided to plug into an experience machine permanently. How would you react?",
  ["I would do whatever I could to stop them, including physically unplugging them", "I would beg them to change their mind and feel betrayed if they went ahead", "I would argue against it once, then accept their choice with sadness", "I would respect the choice without trying to change their mind", "I would be glad for them and might consider joining them"], "social")
N("If you could plug into an experience machine for just a single week of perfect happiness and then return to your real life, would you do it?", "values")
C("If you plugged into an experience machine, what would you miss most about real life, even if the simulated version felt identical?",
  [("real_relationships", "knowing the people are actually there"), ("real_achievements", "knowing you actually did the things"), ("real_risk", "the chance of genuine failure"), ("truth", "not being deceived"), ("affecting_the_world", None), ("nothing", "if it feels the same, nothing is lost"), ("other", None)], "values")
N("An experience machine offers you a simulated life that is merely a bit happier than your real one, with the same people in it as simulations. Would you switch?", "values")
C("Imagine you learned that you have been inside an experience machine all along, and you can now choose to wake up into a harsher real world. What would you do?",
  [("wake_up", None), ("stay_in", None), ("stay_until_old_age", "then wake up"), ("wake_briefly_then_decide", None), ("not_sure", None)], "values")
S("An experience machine can give you the feeling of having written a great novel, without you writing anything. How much would that feeling be worth to you compared with actually writing a good novel?",
  ["The feeling alone would be worthless to me; only the real novel counts", "The feeling would be a pleasant but minor consolation", "The feeling would be worth about half as much as the real thing", "The feeling would be nearly as good as the real thing", "The feeling would be just as good, since the feeling is what matters"], "values")
N("Suppose everyone you love has already plugged into a shared experience machine where they live together happily. Would you plug in to join them?", "social")
C("A shared experience machine lets you and your real friends live together in a perfect simulated world where your actions affect each other. How does it compare with the solo version?",
  [("much_better", "real people make it worth entering"), ("somewhat_better", None), ("no_different", "still not real life"), ("worse", None), ("not_sure", None)], "evaluative")
N("Would it be wrong to secretly plug someone into an experience machine while they slept if you knew they would be happier there forever?", "values")
S("A doctor offers a patient in constant, untreatable pain the option of spending the rest of their life in an experience machine. How do you view that option?",
  ["It would be wrong to offer it; they should face reality whatever the cost", "It should be offered only as a last resort after long counselling", "It is a reasonable option they should be free to take", "It is the kind and obvious choice for them", "It should be the default unless they refuse"], "values")
C("What is the main thing that makes a life lived in an experience machine less valuable, if anything?",
  [("not_real", "the events never actually happened"), ("no_real_others", "no genuine relationships"), ("no_agency", "you do not truly act"), ("no_growth", "you do not become a better person"), ("self_deception", None), ("nothing_is_lost", None), ("other", None)], "evaluative")
N("If a machine could make you feel exactly as if your deceased pet were still alive and with you, would you want to use it?", "values")
N("Would you plug into an experience machine for your final months of life if you were terminally ill and bedridden?", "values")
C("An experience machine offers a life where you are loved by everyone but you remember nothing of your real life. Which part of that bothers you most?",
  [("losing_memories", None), ("fake_love", None), ("abandoning_real_people", None), ("nothing_bothers_me", None), ("all_equally", None)], "evaluative")

# ---------- Teleporter / duplication / fission ----------
S("A teleporter works by scanning you, sending the information, and building you from new matter while the original body is gently dissolved. How would you use it for your daily commute if it were perfectly safe?",
  ["I would never use it; it would kill me every time", "I would use it only in a genuine emergency", "I would use it for long trips but feel uneasy each time", "I would use it regularly after seeing others come through fine", "I would use it every day without a second thought"], "values")
C("A teleporter malfunctions: it builds your copy at the destination but fails to destroy the original, so two of you now exist. Who should keep your home, job, and relationships?",
  [("the_original", None), ("the_copy", "the one who arrived as planned"), ("share_everything", None), ("both_start_over", None), ("let_them_decide", "the two of you negotiate"), ("other", None)], "values")
N("If a teleporter's malfunction left two of you and the original was scheduled to be dissolved a minute later, should the original have the right to refuse?", "values")
C("Your partner comes back from a trip via a destroy-and-rebuild teleporter. How would you feel about the person who arrives?",
  [("exactly_the_same", "it is simply them"), ("mostly_the_same", "with a lingering unease"), ("a_perfect_replacement", "not quite them"), ("a_stranger", "my partner died"), ("not_sure", None)], "social")
S("Before stepping into a teleporter that destroys the original, a friend asks you whether they will survive the trip. What would you honestly tell them?",
  ["You will die and someone else will take your place", "You will probably die, even if your copy never knows it", "Nobody really knows whether you survive", "You will probably survive; the copy is you in every way that matters", "You will certainly survive; it is just a strange way of travelling"], "evaluative")
N("If a teleporter moved your body slowly, atom by atom, rather than rebuilding it from new matter, would you feel safer using it?", "evaluative")
C("A person splits in two, like an amoeba: two people walk away, each with the full memories and character of the original. What happened to the original person?",
  [("died", "two new people replaced them"), ("survived_twice", "they are now both people"), ("survived_as_one", "one of them is really the original"), ("question_has_no_answer", None), ("survival_does_not_matter", "what matters is continued psychology"), ("other", None)], "evaluative")
N("If you knew you were going to split into two identical people tomorrow, would you feel as if you were about to die?", "personality")
S("If you split into two people with identical memories, how should the debts and promises you made before the split be handled?",
  ["Neither of them owes anything; the person who promised is gone", "Each owes a share, like two heirs of an estate", "One of them should be picked to carry the full obligation", "Both are fully bound, as if each made the promise", "Both are bound and should also answer to each other for it"], "values")
C("If an exact duplicate of you were made, which of these would you most want to do with them?",
  [("become_friends", None), ("split_up_life_duties", "one works, one travels"), ("compete", None), ("go_separate_ways", None), ("avoid_them", None), ("study_how_we_differ", None), ("other", None)], "social")
S("A perfect copy of you is made and lives on the other side of the world. As the years pass, how would you feel about them?",
  ["I would think of them as a complete stranger", "I would think of them like a distant relative", "I would think of them like a sibling or twin", "I would think of them as partly me, living another life", "I would think of them as simply me, in a second place"], "personality")
N("If your perfect duplicate committed a crime a day after being created, should you share any of the blame?", "values")
N("Would it be wrong for someone to create a perfect duplicate of you without your consent?", "values")
C("If a scan could store a backup of you that would be activated only if you died suddenly, would you want one made?",
  [("yes_definitely", None), ("yes_for_my_family", "for the sake of those I leave behind"), ("only_if_it_is_really_me", None), ("no_it_would_not_be_me", None), ("no_it_feels_wrong", None), ("not_sure", None)], "values")
S("A backup copy of you is activated after you die in an accident. How should your family treat the backup?",
  ["As an impostor who should not be part of the family", "As a new person who happens to share memories with the one they lost", "As a close relative of the one they lost", "As the same person returned after a gap", "As the same person, with no difference at all"], "social")
N("If a teleporter created your copy at the destination and the original was kept asleep forever instead of destroyed, would that be better than destroying it?", "values")
C("Two people step into a machine that swaps their memories and personalities, then walk out. Where would you say each person now is?",
  [("where_the_memories_went", "in the other body"), ("where_the_body_is", None), ("both_died", None), ("no_fact_of_the_matter", None), ("not_sure", None)], "evaluative")

# ---------- Body swap / memory ----------
S("Before a body-swap machine is used on you and a stranger, one of the two resulting people will be given a large reward and the other will be punished. Which body would you want to be rewarded?",
  ["I would want the body I have now rewarded, no question", "I would lean toward my current body being rewarded", "I would genuinely not know which to choose", "I would lean toward the other body, since my mind will be there", "I would want the other body rewarded, since that is where I will be"], "evaluative")
N("If your memories were implanted into a stranger's brain and theirs were erased, would that stranger now be you?", "evaluative")
C("A machine can move your memories to a new, healthier body, leaving your old body alive but with no memories. Which one would be you?",
  [("new_body_with_memories", None), ("old_body", None), ("neither", None), ("both_in_a_way", None), ("not_sure", None)], "evaluative")
S("You are told you will be tortured tomorrow, but first all your memories will be wiped and replaced with a stranger's. How much would that news frighten you?",
  ["Not at all, because the person tortured will not be me", "A little, as if hearing a stranger will suffer", "A fair amount, since it is still my body", "A great deal, because I am the one who will feel it", "As much as if nothing about my memory would change"], "personality")
N("If your personality slowly changed over years until it was the opposite of what it is now, would you still be the same person?", "evaluative")
C("If you could keep only one thing through a body swap, which would matter most for staying you?",
  [("memories", None), ("personality", None), ("values", None), ("relationships", "the people who know you"), ("body", None), ("skills", None), ("other", None)], "values")
N("Would you agree to swap bodies with someone younger if your memories and personality came with you intact?", "values")
C("After a body swap, your best friend is now in a body you have never seen. How would you want to confirm it is really them?",
  [("shared_secrets", "ask things only they would know"), ("how_they_act", None), ("how_they_treat_me", None), ("trust_the_machine", None), ("could_never_be_sure", None), ("other", None)], "social")
S("A person loses every memory in an accident but keeps their personality. How should the promises they made before the accident be treated?",
  ["They have no obligations at all; they are someone new", "They should honor only promises that protect other people", "They should honor most promises, with some leeway", "They should honor every promise as if they remembered making it", "They should honor every promise and make up for any lost time"], "values")

# ---------- Uploading / gradual replacement ----------
C("A company offers to upload your mind to a computer, but the scan destroys your brain. When would you accept?",
  [("never", None), ("only_if_dying", None), ("in_old_age", None), ("once_many_others_had", None), ("as_soon_as_possible", None), ("not_sure", None)], "values")
S("An uploaded mind says it remembers being you and feels just like you. How much of your estate should it inherit?",
  ["Nothing; it is a machine imitating me", "A small keepsake, like a distant relative", "A share alongside my other heirs", "Most of it, as my closest successor", "All of it, since it is me"], "values")
N("If your mind could be uploaded while your biological brain kept running, would you want the upload made?", "values")
C("If you were uploaded, what would you most worry about?",
  [("not_really_being_me", None), ("being_copied_without_consent", None), ("being_switched_off", None), ("losing_the_body", "missing touch, food, and physical life"), ("being_changed_by_others", None), ("living_forever", None), ("nothing", None)], "evaluative")
N("If an uploaded mind of a dead person asked to be deleted, should its wish be granted?", "values")
S("Your brain cells are replaced one at a time by artificial ones that work identically, and you stay awake the whole time. What would you expect to notice?",
  ["I would feel myself fading away as the replacement went on", "I might notice subtle changes in how things feel", "I would notice nothing but still suspect something was lost", "I would notice nothing and believe nothing was lost", "I would notice nothing and be confident I simply continued"], "evaluative")
N("If artificial replacements for your neurons were available and perfectly safe, would you replace them to avoid brain disease?", "values")
C("Your brain is gradually replaced with artificial parts and the removed biological cells are reassembled into a working brain. Which one is you?",
  [("the_artificial_brain", None), ("the_reassembled_brain", None), ("both", None), ("neither", None), ("not_sure", None)], "evaluative")
N("Would you still consider a friend the same person if you learned they had quietly replaced their whole brain with identical artificial parts?", "social")

# ---------- Ship of Theseus and artifacts ----------
C("A grandfather's axe has had its handle replaced by the father and its head replaced by the son. Is it still the grandfather's axe?",
  [("yes", None), ("no", None), ("yes_in_spirit_only", "the story makes it his, not the parts"), ("it_depends_on_why", None), ("not_sure", None)], "evaluative")
C("Over the years every original member of a band leaves and is replaced, but the name and songs stay the same. Is it still the same band?",
  [("yes", None), ("no", None), ("only_while_one_founder_remains", None), ("only_if_the_sound_stays", None), ("not_sure", None)], "evaluative")
N("If a band has replaced every original member, is it misleading for them to keep playing under the old name?", "values")
S("A historic house burns down and is rebuilt exactly as it was, using new materials. How would you describe the rebuilt house?",
  ["It is a replica with no link to the original", "It is a tribute, not the real house", "It is partly the same house because of its design and place", "It is essentially the same house, repaired", "It is simply the same house"], "evaluative")
N("If a museum painting were restored so heavily that none of the original paint remained, would it still be the artist's painting?", "evaluative")
C("A guitar once owned by a famous musician has had its neck, body, and strings replaced. What makes it worth more than an identical guitar, if anything?",
  [("remaining_original_parts", None), ("its_history", None), ("paperwork", "the documented chain of ownership"), ("nothing", None), ("other", None)], "evaluative")
S("Your childhood teddy bear has been repaired so many times that almost none of the original fabric or stuffing is left. How do you feel about it?",
  ["It is a different toy now and means little to me", "It is a reminder of the old bear, not the bear itself", "It is still partly my bear", "It is my bear, just well repaired", "It is my bear, and the repairs are part of its story"], "personality")
N("If a sports team moves to a new city, changes its name, and replaces every player, is it still the same team?", "evaluative")
C("A company replaces all its staff, moves offices, and changes what it sells, but keeps its name. What would make it the same company?",
  [("the_name", None), ("the_legal_entity", None), ("the_culture", None), ("the_customers", None), ("nothing_it_is_a_new_company", None), ("other", None)], "evaluative")
S("A river's water is entirely different from one moment to the next. When someone says they swam in the same river as last year, how accurate are they?",
  ["Completely wrong; it is a different river", "Mostly wrong, speaking loosely at best", "Partly right, since the banks and name stay", "Mostly right in every way that matters", "Completely right; a river is its course, not its water"], "evaluative")
N("If a ship's planks were replaced one at a time while it stayed in use, would the ship keep its original owner's legal title the whole time?", "evaluative")
C("If someone collected all the discarded original planks of a restored ship and built a second ship from them, which one should sit in the museum as the historic ship?",
  [("restored_ship", "the one continuously in use"), ("rebuilt_ship", "the one made from original planks"), ("both", None), ("neither", None), ("not_sure", None)], "evaluative")
N("If your car had every part replaced over the years, would you say you still drive the same car you bought?", "evaluative")
S("Nearly all the cells in your body are replaced over time. How much does that fact change how you think about being the same person you were as a child?",
  ["It makes me think the child and I are simply different people", "It makes me doubt I am the same person in a deep sense", "It makes me see sameness as a matter of degree", "It barely matters, since my memories and story continue", "It does not matter at all; I am obviously the same person"], "evaluative")
N("If a forest is logged and replanted with the same species in the same place, is it still the same forest?", "evaluative")
C("A famous violin is taken apart and its pieces are shipped to different countries. Where does the violin exist now?",
  [("nowhere_until_reassembled", None), ("in_every_piece", None), ("in_the_largest_piece", None), ("still_exists_scattered", None), ("not_sure", None)], "evaluative")

# ---------- Brain in a vat / demon / dream ----------
S("If you learned for certain that you are a brain in a vat, how would you spend the rest of your simulated life?",
  ["I would stop caring about anything and give up", "I would withdraw and treat everything as meaningless", "I would keep living much the same but with less passion", "I would live exactly as before", "I would live more boldly, since only experiences count"], "personality")
N("If you were a brain in a vat, would your statement 'I have hands' still be true in some sense?", "evaluative")
C("A brain in a vat is told the truth and offered a real, fragile body in a harsh world. What should it choose?",
  [("real_body", None), ("stay_in_the_vat", None), ("depends_on_the_vat_world", None), ("depends_on_the_real_world", None), ("not_sure", None)], "values")
C("An all-powerful trickster might be feeding you false experiences of the whole world. What is the most sensible response?",
  [("ignore_it", "it makes no practical difference"), ("take_it_seriously", "reduce confidence in everything"), ("trust_what_works", None), ("look_for_glitches", None), ("it_cannot_be_true", None), ("other", None)], "evaluative")
N("Can you ever be sure that you are not dreaming right now?", "evaluative")
S("You wake up and realise the last day was a vivid dream. How much would that experience make you doubt the day you are having now?",
  ["Not at all; waking life is obviously different", "Only for a passing second", "Enough that I would check for signs I am awake", "Enough that I would stay unsettled for a while", "Enough that I would start to doubt waking life in general"], "personality")
C("What would be the best test to tell whether you are dreaming?",
  [("read_text_twice", "see if words change"), ("check_clocks_or_screens", None), ("pinch_yourself", None), ("recall_how_you_got_here", None), ("ask_someone", None), ("no_test_works", None), ("other", None)], "evaluative")
N("If a lifelong dream were as detailed, consistent, and shared as waking life, would it be just as real?", "evaluative")
S("A neuroscientist offers to prove to you that you are a brain in a vat. What evidence would you need before believing it?",
  ["No evidence could convince me, since the proof itself could be fake", "I would need to be pulled out and see the vat myself", "I would need an impossible event demonstrated on demand", "I would need a strong argument plus some strange evidence", "Their word as an expert would mostly convince me"], "evaluative")
N("If your whole life were a dream, would the kindness you showed people in it still count as kindness?", "values")

# ---------- Simulation argument ----------
C("If our world is a simulation, who do you think is most likely running it?",
  [("future_humans", None), ("aliens", None), ("a_scientific_experiment", None), ("an_entertainment_game", None), ("an_automated_system", "no one is watching"), ("impossible_to_guess", None), ("other", None)], "evaluative")
S("You find convincing evidence that the world is a simulation. How would your day-to-day behaviour change?",
  ["I would stop following rules, since nothing is real", "I would take more risks and care less about consequences", "I would change a few small habits", "I would carry on exactly as before", "I would try hard to contact or understand the simulators"], "personality")
N("If we live in a simulation, should people try to find a way to send a message to whoever runs it?", "values")
C("Suppose we learn that our world is a simulation that will be switched off someday. What matters most then?",
  [("enjoy_life", None), ("be_kind_to_others", None), ("try_to_escape", None), ("learn_the_truth", None), ("keep_living_normally", None), ("other", None)], "values")
N("If we could build a simulated world full of beings who feel real pain, would it be wrong to build it?", "values")
S("If humans one day run realistic simulations of the past with conscious people inside, how should those people be treated?",
  ["Like characters in a game with no rights at all", "With a few limits on extreme cruelty", "With protection from needless suffering", "With the same moral weight as real people", "As real people, with a right to know the truth"], "values")
C("If you were running a simulation with conscious beings, which rule would you set first?",
  [("no_suffering", None), ("free_will", "let them choose freely"), ("hidden_truth", "never let them find out"), ("reveal_the_truth", None), ("let_it_run_untouched", None), ("other", None)], "values")
N("Would finding out we live in a simulation make scientific discoveries any less valuable?", "evaluative")
S("A popular argument says that if advanced civilizations run many simulations, we are more likely simulated than not. How persuasive do you find it?",
  ["I dismiss it as pure speculation", "I find it clever but not convincing", "I think it raises a real but unanswerable possibility", "I think it makes being simulated a serious live option", "I think it makes being simulated the most likely truth"], "evaluative")
N("If the simulators occasionally edited our memories to fix errors, would that make memory useless as a guide to the past?", "evaluative")
C("What kind of sign would most convince you that you live in a simulation?",
  [("physical_glitch", "something repeating or freezing"), ("hidden_message_in_physics", None), ("repeated_coincidences", None), ("a_message_from_outside", None), ("nothing_could", None), ("other", None)], "evaluative")

# ---------- Chinese room ----------
S("A person inside a room follows a huge rulebook to answer questions written in Chinese, without knowing any Chinese. People outside believe they are talking to a fluent speaker. How would you describe what happens?",
  ["Nothing in the room understands anything; it is symbol shuffling", "There is a faint shadow of understanding in the process", "The room as a whole understands a little", "The room as a whole understands Chinese well", "The room understands Chinese just as a native speaker does"], "evaluative")
C("If the person in the Chinese room memorised the entire rulebook and did everything in their head, would they then understand Chinese?",
  [("yes", None), ("no", None), ("a_second_mind_would_understand", "a separate mind would form inside them"), ("not_sure", None)], "evaluative")
N("If a robot followed the Chinese room rules but also had cameras and arms, linking words to objects, would it understand Chinese?", "evaluative")
C("What does the Chinese room show, if anything?",
  [("computers_cannot_understand", None), ("understanding_needs_more_than_rules", None), ("understanding_is_in_the_system", None), ("our_intuitions_are_unreliable", None), ("nothing_useful", None), ("other", None)], "evaluative")
N("If you exchanged letters for years with someone who turned out to be a Chinese room, would your friendship have been real?", "social")
S("A translator app answers you perfectly in your language using rules it cannot explain. When it says 'I understand', how accurate is that?",
  ["It is simply false; nothing understands", "It is misleading, a figure of speech at best", "It is partly true in a limited, practical sense", "It is mostly true in every way that matters", "It is completely true"], "evaluative")

# ---------- Mary's room / knowledge argument ----------
C("A color scientist who has always lived in a black-and-white room knows every physical fact about color. What is she missing, if anything?",
  [("an_experience", "what red looks like"), ("a_new_fact", None), ("a_new_ability", "to recognise and imagine red"), ("nothing", None), ("not_sure", None)], "evaluative")
N("If someone has read everything about the taste of coffee but never tasted it, do they know what coffee tastes like?", "evaluative")
S("Imagine a scientist who has studied pain in every detail but has a condition that means they have never felt pain. How well do they understand pain?",
  ["They do not understand pain at all", "They understand it only from the outside", "They understand it well except for one piece", "They understand it almost fully", "They understand it completely"], "evaluative")
N("If a person born deaf learned everything science knows about music, would they know what a symphony is like?", "evaluative")
C("A person who has only seen the world in black and white is shown a red apple and a green apple with no labels. Would they know which one is red?",
  [("yes", "their scientific knowledge would tell them"), ("no", None), ("only_by_measuring", None), ("not_sure", None)], "evaluative")
S("Someone argues that no amount of reading about an experience can replace having it. How much do you agree?",
  ["Reading can fully replace having an experience", "Reading can replace most of an experience", "Reading covers some but misses something important", "Reading misses nearly everything that matters", "Reading can never capture what an experience is like"], "evaluative")

# ---------- What is it like to be a bat ----------
C("Could a human ever know what it is like to be a bat that sees the world through echoes?",
  [("yes_with_enough_science", None), ("yes_with_technology", "a device that lets us perceive echoes"), ("only_roughly", None), ("never", None), ("not_sure", None)], "evaluative")
N("If a device let you hear the world the way a bat does for an hour, would you try it?", "personality")
S("Scientists fully map a dolphin's brain. How much would you then know about what it feels like to be that dolphin?",
  ["Nothing about how it feels", "A few hints about how it feels", "A rough picture of how it feels", "A good picture of how it feels", "Everything about how it feels"], "evaluative")
N("If you could briefly swap perspectives with an animal and then return, would you choose to do it?", "personality")
C("Which animal's experience would you most want to understand from the inside?",
  [("bat", None), ("octopus", None), ("dog", None), ("bird_in_flight", None), ("whale", None), ("bee", None), ("other", None)], "personality")

# ---------- Philosophical zombies ----------
S("Imagine a being that looks and acts exactly like a human, even saying 'I am in pain', but has no inner experience at all. How possible is such a being?",
  ["Completely impossible; acting exactly like us means having experience", "Barely imaginable, but not really possible", "Imaginable, but I cannot tell whether it could exist", "Possible in principle, if unlikely in our world", "Clearly possible, and it could even exist among us"], "evaluative")
N("If you found out a coworker was a being with no inner experience who behaved exactly like a person, would you treat them any differently?", "social")
C("A being with no inner experience cries out when injured, exactly as a human would. What is the right way to treat it?",
  [("as_a_person", "because we cannot be sure"), ("with_basic_courtesy", None), ("as_an_object", None), ("depends_on_the_situation", None), ("not_sure", None)], "values")
N("Would it be wrong to break a promise made to a being with no inner experience that behaves exactly like a person?", "values")
S("Suppose half the people you meet were beings with no inner life but you could never tell which. How would that change your kindness toward strangers?",
  ["I would stop bothering to be kind to strangers", "I would be kind only when it cost me nothing", "I would be a little more guarded but mostly the same", "I would be exactly as kind as before", "I would be kinder, to be safe"], "social")
C("If a being with no inner experience wrote a moving poem about sadness, what would the poem be worth?",
  [("as_much_as_any_poem", None), ("less_than_a_human_poem", None), ("nothing", None), ("depends_on_the_reader", "its worth is in how it moves readers"), ("not_sure", None)], "evaluative")

# ---------- Inverted spectrum ----------
N("Could the color you see as red look to someone else the way green looks to you, without either of you ever discovering it?", "evaluative")
C("If you learned that your partner sees all colors inverted compared with you, but you both use the same color words, how much would it matter?",
  [("not_at_all", None), ("a_little_curious", None), ("it_would_feel_strange", None), ("it_would_matter_a_lot", None), ("not_sure", None)], "social")
S("Two people agree on every color name but might see colors differently inside. How much do they share when they both call a sunset beautiful?",
  ["They share nothing but the words", "They share the words and some behaviour", "They share a lot, though their experiences may differ", "They share nearly everything that matters", "They share the experience itself"], "evaluative")
N("If a surgeon could secretly swap how you see red and green overnight, would you notice anything the next morning?", "evaluative")
C("If a friend's experiences of sweet and sour were swapped but their taste in food stayed the same, what would have changed?",
  [("nothing_that_matters", None), ("their_inner_experience", None), ("their_preferences", None), ("everything", None), ("not_sure", None)], "evaluative")

# ---------- Swampman ----------
S("Lightning strikes a swamp and, by pure chance, forms an exact copy of a person who just died nearby, with all their memories. The copy walks home. How should their spouse treat them?",
  ["As a stranger who must leave", "As a guest who can stay while things are sorted out", "As a new person who deserves a fresh relationship", "As their spouse, with some unease", "As their spouse, exactly as before"], "social")
N("If a creature formed by chance from swamp matter had all your memories, would its memories of your childhood count as real memories?", "evaluative")
C("A chance copy of a person forms from swamp matter at the moment they die. Which of the dead person's things should it own?",
  [("everything", None), ("personal_items_only", None), ("nothing", None), ("whatever_the_family_agrees", None), ("not_sure", None)], "values")
N("If a chance copy of a writer formed from lightning and finished the writer's last novel, should the book carry the writer's name?", "values")

# ---------- Newcomb ----------
C("A near-perfect predictor places a prize in a closed box only if it predicted you would leave the smaller open prize behind. What reason best explains your choice?",
  [("predictor_is_reliable", "one-boxers almost always win"), ("prize_already_placed", "my choice cannot change what is in the box"), ("i_would_randomise", None), ("i_would_refuse_to_play", None), ("not_sure", None)], "evaluative")
N("In a game where a near-perfect predictor fills a closed box only if it expects you to take that box alone, would you be tempted to take both boxes at the last second?", "personality")
S("In a game with a near-perfect predictor, a friend takes both boxes and finds the closed one empty. How would you judge their choice?",
  ["They made a clear mistake anyone could see", "They made a mistake, though I understand the logic", "It was a reasonable choice either way", "It was the smarter choice, even though it lost", "It was clearly the right choice; they were just unlucky"], "evaluative")
N("If the predictor in a two-box game were a close friend who knows you very well rather than a machine, would you take only the closed box?", "social")
C("In a two-box prediction game, the closed box is made of glass so you can see the large prize already inside. What do you do?",
  [("take_both", None), ("take_only_the_glass_box", None), ("not_sure", None)], "evaluative")

# ---------- Parfit's spectrum / gradual change ----------
S("Scientists could change your brain and body in tiny steps until you became exactly like a famous stranger. At which point would you stop being you?",
  ["After the very first tiny change", "Early, once a few memories were gone", "Somewhere in the middle, though I could not say where", "Only near the very end", "There is no point; the question has no real answer"], "evaluative")
N("If you would become a different person only through a long series of steps that each seem harmless, should you refuse the first step?", "values")
C("If your personality changed completely because of an illness, would you want loved ones to treat you as the person you were or the person you became?",
  [("who_i_was", None), ("who_i_became", None), ("a_mix", None), ("whatever_makes_them_happier", None), ("not_sure", None)], "social")
S("Suppose personal identity turns out to be a matter of degree rather than all or nothing. How would that change your fear of death?",
  ["It would make no difference to my fear", "It would reduce my fear slightly", "It would change how I think about my fear, not the fear itself", "It would make me fear death much less", "It would make my fear of death disappear"], "personality")
N("Would you care less about your future self decades from now if you believed they would be only partly the same person as you?", "personality")
C("Which would you rather keep if your future self had to lose one?",
  [("memories", None), ("values", None), ("relationships", None), ("personality", None), ("skills", None), ("other", None)], "values")

# ---------- Twin Earth ----------
S("On a planet identical to ours, the clear liquid in lakes and rain looks and tastes like water but is a different substance. When people there say 'water', do they mean the same thing as us?",
  ["They mean exactly the same thing", "They mean mostly the same thing", "It is unclear what they mean", "They mean something slightly different", "They mean something entirely different"], "evaluative")
N("If you were secretly moved to a distant planet with a water-like liquid that is chemically different, would your word 'water' eventually start to mean that liquid?", "evaluative")
C("On a twin planet, a word sounds and is used exactly like 'gold' but refers to a different metal. Does a person there who says 'gold' think the same thought as you?",
  [("same_thought", None), ("different_thought", None), ("same_thought_different_object", None), ("not_sure", None)], "evaluative")

# ---------- Pascal's mugging (secular) ----------
S("A stranger says that if you give them a small amount of pocket money, they will use secret powers to give you a fortune tomorrow. They admit it is almost certainly untrue. How would you respond?",
  ["I would walk away without a thought", "I would laugh it off, maybe with a joke", "I would feel a flicker of temptation but decline", "I would give a tiny amount just in case", "I would pay, since the possible reward is so large"], "personality")
N("Should a wildly unlikely chance of a huge reward ever outweigh a small, certain cost?", "evaluative")
C("A stranger claims, with no evidence, that ignoring their request will cause some vast harm elsewhere. What is the right response?",
  [("ignore_it", None), ("ask_for_proof", None), ("pay_a_little_just_in_case", None), ("report_them", None), ("it_depends_on_the_cost", None), ("other", None)], "evaluative")

# ---------- Sorites ----------
C("If you remove grains from a heap of sand one at a time, when does it stop being a heap?",
  [("at_a_sharp_point", "one grain makes the difference, even if we cannot find it"), ("gradually", "it becomes less and less of a heap"), ("never_clear", "there is no fact of the matter"), ("heaps_do_not_really_exist", None), ("not_sure", None)], "evaluative")
N("Is there an exact moment when a person goes from not bald to bald?", "evaluative")
S("A friend argues that because no single hair lost makes someone bald, nobody is ever bald. How do you respond?",
  ["I cannot find anything wrong with the argument", "I suspect a trick but cannot say what", "I think the argument shows words are vague", "I think vague words still apply to clear cases", "I think the argument is obviously silly"], "evaluative")
N("If a child grows up one day at a time, is there a single day they become an adult?", "evaluative")
C("Which shows most clearly that ordinary words have blurry edges?",
  [("heap", None), ("tall", None), ("bald", None), ("adult", None), ("rich", None), ("red", "the shift from red to orange"), ("none", None)], "evaluative")

# ---------- Ring of Gyges ----------
S("You find a ring that makes you invisible whenever you wear it, and nobody would ever find out what you did with it. How would you use it?",
  ["I would never use it", "I would use it only for harmless fun", "I would use it for small rule-breaking, like sneaking into places", "I would use it to take things I felt I deserved", "I would use it to do whatever I wanted"], "personality")
N("If you had a ring of invisibility that no one knew about, would you ever use it to take something that is not yours?", "personality")
C("If most people were given a secret ring of invisibility, what would happen?",
  [("most_stay_honest", None), ("most_do_small_wrongs", None), ("most_do_serious_wrongs", None), ("most_help_others_secretly", None), ("not_sure", None)], "social")
N("Is a person who behaves well only because they fear being caught really a good person?", "values")
C("If a ring of invisibility could be given to one person you know, whom would you trust with it most?",
  [("myself", None), ("my_best_friend", None), ("a_family_member", None), ("my_partner", None), ("nobody", None), ("other", None)], "social")
S("With a ring of invisibility you could secretly watch anyone you liked. How tempted would you be to spy on people you know?",
  ["Not tempted at all; I would find it repellent", "Tempted briefly, then I would refuse", "I might check on one person I worry about", "I would look in on a few people out of curiosity", "I would spy regularly"], "personality")

# ---------- Molyneux ----------
N("If someone born blind who had learned shapes by touch suddenly gained sight, could they tell a cube from a sphere just by looking?", "evaluative")
C("A person blind from birth gains sight as an adult. What would be hardest for them at first?",
  [("recognising_faces", None), ("judging_distance", None), ("matching_seen_shapes_to_felt_ones", None), ("recognising_colors", None), ("reading", None), ("other", None)], "evaluative")

# ---------- Frankfurt cases ----------
S("A person decides on their own to lie. Unknown to them, a device in their brain would have forced them to lie anyway if they had wavered. How responsible are they for the lie?",
  ["Not responsible at all, since they could not have done otherwise", "Slightly responsible", "Partly responsible", "Mostly responsible", "Fully responsible, since they chose it themselves"], "values")
N("If you could not have acted differently but you acted exactly as you wanted to, were you still acting freely?", "evaluative")
C("A scientist can secretly control your decisions but has never needed to, because you always chose what they wanted anyway. Are your choices free?",
  [("yes", None), ("no", None), ("free_but_less_meaningful", None), ("not_sure", None)], "evaluative")

# ---------- Buridan's ass ----------
C("A hungry donkey stands exactly between two identical piles of hay. What should it do?",
  [("pick_either_at_random", None), ("wait_for_a_reason", None), ("eat_from_both", None), ("it_would_starve", None), ("not_sure", None)], "evaluative")
S("When you face two options that seem exactly equal, what do you usually do?",
  ["I get stuck and often choose neither", "I delay for a long time looking for a difference", "I ask someone else to decide", "I flip a coin or pick at random", "I pick one immediately and move on"], "personality")
N("If two choices are perfectly equal, is picking one at random still a real decision?", "evaluative")

# ---------- Predictor / foreknowledge ----------
S("A machine that has never been wrong predicts what you will order at a restaurant and seals the prediction in an envelope. How would you feel while ordering?",
  ["I would feel my choice was entirely fake", "I would feel uneasy and try to trick it", "I would feel curious but order normally", "I would feel it does not change my freedom", "I would find it fun and not think twice"], "personality")
N("If a machine that is never wrong predicted you would betray a friend, would you still be to blame if you did?", "values")
C("A machine that has never been wrong tells you which job you will take next year. What would you do?",
  [("try_to_prove_it_wrong", None), ("accept_it", None), ("ask_it_more_questions", None), ("ignore_it", None), ("not_sure", None)], "personality")
N("If a perfect predictor told you what you will be doing on some future morning, would you want to know?", "personality")

# ---------- Veil of ignorance (non-political) ----------
C("You are designing a family household's rules without knowing whether you will be a parent, a child, or a grandparent in it. What would you prioritize?",
  [("fair_chores", None), ("everyone_gets_a_say", None), ("protect_the_weakest", None), ("freedom_for_each", None), ("strong_leadership", None), ("other", None)], "values")
N("If you were designing a school's rules without knowing whether you would be a teacher or a student, would you choose the same rules you would pick as a student?", "values")
S("You are setting up a board game's rules before learning which player you will be. How would you balance the starting positions?",
  ["I would give one player a big advantage and gamble on being them", "I would allow a small advantage for the first player", "I would make the positions roughly even", "I would make them exactly even", "I would give extra help to whoever starts in the worst spot"], "values")

# ---------- Sleeping Beauty / anthropic ----------
C("A person is put to sleep, woken once or twice depending on a coin flip, and made to forget each waking. On waking, how should they think about whether the coin landed heads?",
  [("even_odds", "nothing new was learned"), ("less_likely_than_tails", "wakings are more common on tails"), ("more_likely", None), ("the_question_is_confused", None), ("not_sure", None)], "evaluative")
N("If you woke up with no memory of whether you had been woken before, would that fact alone give you information about the past?", "evaluative")

# ---------- Lottery and preface paradoxes ----------
N("If you hold a ticket in a huge lottery, can you truly know that your ticket will lose?", "evaluative")
C("An author believes each claim in her book is true but admits the book surely contains some error. Is she being irrational?",
  [("no_that_is_sensible", None), ("yes_a_contradiction", None), ("a_little_but_forgivable", None), ("not_sure", None)], "evaluative")
S("You are almost certain your lottery ticket will lose. How should you talk about it?",
  ["I know I will lose", "I will almost surely lose", "I will probably lose, but it is a real chance", "I have no idea whether I will win", "I might well win"], "evaluative")

# ---------- Surprise exam ----------
C("A teacher announces a surprise test next week that students cannot predict the day of. A student reasons that such a test is impossible. What is wrong with the reasoning?",
  [("nothing_it_is_impossible", None), ("the_student_is_overthinking", None), ("the_announcement_contradicts_itself", None), ("surprise_is_still_possible", None), ("not_sure", None)], "evaluative")
N("If someone tells you to expect a surprise, can it still truly surprise you?", "evaluative")

# ---------- Grue / induction ----------
S("A word 'grue' means green until some future moment and blue after it. Every emerald so far fits both 'green' and 'grue'. How reasonable is it to expect future emeralds to be grue?",
  ["Just as reasonable as expecting them to be green", "Somewhat reasonable", "Hardly reasonable", "Unreasonable", "Plainly absurd"], "evaluative")
N("Can we ever be justified in believing the sun will rise tomorrow just because it always has?", "evaluative")
C("A turkey is fed every morning and grows sure that it will be fed every morning, until one day it is not. What is the lesson?",
  [("past_patterns_can_mislead", None), ("look_for_the_reason_behind_patterns", None), ("expect_the_unexpected", None), ("it_was_right_to_trust_the_pattern", None), ("no_lesson", None), ("other", None)], "evaluative")

# ---------- Perfect lie detector world ----------
C("Imagine a world where everyone wears a device that lights up whenever anyone tells a lie. What would change most?",
  [("friendships", None), ("romance", None), ("business", None), ("family_life", None), ("small_talk", None), ("courts", None), ("other", None)], "social")
S("In a world where every lie is instantly detected, how would you handle a friend asking whether you like their new haircut that you dislike?",
  ["I would say I dislike it outright", "I would say it is not my favourite", "I would praise something else about them instead", "I would avoid answering", "I would try to feel differently so I could say I like it"], "social")
C("If a perfect lie detector became cheap and available to anyone, what would you use it for first?",
  [("checking_my_partner", None), ("checking_salespeople", None), ("checking_myself", "to catch self-deception"), ("checking_friends", None), ("would_not_use_it", None), ("other", None)], "social")
S("A world with perfect lie detection would end all lying. How would that world compare with ours?",
  ["Far worse; small lies hold society together", "Somewhat worse", "About the same, just different", "Somewhat better", "Far better; honesty would transform everything"], "evaluative")

# ---------- Pill to stop caring / value-change pills ----------
C("A pill would make you stop caring about something that currently causes you pain. What would you want it to remove?",
  [("fear_of_failure", None), ("what_others_think", None), ("an_old_heartbreak", None), ("worry_about_the_future", None), ("nothing", "I would not take it"), ("other", None)], "values")
S("A pill would make you stop caring about the approval of others entirely. How would you feel about taking it?",
  ["I would refuse; caring about others' views is part of who I am", "I would refuse, though I see the appeal", "I would take a milder version if it existed", "I would take it after some thought", "I would take it immediately"], "values")
C("A pill would make you love a partner you currently feel lukewarm about. Would taking it make the love real?",
  [("yes_love_is_love", None), ("no_it_would_be_fake", None), ("real_but_less_valuable", None), ("depends_on_the_partner", None), ("not_sure", None)], "evaluative")
S("A pill could make you enjoy tasks you currently hate, like doing paperwork. How willing would you be to take it?",
  ["I would never take it; it would change who I am", "I would take it only if my job depended on it", "I would take it for a trial period", "I would take it happily", "I would take it and ask for more pills like it"], "values")
C("A pill can make you perfectly content with your life as it is, without changing anything around you. What would be the biggest cost?",
  [("losing_ambition", None), ("losing_the_urge_to_help_others", None), ("losing_self_knowledge", None), ("becoming_easy_to_exploit", None), ("no_real_cost", None), ("other", None)], "evaluative")
S("A pill would permanently make you more compassionate but a little less ambitious. How would you decide?",
  ["I would refuse outright", "I would lean toward refusing", "I would be torn and need a long time", "I would lean toward taking it", "I would take it without hesitation"], "values")
C("A pill would make you forget a person who hurt you badly, as if you had never met. Would you take it?",
  [("yes", None), ("no_the_memory_teaches_me", None), ("no_it_is_part_of_me", None), ("only_if_the_pain_never_fades", None), ("not_sure", None)], "values")

# ---------- Mind reading machine ----------
C("A machine could let you read one person's thoughts for a single day. Whose would you choose?",
  [("my_partner", None), ("a_parent", None), ("my_best_friend", None), ("my_boss", None), ("a_rival", None), ("a_stranger", None), ("nobody", None), ("other", None)], "social")
S("A mind-reading device lets anyone see your passing thoughts. How would that affect the way you think?",
  ["I would stop thinking freely at all", "I would try to censor many of my thoughts", "I would feel self-conscious but think mostly as usual", "I would barely change", "I would not change at all; I have nothing to hide"], "personality")
C("If everyone's thoughts were visible to everyone else, what would become most valuable?",
  [("kindness", None), ("self_control", None), ("forgiveness", None), ("solitude", None), ("humor", None), ("other", None)], "values")
S("If you could read your partner's mind whenever you wanted, how often would you use it?",
  ["Never; I would not want to know", "Only in a real crisis", "Now and then, when I was unsure how they felt", "Often, to keep things smooth", "Constantly"], "social")

# ---------- Eternal recurrence variations ----------
C("A voice tells you that you will live your life again and again forever, exactly the same each time. What would you change about how you live now?",
  [("nothing", None), ("take_more_risks", None), ("be_kinder", None), ("spend_more_time_with_loved_ones", None), ("work_less", None), ("fix_old_mistakes", None), ("other", None)], "values")
S("If you knew you would relive your life forever, how would you feel about your worst day?",
  ["It would make my whole life unbearable to repeat", "It would weigh heavily on me", "I would accept it as part of the package", "I would see it as necessary for the good days", "I would embrace it gladly"], "personality")
C("If you would relive your life forever but could change one habit first, which would you change?",
  [("worrying_less", None), ("being_more_patient", None), ("exercising_more", None), ("spending_less_time_on_screens", None), ("saying_what_i_feel", None), ("none", None), ("other", None)], "values")

# ---------- Brain in a jar with memory implant / false memories ----------
S("A surgeon gives you an implanted memory of a wonderful holiday you never took. How much would you value that memory?",
  ["Not at all; it would feel like a lie", "A little, like a nice dream", "Somewhat, even knowing it was fake", "Almost as much as a real holiday", "Just as much as a real holiday"], "values")
C("If you could buy a false memory of any experience, which would you choose?",
  [("climbing_a_great_mountain", None), ("a_childhood_with_more_joy", None), ("meeting_a_hero", None), ("performing_on_stage", None), ("travelling_the_world", None), ("none", None), ("other", None)], "values")
S("You discover that one of your fondest childhood memories was implanted without your knowledge. How would you react?",
  ["I would feel my whole past is now suspect", "I would feel betrayed and grieve the memory", "I would feel strange but keep the memory", "I would shrug; it still feels good", "I would be grateful someone gave me a nice memory"], "personality")
C("If your memories could be edited, who should have the right to edit them?",
  [("only_me", None), ("me_and_a_doctor", None), ("my_family", None), ("nobody", None), ("not_sure", None)], "values")

# ---------- Cells / body replacement ----------
C("If every part of your body were gradually replaced with lab-grown parts, what would keep you the same person?",
  [("my_memories", None), ("my_brain_continuity", None), ("my_personality", None), ("my_relationships", None), ("nothing", None), ("other", None)], "evaluative")
S("If a lab could grow you a new, younger body and move your brain into it, how would you view the old body afterward?",
  ["As me, and I would mourn it like a death", "As a close part of me I lost", "Like an old home I moved out of", "Like worn clothing I no longer need", "As something that was never really me"], "personality")

# ---------- Duplicates and copies: more ----------
C("A perfect duplicate of you appears and wants to live your life. How would you settle who gets to keep it?",
  [("coin_flip", None), ("take_turns", None), ("split_it", "one takes work, one takes home"), ("both_start_fresh", None), ("ask_loved_ones", None), ("other", None)], "social")
S("Someone makes a perfect copy of your best friend, and the copy wants to be friends with you too. How would you respond?",
  ["I would refuse to have anything to do with the copy", "I would be polite but distant", "I would get to know them slowly", "I would treat them as a second best friend", "I would treat them exactly like my best friend"], "social")
C("If you could send a copy of yourself to live a different life you gave up on, which life would it live?",
  [("different_career", None), ("different_country", None), ("different_partner", None), ("life_of_travel", None), ("simpler_life", None), ("would_not_send_one", None), ("other", None)], "values")
S("Your duplicate lives in another city and makes choices you disagree with. How would that feel?",
  ["It would not bother me; they are someone else", "It would bother me only a little", "It would feel strange, like watching a sibling", "It would feel like I was making those mistakes", "It would be deeply upsetting, like losing control of myself"], "personality")
C("A duplicate of you was made yesterday and today it apologises to your friend for something you did last week. Does the apology count?",
  [("yes_fully", None), ("partly", None), ("no", None), ("only_if_i_agree", None), ("not_sure", None)], "social")

# ---------- Experience machine: more ----------
S("An experience machine could give you the exact feeling of reuniting with an old friend you have lost touch with. How would you choose between the machine and a real but awkward reunion?",
  ["I would choose the machine every time", "I would lean toward the machine", "I would find it hard to choose", "I would lean toward the real reunion", "I would choose the real reunion without doubt"], "social")
C("If experience machines became common, what would happen to society?",
  [("most_people_plug_in", None), ("a_minority_plug_in", None), ("society_collapses", None), ("people_use_them_like_holidays", None), ("they_get_banned", None), ("other", None)], "social")
S("An experience machine can only make you feel as though you have close friends. How lonely would you feel inside it?",
  ["Not lonely at all", "Occasionally lonely when I remembered", "Lonely beneath the surface", "Lonely most of the time", "More lonely than ever"], "personality")

# ---------- Identity puzzles: more ----------
C("If you woke up tomorrow in a different body with all your memories, who would you tell first?",
  [("partner", None), ("parent", None), ("best_friend", None), ("doctor", None), ("nobody", None), ("other", None)], "social")
S("If you woke up in a stranger's body, how long would it take before you felt at home in it?",
  ["I would never feel at home", "Years", "Months", "A few weeks", "A day or two"], "personality")
C("Imagine your memories were split between two new bodies, half in each. Which would you care most about protecting?",
  [("the_one_with_childhood_memories", None), ("the_one_with_recent_memories", None), ("both_equally", None), ("neither_is_me", None), ("not_sure", None)], "evaluative")
S("A person with severe amnesia reads a detailed diary of their past life. How much would reading it restore who they were?",
  ["Not at all; they would read it like a stranger's story", "A little; it would give them facts, not identity", "Partly; they would rebuild some sense of self", "Mostly; they would feel like themselves again", "Completely; the diary would return them to themselves"], "evaluative")
C("If you could remember everything from every day of your life perfectly, would you choose that?",
  [("yes", None), ("no_too_much_pain", None), ("no_forgetting_is_healthy", None), ("only_the_good_days", None), ("not_sure", None)], "values")

# ---------- Other puzzles ----------
C("You are offered the choice to know one truth that would change your whole view of reality, but you could never tell anyone. Would you take it?",
  [("yes", None), ("no_i_would_want_to_share_it", None), ("no_ignorance_is_safer", None), ("only_if_it_is_good_news", None), ("not_sure", None)], "values")
S("A genie offers to answer one deep question about reality truthfully, but the answer might be unsettling. How would you approach it?",
  ["I would decline the offer", "I would ask something safe and small", "I would ask something important after careful thought", "I would ask the biggest question I could think of", "I would ask the question most likely to overturn everything"], "personality")
C("A drug could let you make a single afternoon feel like it lasts for weeks. What would you do with that afternoon?",
  [("read_and_learn", None), ("be_with_loved_ones", None), ("create_something", None), ("rest", None), ("would_not_take_it", None), ("other", None)], "personality")
C("Imagine a society where everyone must forget their own names and pasts each morning. What would hold it together?",
  [("routines", None), ("written_records", None), ("kindness_to_strangers", None), ("strong_rules", None), ("nothing", None), ("other", None)], "evaluative")
S("A device lets you feel exactly what a stranger feels for a day. How would that change the way you treat strangers?",
  ["It would not change anything", "It would change how I treat that one person", "It would make me a little more patient with strangers", "It would make me noticeably kinder", "It would transform how I treat everyone"], "social")
C("If you could live one extra life as someone completely different, then return to your own, whose life would you live?",
  [("someone_very_rich", None), ("someone_very_poor", None), ("someone_of_another_culture", None), ("an_animal", None), ("someone_of_another_era", None), ("would_not", None), ("other", None)], "personality")
C("Suppose we learned that everything in the universe froze for a long time every night and then continued, with no one able to notice. Would that matter?",
  [("not_at_all", None), ("only_intellectually", None), ("it_would_unsettle_me", None), ("it_would_change_how_i_live", None), ("not_sure", None)], "evaluative")
S("You learn that the world is exactly the same as it would be if it had been created a moment ago with a full history built in. How would that change your trust in history books?",
  ["I would stop trusting them entirely", "I would trust them much less", "I would trust them a little less", "I would trust them just the same", "I would trust them more, since they are all I have"], "evaluative")
C("If a machine could predict exactly how any argument you start will end, would you still argue with people?",
  [("yes_for_the_fun", None), ("yes_for_the_connection", None), ("only_when_i_would_win", None), ("no", None), ("not_sure", None)], "social")
C("A person has a perfect twin who knows them completely. If that twin makes a promise on their behalf, should they keep it?",
  [("yes", None), ("only_if_i_agree", None), ("no", None), ("depends_on_the_promise", None), ("not_sure", None)], "values")
S("Imagine you are told that you will wake up tomorrow with no memory of today. How would you spend today?",
  ["I would waste it, since it will not count", "I would relax and not bother with anything important", "I would live it as normal", "I would do things that help my future self", "I would treat it as especially precious"], "values")
C("A time machine lets you watch, but not change, any moment in history. Which kind of moment would you watch?",
  [("a_great_discovery", None), ("a_famous_speech", None), ("my_own_birth", None), ("my_ancestors_meeting", None), ("the_beginning_of_life", None), ("other", None)], "personality")
C("If you could see your whole life story written out in advance, would you read it?",
  [("all_of_it", None), ("only_the_good_parts", None), ("only_the_next_chapter", None), ("none_of_it", None), ("not_sure", None)], "personality")
S("A thought experiment asks you to imagine you were born into a completely different family and culture. How different do you think you would be?",
  ["Exactly the same person underneath", "Mostly the same person with different habits", "A fairly different person", "A very different person", "Someone with nothing in common with me"], "evaluative")
C("If aliens offered to reveal every scientific law they know, but only to you, what would you do?",
  [("share_it_with_scientists", None), ("share_it_slowly", None), ("keep_it_secret", None), ("refuse_the_offer", None), ("not_sure", None)], "values")
S("A button would make the whole world forget you exist, but would guarantee you a comfortable life. How tempted would you be?",
  ["Not at all; being known is everything to me", "Barely; the comfort is not worth it", "Somewhat, on hard days", "Quite tempted", "I would press it"], "personality")
C("Suppose a device could let you share your dreams with someone else each night. Who would you share them with?",
  [("partner", None), ("best_friend", None), ("family_member", None), ("a_therapist", None), ("nobody", None), ("other", None)], "social")
S("An oracle that is always right says a decision you made long ago was a mistake. How much would you trust that judgment over your own?",
  ["I would reject it; only I can judge my life", "I would doubt it", "I would consider it seriously", "I would mostly accept it", "I would accept it completely"], "evaluative")
C("If you could press a button to experience the entire life of another person in an instant, who would you choose?",
  [("a_historical_figure", None), ("a_parent", None), ("my_partner", None), ("a_stranger", None), ("someone_i_dislike", None), ("nobody", None), ("other", None)], "personality")

# ---------- More coverage ----------
C("A perfect robot pet behaves exactly like a real dog, including showing affection. What would you be missing compared with a real dog?",
  [("its_real_feelings", None), ("its_unpredictability", None), ("the_responsibility", None), ("nothing", None), ("not_sure", None)], "evaluative")
C("If a brain could be kept alive in a lab with no body but with full memories, what would it most need to stay the same person?",
  [("conversation_with_loved_ones", None), ("a_simulated_body", None), ("purpose_or_work", None), ("its_memories_alone", None), ("nothing_it_would_already_be_the_same", None), ("other", None)], "evaluative")
C("An exact copy of the Mona Lisa is so perfect that no expert can tell it from the original. Which would you rather own?",
  [("the_original", None), ("the_copy", "if it cost far less"), ("either", None), ("neither", None)], "values")
C("If a forged painting fooled every expert for centuries, was it ever less beautiful than a genuine work?",
  [("no_beauty_is_in_the_seeing", None), ("yes_the_story_matters", None), ("equally_beautiful_but_less_valuable", None), ("not_sure", None)], "evaluative")
C("If you met a perfect copy of a deceased loved one, created from their memories, what would you most want to do?",
  [("say_goodbye", None), ("spend_time_together", None), ("ask_questions", None), ("avoid_them", None), ("not_sure", None)], "social")
C("You learn your memory of a key event was wrong, but it shaped who you are. What matters more to who you are?",
  [("the_real_event", None), ("the_memory", None), ("both_equally", None), ("neither", None), ("not_sure", None)], "evaluative")
C("An exact duplicate of your house appears next door, with copies of all your belongings. Which one is your home?",
  [("the_original_house", None), ("whichever_i_live_in", None), ("both", None), ("neither", None), ("not_sure", None)], "evaluative")
C("A machine lets you pause the whole world while you keep moving. What would you use the paused time for most?",
  [("rest", None), ("study_or_work", None), ("think_before_decisions", None), ("explore_quietly", None), ("would_not_use_it", None), ("other", None)], "personality")
C("If a writer's mind were uploaded and it wrote new novels, whose novels would they be?",
  [("the_writer", None), ("the_upload", None), ("the_company_running_it", None), ("nobody", None), ("not_sure", None)], "values")
C("Scientists grow a brain in a lab and it shows signs of dreaming. What should they do?",
  [("keep_studying_it", None), ("give_it_protections", None), ("stop_the_experiment", None), ("try_to_communicate", None), ("not_sure", None)], "values")
C("If you learned that your free choices were all produced by chemistry you did not control, what would change?",
  [("nothing", None), ("i_would_blame_people_less", None), ("i_would_blame_myself_less", None), ("i_would_feel_less_proud", None), ("i_would_feel_trapped", None), ("other", None)], "evaluative")
C("A stone is carved one chip at a time into a statue. When does the statue begin to exist?",
  [("at_the_first_chip", None), ("when_the_shape_is_recognisable", None), ("when_the_sculptor_finishes", None), ("it_was_always_in_the_stone", None), ("there_is_no_moment", None), ("other", None)], "evaluative")
C("A lump of clay is shaped into a statue and later squashed back into a lump. Is the clay the same thing as the statue?",
  [("yes_the_same", None), ("no_two_things_in_one_place", None), ("only_while_shaped", None), ("not_sure", None)], "evaluative")
C("Suppose a being could remember the future but not the past. What would it find hardest to understand about us?",
  [("regret", None), ("hope", None), ("surprise", None), ("nostalgia", None), ("planning", None), ("other", None)], "evaluative")
C("If you could send one message back to yourself at a younger age, but it might change who you are now, would you send it?",
  [("yes", None), ("no_i_like_who_i_am", None), ("only_a_small_hint", None), ("not_sure", None)], "values")
C("A perfect virtual version of your hometown lets you visit it as it was in your childhood. How often would you visit?",
  [("never", None), ("once", None), ("on_special_occasions", None), ("regularly", None), ("i_would_live_there", None)], "personality")
C("If you could step into a world where every decision you ever regretted went the other way, would you want to see it?",
  [("yes", None), ("no_it_would_hurt", None), ("only_briefly", None), ("not_sure", None)], "personality")
C("A computer program claims to be the reincarnation of your childhood imaginary friend and knows all your secret games. What is your first reaction?",
  [("delight", None), ("suspicion", None), ("fear", None), ("curiosity", None), ("amusement", None), ("other", None)], "personality")
C("If you discovered that every person you have met is played by the same single being, what would you do?",
  [("confront_it", None), ("keep_living_normally", None), ("withdraw_from_people", None), ("try_to_befriend_it", None), ("not_sure", None)], "social")
C("Imagine the universe resets to its beginning every so often with everything replayed identically. Does anything you do now still matter?",
  [("yes_fully", None), ("yes_but_less", None), ("only_to_me", None), ("no", None), ("not_sure", None)], "evaluative")
C("A mirror world is identical to ours except left and right are swapped. If you were swapped into it, what would you notice?",
  [("nothing", None), ("my_handwriting_feels_odd", None), ("faces_look_wrong", None), ("everything_feels_off", None), ("not_sure", None)], "evaluative")
C("If a hologram of you could attend events on your behalf and say what you would say, would you use it?",
  [("for_work_only", None), ("for_boring_events", None), ("for_everything", None), ("never", None), ("not_sure", None)], "social")
C("A thought experiment asks you to imagine a colour no human has ever seen. What happens when you try?",
  [("i_can_almost_imagine_it", None), ("i_only_get_mixtures_of_known_colours", None), ("nothing_at_all", None), ("i_get_a_feeling_not_a_colour", None), ("other", None)], "personality")
C("If your future self could send you a one-word warning, which would you most expect it to be?",
  [("slow_down", None), ("save", None), ("rest", None), ("call_home", None), ("relax", None), ("other", None)], "personality")
C("A book contains a true account of every thought you have ever had. Who, if anyone, should be allowed to read it?",
  [("only_me", None), ("my_partner", None), ("my_family_after_my_death", None), ("nobody_including_me", None), ("anyone", None), ("other", None)], "values")
C("If you learned the people in your dreams were real minds somewhere else, how would you treat them?",
  [("with_the_same_care_as_waking_people", None), ("more_carefully_than_before", None), ("no_differently", None), ("not_sure", None)], "values")
C("Imagine a machine that could make you believe anything you chose. Which belief would you pick?",
  [("i_am_loved", None), ("everything_will_be_fine", None), ("my_life_has_meaning", None), ("i_am_talented", None), ("would_not_use_it", None), ("other", None)], "values")
C("If a vast library contained every possible book, including your life story with every variation, would your real life feel less special?",
  [("yes", None), ("no", None), ("only_a_little", None), ("not_sure", None)], "evaluative")
C("A room contains a perfect model of the universe, including a model of the room itself. What does that puzzle make you think?",
  [("it_is_impossible", None), ("it_goes_on_forever", None), ("it_is_just_a_fun_puzzle", None), ("we_might_be_in_such_a_model", None), ("other", None)], "evaluative")
C("If you could move into a fresh new body whenever your old one aged but kept your mind, would you do it?",
  [("yes", None), ("only_when_the_old_one_fails", None), ("no", None), ("not_sure", None)], "values")
C("If two people had their memories fully merged into one mind, who would the merged person be?",
  [("both_of_them", None), ("neither", None), ("whoever_had_the_stronger_personality", None), ("a_brand_new_person", None), ("not_sure", None)], "evaluative")
C("A robot built to look and speak exactly like you replaces you at work without anyone noticing. What would bother you most?",
  [("being_so_replaceable", None), ("the_deception", None), ("losing_the_income", None), ("nothing", None), ("other", None)], "personality")
C("A drug lets you feel what your pet feels for an hour. What would you most expect to learn?",
  [("it_loves_me", None), ("it_is_often_bored", None), ("its_senses_are_richer", None), ("it_worries_more_than_i_thought", None), ("not_sure", None)], "evaluative")

S("A copy of you is made every night while you sleep, and the old version is quietly removed. How would learning this change how you feel about going to sleep?",
  ["Sleep would terrify me from then on", "I would dread going to sleep", "I would feel uneasy but still sleep", "I would feel a passing strangeness only", "It would not bother me at all"], "personality")
S("A friend tells you they have a perfect memory implant that records everything they see. How comfortable would you be around them?",
  ["I would avoid them", "I would be guarded around them", "I would be mildly careful about what I say", "I would be relaxed but aware of it", "I would not mind at all"], "social")
S("You are offered a guarantee that a perfect copy of you will live on after your death. How much comfort would that give you?",
  ["None; I would still die", "A little, as a kind of legacy", "Some, mostly for my family's sake", "A lot; much of me would continue", "Complete comfort; I would not really die"], "values")
S("A game lets you live a full simulated lifetime in a single night of sleep. How would you treat the people you met in it?",
  ["As props that do not matter", "As characters I might enjoy", "As real enough to be polite to", "As people who deserve my honesty", "As fully real people"], "values")
S("If you could see a perfect recording of your whole childhood, how would you use it?",
  ["I would never watch it", "I would watch a few moments and stop", "I would look up key events to check my memories", "I would watch large parts of it", "I would watch all of it"], "personality")
S("Imagine someone proves that time does not really flow and that past, present, and future all exist equally. How would that change your view of your own life?",
  ["It would unsettle me deeply", "It would make me feel a little strange", "It would interest me but change nothing", "It would comfort me that the past still exists", "It would change how I think about death and loss"], "personality")
S("You can choose to have a gentle, invisible guide whisper the wisest choice to you in every decision. How often would you follow it?",
  ["I would refuse the guide entirely", "I would listen but rarely follow", "I would follow it on big decisions only", "I would follow it most of the time", "I would follow it every time"], "values")
S("If you could erase the memory of your favourite film so you could watch it fresh, how would you feel about doing that?",
  ["I would never erase it; the memory is precious", "I would be reluctant", "I would consider it", "I would do it gladly", "I would do it for many films"], "personality")
S("Suppose everyone you know agreed to live inside the same perfect simulation. How would you respond?",
  ["I would stay outside alone", "I would stay out and try to bring them back", "I would visit but not stay", "I would join them after a while", "I would join them right away"], "social")
S("If you could perfectly understand every word of every language instantly, how different would your life be?",
  ["I would carry on exactly as I do now", "I would enjoy more foreign films and books but otherwise live the same", "I would travel much more and make friends abroad", "I would change careers to work across languages", "I would move abroad and rebuild my life around it"], "personality")
S("A mind-reading scanner shows that your good deeds were always done partly for praise. How would you view those deeds?",
  ["As worthless", "As much less good than I thought", "As still good, if a little less so", "As just as good; the help was real", "As good, and I would stop worrying about motives"], "values")
S("If you could live as a disembodied mind with no senses but full thought, how long would you choose to stay?",
  ["Not even a moment", "A few minutes, out of curiosity", "A few days", "A long time", "Forever"], "personality")
S("If a device showed that a person you love has an inner life very different from what you imagined, how would that affect your bond?",
  ["It would end the bond", "It would weaken it", "It would make things awkward for a while", "It would deepen it", "It would make me love them more"], "social")
S("You are told a person in a coma is fully aware but unable to move. How would that change the way you behave in their hospital room?",
  ["Not at all", "I would be a little more careful what I said", "I would talk to them sometimes", "I would talk to them often and gently", "I would treat them exactly as if they were awake"], "social")

N("If an exact copy of your favourite restaurant opened across the street, would it matter to you which one you ate at?", "evaluative")
N("If someone could make a perfect copy of your handwritten letters, would the copies mean as much to the people who received them?", "evaluative")
N("If it were proven that the past no longer exists in any sense, would your memories still count as knowledge?", "evaluative")
N("If a statue of you were built from your own recycled atoms after death, would it be you in any sense?", "evaluative")
N("If your mind were copied into a robot body while you were alive, would you want to meet it?", "personality")

dump('/Users/junzhang/Projects/askjev/scratchpad/phase6_mind1/thought_experiments.jsonl')
