import sys; sys.path.insert(0,'/Users/junzhang/Projects/askjev/scratchpad/phase6_mind1')
from lib import *
node("big_questions")

# ---------- Free will, determinism, responsibility ----------
C("When you make an ordinary choice, like what to eat for lunch, what do you think is really happening?",
  [("i_freely_choose","I could genuinely have picked anything"),
   ("causes_decide","prior causes settle it and I experience the result"),
   ("mix","some of each"),
   ("never_thought_about_it",None)], "values")
C("If every choice you make was fully caused by earlier events, what would that mean for your choices?",
  [("still_mine","they would still be my choices because they flow from me"),
   ("not_really_mine","they would not really be mine"),
   ("partly_mine",None),
   ("question_makes_no_sense",None)], "values")
C("What would be the biggest thing lost if free will did not exist?",
  ["moral_blame","pride_in_achievement","sense_of_control","meaning_of_effort","romantic_love","nothing_important"], "values")
C("Which best describes the feeling you have when you make a hard decision?",
  [("genuinely_open","it feels like the future is genuinely open"),
   ("discovering_myself","it feels like discovering what I was always going to do"),
   ("being_pushed","it feels like being pushed by forces I don't control"),
   ("no_particular_feeling",None)], "personality")
C("What most limits how free a person really is?",
  ["genes","upbringing","money","culture","brain_chemistry","chance_events","nothing_much"], "values")
C("Where do you think your desires ultimately come from?",
  [("i_choose_them",None),("my_biology",None),("my_upbringing",None),("my_culture",None),("a_mix_of_all",None),("no_idea",None)], "values")
C("If a scientist could predict every decision you will make, what would you conclude?",
  [("no_free_will","I never had free will"),
   ("free_will_intact","I'd still be free, just predictable"),
   ("predictor_must_be_wrong","the prediction must be flawed somewhere"),
   ("unsure",None)], "values")
C("What is the main reason people hold on to the idea of free will?",
  [("it_feels_true","it matches how choosing feels"),
   ("needed_for_blame","society needs it to hold people responsible"),
   ("it_is_true","because it is actually true"),
   ("comfort","it is comforting"),
   ("never_questioned","they have never questioned it")], "social")
C("Which kind of freedom matters most to you?",
  [("freedom_from_control","not being controlled by others"),
   ("freedom_of_will","being the ultimate source of my choices"),
   ("freedom_to_act","being able to do what I want"),
   ("inner_freedom","not being ruled by my impulses")], "values")
C("If someone commits harm because of a brain tumor that changed their behavior, how responsible are they?",
  [("fully",None),("partly",None),("not_at_all",None),("depends_on_the_details",None)], "values")
C("What should punishment mainly be for, if free will is doubtful?",
  ["protecting_others","rehabilitation","deterring_others","expressing_disapproval","deserved_suffering","no_punishment_at_all"], "values")
C("Which best describes how you think about your own past mistakes?",
  [("could_have_done_otherwise","I really could have done otherwise"),
   ("did_what_i_could","I did what the person I was then could do"),
   ("mostly_bad_luck",None),
   ("i_do_not_dwell",None)], "personality")
C("Which is more real to you: the laws of physics or your ability to choose?",
  ["laws_of_physics","ability_to_choose","both_equally","neither_is_what_it_seems"], "values")
C("When you picture the next moment of the universe, which feels right?",
  [("already_fixed","it is already fixed by the present"),
   ("genuinely_random","parts of it are genuinely random"),
   ("partly_up_to_us","part of it is up to choosing beings"),
   ("cannot_say",None)], "values")
C("If randomness exists in physics, what does it do for free will?",
  [("helps","it makes room for free will"),
   ("does_not_help","random is not the same as free"),
   ("irrelevant",None),
   ("unsure",None)], "values")

S("How much does the question of free will affect how you judge other people?",
  ["I never think about free will when judging anyone",
   "I occasionally remember that people's choices have causes, but it rarely changes my judgment",
   "I often soften my judgment because I think about what shaped the person",
   "I find it hard to blame anyone because I see behavior as caused by things they didn't pick"], "values")
S("How often do you catch yourself wondering whether you could have chosen differently?",
  ["I never wonder about that",
   "It crosses my mind after big decisions only",
   "I wonder about it every few weeks",
   "It is something I think about nearly every day"], "personality")
S("How strongly do you feel you are the author of your own life?",
  ["I feel my life simply happens to me",
   "I steer small things but big things are out of my hands",
   "I shape most of my life within the limits I was given",
   "I feel I have written my own life almost entirely"], "values")
S("How much credit do you think a successful person deserves for their success?",
  ["None: it all came from luck, genes, and circumstance",
   "A little: effort mattered, but luck mattered far more",
   "About half: effort and luck were equal partners",
   "Most of it: their effort and choices did the heavy lifting",
   "All of it: they earned every bit"], "values")
S("How would you feel if science proved all your decisions were determined in advance?",
  ["It would not bother me at all and I would live the same way",
   "I would find it interesting but not upsetting",
   "I would feel uneasy for a while",
   "It would shake how I see myself for a long time",
   "It would feel devastating, like my life was a script"], "personality")
S("How much should people forgive themselves for who they were before they knew better?",
  ["Not at all: ignorance is no excuse",
   "A little, while still carrying real guilt",
   "Mostly, as long as they now act differently",
   "Completely: nobody should blame a past self for what it didn't know"], "values")
S("When you resist a temptation, how much of that do you credit to yourself?",
  ["None: some mood or circumstance happened to win out",
   "A little: circumstances mostly decided it",
   "A lot: I made a real effort of will",
   "All of it: it was purely my own choice"], "personality")

N("Do you believe you could have made a different choice in a situation where you actually chose one thing?", "values")
N("Would you still feel proud of your achievements if free will turned out not to exist?", "values")
N("Do you think it is fair to punish someone for something they could not have avoided doing?", "values")
N("Do you think the future is already settled?", "values")
N("Does believing in free will make people behave better?", "social")
N("Do you think animals make free choices?", "values")
N("Do you think moral responsibility can exist even if everything is determined?", "values")
N("Have you ever changed your behavior after thinking about whether free will is real?", "personality")
N("Do you think people deserve gratitude for kindness that came naturally to them?", "values")
N("Is willpower something a person can take credit for?", "values")

# ---------- Meaning, purpose, absurdity ----------
C("What most often makes your life feel meaningful on an ordinary day?",
  ["relationships","work","learning","helping_someone","creating_something","small_pleasures","nothing_does"], "values")
C("What is the best response to realizing life might have no built-in meaning?",
  [("make_my_own","create my own meaning"),
   ("enjoy_it_anyway","enjoy life without needing meaning"),
   ("keep_searching","keep looking for a meaning that is out there"),
   ("despair",None),
   ("ignore_the_question",None)], "values")
C("Which kind of life seems most meaningful to you?",
  ["devoted_to_family","devoted_to_a_craft","devoted_to_helping_strangers","devoted_to_discovery","devoted_to_adventure","quiet_and_contented"], "values")
C("Can a life be meaningful if it involves doing the same simple task every day?",
  [("yes_if_chosen","yes, if the person embraces it"),
   ("yes_always",None),
   ("only_if_it_helps_others",None),
   ("no",None)], "values")
C("Does meaning come more from what you do or from who you are?",
  ["what_i_do","who_i_am","who_i_love","what_i_leave_behind","none_of_these"], "values")
C("Which threatens the meaning of a life most?",
  ["loneliness","boredom","pointless_suffering","being_forgotten","wasted_talent","nothing_can_threaten_it"], "values")
C("If you learned for certain that humanity will someday vanish without a trace, how would that affect your sense of meaning?",
  [("no_effect","it wouldn't change anything for me"),
   ("more_precious","life would feel more precious"),
   ("somewhat_emptier",None),
   ("everything_pointless","everything would feel pointless")], "values")
C("Can someone else give your life meaning?",
  ["yes_mostly","yes_partly","no_only_i_can","meaning_is_not_given"], "values")
C("Which best describes the idea that life is absurd?",
  [("true_and_funny","true, and that is freeing or funny"),
   ("true_and_sad","true, and that is sad"),
   ("false","life makes sense"),
   ("meaningless_question",None)], "values")
C("Where would you look first if you felt your life had lost its meaning?",
  ["friends_and_family","new_work_or_project","nature","art_or_books","helping_others","philosophy","time_alone"], "personality")
C("What gives a single moment the most meaning?",
  ["sharing_it","remembering_it","understanding_it","its_beauty","its_rarity","nothing_special"], "values")
C("Is a meaningful life the same thing as a good life?",
  [("same",None),("meaning_is_part_of_goodness",None),("different_things",None),("unsure",None)], "values")
C("Which statement about purpose fits you best?",
  [("have_clear_purpose","I have a clear purpose I'm living for"),
   ("purpose_is_forming","I'm still working mine out"),
   ("many_small_purposes","I have many small purposes, not one big one"),
   ("dont_need_one","I don't need a purpose")], "personality")
C("Could a life spent entirely in pleasure be meaningless?",
  ["yes","no","only_if_it_harmed_others","not_sure"], "values")
C("Which do you think is more meaningful: a short life of great impact or a long quiet life?",
  ["short_great_impact","long_quiet_life","equally_meaningful","depends_on_the_person"], "values")
C("Does the meaning of your life depend on what happens after you are gone?",
  [("yes_legacy_matters",None),("partly",None),("no_it_is_complete_as_lived",None),("never_considered_it",None)], "values")
C("What role does struggle play in a meaningful life?",
  [("essential","essential: no struggle, no meaning"),
   ("helpful",None),
   ("irrelevant",None),
   ("gets_in_the_way",None)], "values")

S("How meaningful does your life feel to you right now?",
  ["It feels empty and pointless most days",
   "It feels meaningful only now and then",
   "It feels meaningful on most days, with some flat stretches",
   "It feels deeply meaningful nearly all the time"], "evaluative")
S("How much do you need a big reason to get out of bed in the morning?",
  ["I get up without thinking about reasons at all",
   "Small things like coffee or a routine are enough reason",
   "I need something I'm working toward to feel motivated",
   "Without a larger purpose I struggle to get going"], "personality")
S("How absurd does ordinary human life look to you when you step back?",
  ["It never looks absurd; everything people do makes sense",
   "Occasionally a routine strikes me as odd, then the feeling passes",
   "I regularly notice how strange and arbitrary daily life is",
   "Most of what people do looks absurd to me when I step back"], "values")
S("How much would your sense of meaning suffer if no one ever knew what you accomplished?",
  ["Not at all: I do things for their own sake",
   "A little: I'd miss sharing it but still feel satisfied",
   "A lot: recognition is a big part of why I do things",
   "Completely: an unseen achievement would feel worthless"], "values")
S("How often do you feel your daily activities connect to something larger than yourself?",
  ["Never: my days are just my days",
   "Rarely, maybe on special occasions",
   "Fairly often, when I'm helping or creating",
   "Almost always: I see most of what I do as part of something bigger"], "evaluative")
S("How settled are you on what the purpose of your life is?",
  ["I have no idea and it doesn't bother me",
   "I have no idea and it bothers me",
   "I have a rough idea that keeps shifting",
   "I have a clear sense of purpose I rarely question"], "personality")
S("How much do you think a person's life can matter in the long run of history?",
  ["Not at all: every life is soon forgotten",
   "Only a few famous lives matter in the long run",
   "Ordinary lives matter through the small ripples they leave",
   "Every life shapes the future in lasting ways"], "values")

N("Do you think a meaningful life requires making a difference to other people?", "values")
N("Would you choose a meaningful but hard life over an easy but meaningless one?", "values")
N("Do you think meaning can be found in suffering itself?", "values")
N("Have you ever felt that life was completely pointless?", "personality")
N("Do you think the question 'what is the meaning of life?' has an answer?", "values")
N("Could a person who has done nothing noteworthy still have lived a meaningful life?", "values")
N("Do you think meaning is the same for everyone?", "values")
N("Would you want to know the purpose of your life if someone could tell you?", "values")
N("Is it possible to find meaning in a job you dislike?", "values")

# ---------- Human nature ----------
C("When a stranger drops their wallet in a busy street, what do you expect most people nearby to do?",
  ["return_it_intact","return_it_minus_cash","ignore_it","keep_it","not_sure"], "social")
C("What mainly drives people when nobody is watching?",
  ["self_interest","habit","conscience","fear_of_being_found_out","kindness","depends_on_the_person"], "social")
C("Which is the deepest root of human cruelty?",
  ["fear","ignorance","group_loyalty","greed","boredom","pain_passed_on","it_is_innate"], "values")
C("Which is the most human invention of all?",
  ["language","music","storytelling","laughter","promises","tools","none_stand_out"], "values")
C("If all laws disappeared tomorrow, what do you think most people would do?",
  [("carry_on_decently","mostly carry on as before"),
   ("chaos","society would fall into chaos"),
   ("form_new_rules","quickly create new rules"),
   ("depends_on_place",None)], "social")
C("What mostly holds large groups of strangers together?",
  ["shared_stories","laws","trade","shared_enemies","kindness","habit"], "social")
C("What best explains why ordinary people sometimes do terrible things?",
  [("obeying_authority",None),("peer_pressure",None),("desperation",None),("hidden_bad_character",None),("gradual_steps","small steps that add up"),("not_sure",None)], "social")
C("Is envy a natural part of being human or something learned?",
  ["natural","learned","both","not_sure"], "values")
C("Which trait is most universal among humans?",
  ["curiosity","fear","love_of_family","self_interest","desire_for_status","need_to_belong","storytelling"], "values")
C("If you could remove one feature of human nature, which would you remove?",
  ["greed","jealousy","tribalism","cruelty","vanity","laziness","none"], "values")
C("What do you think people are most afraid of, deep down?",
  ["death","being_alone","being_unimportant","losing_control","failure","being_seen_as_they_are"], "social")
C("Are heroes and villains different kinds of people, or the same kind in different situations?",
  ["different_kinds","same_kind_different_situations","a_bit_of_both","not_sure"], "values")
C("Which best describes what is under the surface of most people?",
  [("mostly_good",None),("mostly_selfish",None),("mostly_frightened",None),("mixed",None),("it_varies_too_much_to_say",None)], "social")
C("What do you think humans value most, judging by how they actually live?",
  ["comfort","status","family","safety","pleasure","truth","belonging"], "social")

S("How much do you trust the goodness of people you have never met?",
  ["I assume strangers will take advantage of me if they can",
   "I stay guarded with strangers until they prove themselves",
   "I give strangers the benefit of the doubt in most cases",
   "I assume nearly every stranger means well"], "social")
S("How often do you think people act against their own interest for a principle?",
  ["Never: it only looks that way",
   "Rarely, in a few famous cases",
   "Fairly often, in quiet everyday ways",
   "Constantly: principles drive people more than interest"], "social")
S("How easily do you think a decent person could be led into doing something cruel?",
  ["It would never happen; decent people stay decent",
   "Only under extreme threat to their life",
   "Under strong pressure from authority or a group, quite easily",
   "With the right small steps, almost anyone could be led there"], "values")
S("How much do you think old age makes people wiser rather than just older?",
  ["Not at all: people just get more set in their ways",
   "A little, in a few practical matters",
   "Noticeably, for most people who reflect on their lives",
   "Greatly: age reliably brings deep wisdom"], "social")
S("How much do you think people are shaped by the era they are born into?",
  ["Hardly at all: people are the same in every era",
   "Their tastes differ but their character is timeless",
   "Their values and habits are largely set by their era",
   "Almost everything about them comes from their era"], "values")
S("How often do you see real altruism in everyday life?",
  ["Never: there is always an angle",
   "Rarely, maybe a few times in my life",
   "Regularly, in small acts from people around me",
   "Constantly, everywhere I look"], "social")

N("Do you think humans are the only animals capable of real cruelty?", "values")
N("Do you think people would be kinder if they had everything they needed?", "social")
N("Do you believe every person has some good in them?", "values")
N("Do you think humans are naturally violent?", "values")
N("Do you think people are more alike than different?", "values")
N("Would most people steal if they were certain they would never be caught?", "social")
N("Do you think human nature is the same in every culture?", "values")

# ---------- Alone in the universe / aliens ----------
C("If we found out we are truly alone in the universe, how would you feel?",
  ["lonely","special","frightened","indifferent","responsible","disappointed"], "personality")
C("If intelligent aliens exist, what would they most likely be like?",
  [("friendly",None),("hostile",None),("indifferent_to_us",None),("incomprehensible",None),("much_like_us",None)], "values")
C("What would be the most important effect of discovering alien life?",
  ["humility","unity_among_humans","fear","new_science","change_in_meaning_of_life","little_real_effect"], "values")
C("What kind of alien life would you expect us to find first, if any?",
  ["microbes","plants_or_simple_life","animals","intelligent_beings","machines_they_built","none_ever"], "values")
C("Should humans try to announce themselves to possible alien civilizations?",
  [("yes",None),("no_too_risky",None),("only_after_listening_longer",None),("doesnt_matter",None)], "values")
C("If an alien civilization contacted us, who should reply for humanity?",
  ["scientists","world_leaders","a_global_vote","artists_and_thinkers","nobody_should_reply"], "values")
C("Which would change your view of humanity more?",
  ["finding_alien_microbes","finding_alien_ruins","receiving_an_alien_message","proving_no_one_is_out_there"], "values")

S("How much do you think about whether humans are alone in the universe?",
  ["I never think about it",
   "It comes up only when I see something in the news",
   "I wonder about it when I look at the night sky",
   "It is a question I return to often and care about deeply"], "personality")
S("How would finding alien intelligence change how you see human importance?",
  ["It would not change anything about how I see us",
   "It would make us feel a little less central",
   "It would make me see humans as one small voice among many",
   "It would completely overturn my sense of our place"], "values")
S("How ready do you think humanity is to learn it is not alone?",
  ["We would panic and fall apart",
   "We would be shaken and divided for a long time",
   "We would adjust after an initial shock",
   "We would take it calmly and with curiosity"], "social")

N("Would you want to be among the first people to meet an alien species?", "personality")
N("Would it matter to you if alien life turned out to be only microbes?", "values")
N("Do you think intelligent aliens would share some of our morals?", "values")
N("If you had to choose, would you rather humanity be alone than share the universe with a hostile species?", "values")
N("Would the discovery of alien life make you feel more hopeful?", "personality")

# ---------- Reality and appearance ----------
C("Which do you think is most real?",
  ["physical_matter","minds","information","mathematical_structure","experiences","cannot_be_known"], "values")
C("What is color really?",
  [("property_of_objects","a property of the objects themselves"),
   ("in_the_mind","something the mind adds"),
   ("relationship","a relationship between light, objects, and eyes"),
   ("not_sure",None)], "values")
C("If nobody were around to see it, would a sunset still be beautiful?",
  ["yes","no","it_would_have_the_potential","question_makes_no_sense"], "values")
C("What is the world like when no one is perceiving it?",
  [("same_as_we_see_it",None),("very_different_from_how_it_looks",None),("unknowable",None),("it_does_not_exist_unperceived",None)], "values")
C("Which is more fundamental: objects or the events that happen to them?",
  ["objects","events","both_equally","neither","no_opinion"], "values")
C("Which comes closest to your view of what dreams tell us about reality?",
  [("nothing","nothing: dreams are just noise"),
   ("waking_could_be_similar","waking life could be just as unreal"),
   ("mind_builds_reality","the mind builds much of what we experience"),
   ("hidden_truths","dreams reveal hidden truths")], "values")
C("Is there a deeper reality behind the everyday world of tables and chairs?",
  ["yes_physics_describes_it","yes_but_physics_misses_it","no_this_is_it","unsure"], "values")
C("What do you think physics ultimately describes?",
  [("reality_itself",None),("useful_models",None),("patterns_in_our_observations",None),("part_of_reality_only",None),("not_sure",None)], "values")
C("Which feels more real to you from moment to moment?",
  ["the_outside_world","my_thoughts","my_feelings","my_body","my_relationships"], "personality")

S("How closely do you think the world as you see it matches the world as it really is?",
  ["It matches perfectly; things are exactly as they look",
   "It matches closely, with small distortions",
   "It matches loosely; our senses simplify a lot",
   "It barely matches; we see a useful fiction"], "values")
S("How often do you question whether ordinary reality is what it appears to be?",
  ["Never: I take the world at face value",
   "Only after a strange experience or a weird movie",
   "Every so often, when something makes me stop and think",
   "Regularly: it is a background question in my mind"], "personality")
S("How much of your everyday experience do you think your brain fills in rather than takes in?",
  ["None: I take in the world directly",
   "A little: some details are guessed",
   "A lot: much of what I see is my brain's best guess",
   "Nearly all of it: experience is mostly constructed"], "values")

N("Do you think the world would still exist if every mind disappeared?", "values")
N("Do you think there are parts of reality that humans can never perceive?", "values")
N("Do you believe things have a true nature beyond how they appear to us?", "values")
N("Has a single experience ever made you doubt that the world is what it seems?", "personality")
N("Do you think empty space is really nothing?", "values")

# ---------- Existence, cosmos, significance ----------
C("How do you react to the question of why there is something rather than nothing?",
  [("fascinated","it fascinates me"),("dizzy","it makes me dizzy or uneasy"),("pointless_question","it seems like a pointless question"),("science_will_answer","science will answer it eventually"),("never_considered",None)], "personality")
C("Did the universe have a beginning?",
  ["yes","no_it_always_existed","it_goes_in_cycles","the_question_does_not_apply","no_idea"], "values")
C("Will the universe have an end?",
  ["yes","no","it_will_start_over","no_idea"], "values")
C("Is the existence of the universe a brute fact or does it need an explanation?",
  [("brute_fact","it just is, with no further explanation"),("needs_explanation",None),("explanation_exists_but_unknowable",None),("not_sure",None)], "values")
C("Which image best matches how you picture the universe?",
  ["a_machine","an_ocean","a_story","a_living_thing","an_empty_stage","a_puzzle"], "values")
C("Could there be other universes besides ours?",
  ["very_likely","possible","unlikely","impossible","meaningless_question"], "values")
C("If there are countless other universes, what does that do to the importance of this one?",
  [("no_change",None),("makes_ours_less_special",None),("makes_ours_more_special",None),("makes_me_curious",None)], "values")
C("Is the universe the kind of thing that can be fully explained?",
  ["yes_in_principle","mostly","only_partly","no"], "values")
C("What best describes the fact that the universe allows life to exist at all?",
  [("lucky_accident",None),("inevitable",None),("one_of_many_tries","one of many universes, so not surprising"),("needs_deeper_explanation",None),("not_sure",None)], "values")
C("Which is the more astonishing fact?",
  ["that_anything_exists","that_life_exists","that_minds_exist","that_the_universe_is_understandable"], "values")
C("Which view about cosmic significance fits you best?",
  [("humans_matter_to_universe","humans matter to the universe itself"),
   ("humans_matter_to_each_other","we matter only to each other"),
   ("nothing_matters",None),
   ("everything_matters_equally",None)], "values")

S("How often do you think about the size and age of the universe?",
  ["Never: it doesn't cross my mind",
   "Only when something like a space photo prompts me",
   "Now and then on my own, when I'm outside at night or thinking quietly",
   "Often: it is a regular part of how I think about life"], "personality")
S("How much comfort do you take from being part of a vast universe?",
  ["None: vastness makes me feel lost",
   "Very little: I mostly find it neutral",
   "Some: it puts my worries in perspective",
   "A great deal: it makes me feel connected to everything"], "personality")
S("How much does the idea of infinity unsettle you?",
  ["Not at all: it's just a word",
   "It puzzles me briefly and then I move on",
   "It makes my head spin whenever I think about it",
   "It genuinely disturbs me"], "personality")

N("Do you find it strange that anything exists at all?", "personality")
N("Do you think the universe would be worse off without humans in it?", "values")
N("Do you think the universe is in some sense aware of itself through us?", "values")
N("Would you want to know how the universe will end, even if it is bleak?", "personality")
N("Do you think nothingness is even possible?", "values")

# ---------- Objective value, beauty, truth ----------
C("Is beauty in the eye of the beholder?",
  [("entirely",None),("mostly",None),("partly_objective",None),("mostly_objective",None),("entirely_objective",None)], "values")
C("If everyone on Earth disliked a piece of music, could it still be good?",
  ["yes","no","maybe","depends_on_why"], "values")
C("Which is more valuable in a life: depth or breadth?",
  [("depth","going deep into a few things"),("breadth","trying many different things"),("equal",None),("depends_on_person",None)], "values")
C("Which is the most solid foundation for right and wrong?",
  ["human_wellbeing","reason","feelings_of_compassion","social_agreement","nature","there_is_none"], "values")
C("Is truth something that exists independently of what people think?",
  ["yes_always","for_facts_not_values","no_truth_is_agreement","not_sure"], "values")
C("When two cultures disagree about a moral practice, what best describes the situation?",
  [("one_is_right",None),("both_right_for_themselves",None),("both_wrong",None),("no_fact_of_the_matter",None),("depends_on_the_practice",None)], "values")
C("Where does value in the world come from?",
  ["from_minds_that_care","from_nature","from_reason","from_society","it_is_built_in","nowhere"], "values")
C("Is anything worth doing for its own sake?",
  ["pleasure","knowledge","love","beauty","virtue","nothing","many_things"], "values")
C("Which is most likely to be objectively valuable, if anything is?",
  ["happiness","knowledge","love","beauty","freedom","life_itself","none"], "values")
C("If a moral truth were discovered that you found repugnant, what would you do?",
  [("accept_it",None),("reject_it_anyway",None),("suspect_a_mistake",None),("feel_torn",None)], "values")

S("How objective do you think the difference between good and bad art is?",
  ["Completely subjective: it's all personal taste",
   "Mostly taste, though skill counts for something",
   "Some works really are better, though taste matters a lot",
   "Quality in art is as real as quality in engineering"], "values")
S("How much do you think your own values would hold up if you had been born in a very different culture?",
  ["I'd have completely different values",
   "I'd share only a few of my current values",
   "Most of my core values would be the same",
   "My values would be exactly the same wherever I was born"], "values")
S("How sure are you that cruelty for fun is wrong everywhere and always?",
  ["I think it's only wrong if a society says so",
   "I think it's wrong in most societies but not universally",
   "I'm fairly sure it's wrong everywhere, with some doubt",
   "I'm completely sure it's wrong everywhere and always"], "values")

N("Do you believe some things are good whether or not anyone thinks they are?", "values")
N("Would the world still contain value if no living things existed?", "values")
N("Do you think a mathematical proof can be beautiful?", "values")
N("Do you think nature is beautiful in a way that doesn't depend on humans?", "values")
N("Is it possible for a whole society to be morally mistaken?", "values")

# ---------- Mathematics and logic ----------
C("Is mathematics discovered or invented?",
  ["discovered","invented","some_of_each","neither","no_opinion"], "values")
C("Why do you think mathematics describes the physical world so well?",
  [("world_is_mathematical","the world is mathematical at its core"),
   ("we_built_it_to_fit","we built mathematics to fit the world"),
   ("we_only_notice_what_fits",None),
   ("a_mystery",None)], "values")
C("Would aliens have the same mathematics as us?",
  ["same_truths","different_math","same_truths_different_notation","no_idea"], "values")
C("Could the laws of logic have been different?",
  ["yes","no","question_makes_no_sense","unsure"], "values")

S("How real do mathematical objects like circles and triangles seem to you?",
  ["Not real at all: they are just human ideas",
   "Useful fictions that help us describe things",
   "Real patterns that exist in nature",
   "As real as anything, existing whether we think of them or not"], "values")

N("Would the truths of arithmetic still hold if no minds existed?", "values")
N("Do you think there are mathematical truths that can never be proven?", "values")

# ---------- Progress and the fate of humanity ----------
C("What is the greatest achievement of humanity so far?",
  ["science","art","medicine","language","moral_progress","exploration","cooperation_at_scale"], "values")
C("What will people in the far future most likely think of us?",
  [("primitive",None),("cruel",None),("brave_pioneers",None),("much_like_themselves",None),("won_t_think_of_us",None)], "values")
C("What is the greatest threat to humanity's long-term future?",
  ["our_own_weapons","environmental_collapse","disease","loss_of_meaning","cosmic_disaster","division_among_ourselves","none_is_serious"], "values")
C("What will be humanity's ultimate fate?",
  ["spread_among_the_stars","go_extinct","become_something_new","stay_much_the_same","no_idea"], "values")
C("If humanity could become something beyond human, should it?",
  ["yes","no","only_gradually","not_sure"], "values")
C("Which kind of progress matters most?",
  ["moral","scientific","technological","artistic","personal","none_is_real"], "values")
C("Which common practice today do you think future people will look back on with horror?",
  [("how_we_treat_animals",None),("how_we_treat_the_old",None),("how_we_use_the_planet",None),("how_we_spend_attention",None),("how_we_treat_prisoners",None),("none",None)], "values")
C("Should humanity try to live forever as a species, no matter what?",
  ["yes","no","only_if_worth_it","irrelevant"], "values")
C("What gives you the most hope about humanity?",
  ["kindness_of_strangers","young_people","science","art","how_far_we_ve_come","nothing"], "personality")
C("What would most surprise a visitor from the distant past about life today?",
  ["how_long_people_live","how_alone_people_are","how_much_people_know","how_little_people_are_satisfied","how_much_is_the_same"], "social")
C("If humanity could only pass one thing on to whatever comes after us, what should it be?",
  ["knowledge","art","moral_lessons","our_story","our_genes","nothing"], "values")

S("How much do you think humans today are wiser than humans long ago?",
  ["We are less wise than our ancestors",
   "We know more facts but are no wiser",
   "We are somewhat wiser thanks to accumulated experience",
   "We are far wiser in almost every way"], "values")
S("How responsible do you feel for people who will live long after you?",
  ["Not at all: they will have to handle their own world",
   "A little: I try not to leave a mess",
   "A lot: I think about them when making choices",
   "Deeply: their fate shapes much of what I do"], "values")
S("How likely do you think it is that humanity will still exist in the very far future?",
  ["I expect humanity to be gone long before then",
   "I think survival is possible but unlikely",
   "I think survival is likely but not certain",
   "I'm confident humanity will still be around"], "values")
S("How much does the far future of humanity figure into your everyday thoughts?",
  ["It never comes up in my thoughts",
   "It comes up when I read about big risks",
   "I think about it several times a month",
   "It is one of the main things I think about"], "personality")

N("Do you think humanity will eventually outgrow war?", "values")
N("Is it important to you that humanity continues after you die?", "values")
N("Do you think humans are the most important thing that has happened on Earth?", "values")
N("Would humanity be better off if it grew more slowly and carefully?", "values")
N("Would you trade places with someone living in a distant future you know nothing about?", "personality")
N("Do you think future generations matter as much as people alive today?", "values")

# ---------- Personal identity over a life ----------
C("Which part of you would have to change for you to become a different person?",
  ["memories","personality","values","body","relationships","nothing_could_do_it"], "values")
C("Is the child you once were the same person as you now?",
  [("yes_same_person",None),("same_person_changed",None),("a_different_person",None),("no_clear_answer",None)], "values")
C("Is there a stable 'self' underneath all your changing thoughts and moods?",
  ["yes","no_just_a_stream","partly","not_sure"], "values")
C("What do you think most makes you who you are?",
  ["my_choices","my_memories","my_relationships","my_body","my_values","my_story_about_myself"], "values")
C("Should people be held to promises they made as very different younger selves?",
  ["always","usually","only_minor_ones","rarely","never"], "values")

S("How connected do you feel to the person you were as a young child?",
  ["That child feels like a stranger to me",
   "I remember that child but feel little connection",
   "I feel clearly connected, though much has changed",
   "I feel I am essentially the same person I was then"], "personality")
S("How much do you think your future self is really you?",
  ["My future self feels like a different person I owe nothing",
   "My future self is partly me, partly someone else",
   "My future self is mostly me, just older",
   "My future self is fully me and I plan for them as myself"], "values")
S("How much of your identity comes from your own choices rather than things given to you?",
  ["Almost none: I am mostly what I was handed",
   "Some: a few key choices shaped me",
   "Much: my choices have shaped most of who I am",
   "Nearly all: I built myself on purpose"], "values")
S("How fixed does your sense of self feel from day to day?",
  ["It shifts so much I barely know who I am",
   "It wobbles noticeably depending on mood and company",
   "It is mostly steady with occasional shifts",
   "It feels rock solid every single day"], "personality")
S("How much would you still be yourself if you lost all your beliefs and values?",
  ["I'd be completely myself; beliefs are just clothing",
   "I'd be mostly myself with a different outlook",
   "I'd be only partly myself",
   "I'd be someone else entirely"], "values")

N("Do you think you have a true self that you could discover?", "values")
N("Would you still be the same person if your personality changed completely?", "values")
N("Do you feel responsible for things you did many years ago?", "values")

# ---------- Time ----------
C("Which view of time feels closest to the truth?",
  [("only_now_is_real","only the present really exists"),
   ("all_times_real","past, present, and future are all equally real"),
   ("past_and_present","the past and present exist, the future doesn't yet"),
   ("time_is_illusion",None),
   ("no_idea",None)], "values")
C("Does time really flow, or does it only seem to?",
  ["really_flows","only_seems_to","not_sure","question_makes_no_sense"], "values")
C("Is the past still real in some sense, even though it is gone?",
  ["yes","no","only_in_memory","only_in_its_effects"], "values")
C("If time had no direction, what would be lost?",
  ["cause_and_effect","memory","growth","regret","hope","nothing"], "values")

S("How often do you feel that time itself is mysterious?",
  ["Never: time is just what clocks measure",
   "Rarely, maybe when a day flies by strangely fast",
   "Sometimes, when I stop to think about what time is",
   "Often: time is one of the strangest things I know"], "personality")
S("How real does the future feel to you right now?",
  ["The future feels like pure fiction",
   "The future feels like a vague possibility",
   "The future feels fairly concrete and predictable",
   "The future feels as solid as the present"], "personality")

N("Do you think it is possible, even in principle, to change the past?", "values")
N("Do you think time existed before the universe began?", "values")

# ---------- Good, evil, suffering ----------
C("What is evil?",
  [("a_real_force",None),("extreme_harm",None),("absence_of_empathy",None),("just_a_word_for_what_we_hate",None),("a_choice_people_make",None)], "values")
C("Why is there so much suffering in the world?",
  ["nature_is_indifferent","human_choices","scarcity","it_teaches_us","no_reason","a_mix"], "values")
C("If you could remove all suffering from the world but also remove all joy, would you?",
  ["yes","no","not_sure"], "values")
C("Is suffering ever good for the person who suffers?",
  [("often",None),("sometimes",None),("rarely",None),("never",None)], "values")
C("Which is harder to explain: the existence of evil or the existence of goodness?",
  ["evil","goodness","both_equally","neither"], "values")
C("Can a person be born evil?",
  ["yes","no","born_with_tendencies_only","not_sure"], "values")

S("How much of the world's suffering do you think is avoidable?",
  ["None: suffering is built into existence",
   "A small portion could be avoided with effort",
   "Much of it could be avoided if people cooperated",
   "Almost all of it comes from choices we could make differently"], "values")
S("How much does the scale of suffering in the world weigh on you day to day?",
  ["It doesn't weigh on me at all",
   "It crosses my mind when I see the news, then fades",
   "It weighs on me regularly and shapes some choices",
   "It weighs on me constantly and I struggle to set it aside"], "personality")
S("How balanced do you think good and evil are in the world?",
  ["Evil clearly outweighs good",
   "Evil slightly outweighs good",
   "Good slightly outweighs evil",
   "Good clearly outweighs evil"], "values")
S("How much do you believe that even the worst people can become good?",
  ["Not at all: some people are beyond change",
   "Very rarely, and only with extraordinary help",
   "Fairly often, if given a real chance",
   "Always: nobody is beyond redemption"], "values")

N("Do you think a world with less pain but less passion would be better?", "values")
N("Would a world with no suffering be a world without meaning?", "values")
N("Do you think good will eventually win out over evil in human history?", "values")

# ---------- Limits of understanding (big-picture) ----------
C("Which big question do you think science is most likely to answer eventually?",
  ["origin_of_life","origin_of_universe","nature_of_time","what_matter_ultimately_is","whether_we_are_alone","none_of_them"], "values")
C("Which big question do you think will never be answered?",
  ["why_anything_exists","what_happens_after_death","whether_we_have_free_will","what_time_is","meaning_of_life","all_can_be_answered"], "values")
C("Which would you rather humanity understand completely?",
  [("itself","the human mind"),("the_cosmos","the physical universe"),("life","how life works"),("morality","what is right"),("none","I'd keep the mysteries")], "values")
C("What does wonder mostly do for a person?",
  ["makes_them_humble","makes_them_curious","makes_them_happy","distracts_them","nothing_much"], "values")

S("How much do you think humans currently understand about how reality works?",
  ["Almost nothing: we are barely scratching the surface",
   "A small fraction, with huge gaps",
   "A good share of the basics, with key gaps",
   "Nearly everything important is already understood"], "values")
S("How much do you think every event has a cause?",
  ["Many events just happen, with no cause at all",
   "Most events have causes, but some don't",
   "Nearly all events have causes, with rare exceptions",
   "Every single event has a cause, without exception"], "values")

# ---------- Humans and nature ----------
C("Are humans part of nature or separate from it?",
  ["fully_part","partly_separate","fully_separate","not_sure"], "values")
C("What is the right relationship between humans and the rest of nature?",
  [("stewards",None),("equals",None),("masters",None),("guests",None),("just_another_species",None)], "values")
C("Is a city as natural as a forest?",
  ["yes","no","in_some_ways","not_sure"], "values")

S("How much do you think humans owe to the rest of life on Earth?",
  ["Nothing: other life exists for our use",
   "Little beyond avoiding needless waste",
   "A real duty to protect what we can",
   "Everything: we should put the living world before our own comfort"], "values")
S("How much do you think nature has something to teach us about how to live?",
  ["Nothing: nature is brutal and has no lessons for us",
   "Very little beyond practical survival",
   "A fair amount, if we pay attention",
   "Almost everything we need to know about living well"], "values")

N("Do you think humanity's rise was inevitable once life began on Earth?", "values")
N("Do you think the Earth has value apart from its usefulness to living things?", "values")

# ---------- Extra scores across themes ----------
S("How much do you think your character was up to you?",
  ["Not at all: it was fully set by genes and upbringing",
   "Slightly: I nudged it here and there",
   "Considerably: I worked on it and it changed",
   "Almost entirely: I chose who to become"], "values")
S("How much do you believe you are in control of your own thoughts?",
  ["Thoughts just pop into my head; I control none of them",
   "I can steer a few thoughts but most arrive unbidden",
   "I can direct most of my thinking when I try",
   "I decide what I think about nearly all the time"], "personality")
S("How much does the idea of an indifferent universe affect how you treat people?",
  ["It makes me care less, since nothing matters in the end",
   "It doesn't affect how I treat people",
   "It makes me a little kinder, since we only have each other",
   "It makes me much kinder, since caring is all that gives things weight"], "values")
S("How much do you think a life's worth can be judged by the person living it?",
  ["Not at all: people are poor judges of their own lives",
   "A little: others often see more clearly",
   "Mostly: the person usually knows best",
   "Completely: only the person living it can judge"], "values")
S("How much do you think ordinary kindness matters in the grand scheme of things?",
  ["Not at all: it's too small to matter",
   "A little: it makes a moment nicer",
   "A lot: it quietly holds society together",
   "Enormously: it is the most important thing people do"], "values")
S("How much do you enjoy thinking through arguments about existence you can never settle?",
  ["I find them a waste of time",
   "I tolerate them briefly when they come up",
   "I enjoy them now and then",
   "I love them and seek them out"], "personality")
S("How much do you think people's deepest beliefs about life are shaped by chance encounters?",
  ["Not at all: people reason their way to their beliefs",
   "A little: a chance book or friend nudges some people",
   "A lot: most people's worldview traces back to who they happened to meet",
   "Almost entirely: nobody would believe what they do without lucky accidents"], "social")
S("How much do you think humanity learns from its own history?",
  ["Nothing: we repeat the same mistakes forever",
   "Very little: lessons fade within a generation",
   "A fair amount, though slowly and unevenly",
   "A great deal: each age builds on the lessons of the last"], "social")
S("How much do you think people really understand their own reasons for acting?",
  ["Not at all: people invent reasons afterward",
   "A little: they know some reasons but miss the real drivers",
   "Fairly well, with occasional blind spots",
   "Very well: people usually know exactly why they act"], "social")
S("How much of your life do you think has been shaped by decisions you consciously made?",
  ["Almost none: things just happened to me",
   "A small part; most came from circumstances",
   "A large part, alongside plenty of circumstance",
   "Nearly all of it came from my deliberate decisions"], "evaluative")
S("How much do you think the lives of people long dead still matter?",
  ["They don't matter at all anymore",
   "They matter only through what they left behind",
   "They still matter in themselves, even if forgotten",
   "They matter as much as any life happening now"], "values")
S("How much do you think tiny, unnoticed acts ripple outward in the world?",
  ["Not at all: small acts vanish without a trace",
   "A little: they touch one or two people briefly",
   "A lot: they spread in ways we never see",
   "Endlessly: every small act changes the whole future"], "values")
S("How strongly do you feel that some things are sacred, in a non-religious sense?",
  ["Nothing is sacred to me",
   "A few things feel special but not sacred",
   "Some things, like human dignity, feel truly sacred",
   "Many things feel sacred and I treat them that way"], "values")
S("How much do you think a person's worth depends on what they do?",
  ["Not at all: every person has the same worth regardless",
   "A little: actions add to a basic worth everyone has",
   "A lot: worth is mostly earned through deeds",
   "Entirely: a person is worth exactly what they do"], "values")
S("How much do you think technology has changed what it means to be human?",
  ["Not at all: we are the same creatures with new tools",
   "A little: our habits changed but our core did not",
   "A lot: our attention and relationships work differently now",
   "Profoundly: we are becoming a different kind of being"], "values")
S("How much do you think a simple rule lies behind all of nature?",
  ["None: nature is a patchwork of unrelated facts",
   "Some areas share rules but there is no single one",
   "A few deep rules probably explain almost everything",
   "One simple rule will someday explain it all"], "values")
S("How much do you think love is part of the answer to what life is for?",
  ["Not at all: love is a pleasant side feature",
   "A little: it's one good among many",
   "A lot: it's among the main things that make life worthwhile",
   "Completely: love is what life is for"], "values")
S("How much do you think curiosity is part of human nature?",
  ["Barely: most people want comfort, not answers",
   "Somewhat in childhood, but it fades for most people",
   "It is strong in most people when given room",
   "It is the defining drive of our species"], "social")
S("How much would it change your life to be certain that nothing you do matters in the long run?",
  ["Not at all: I'd live exactly the same way",
   "A little: I might relax about small worries",
   "A lot: I'd rethink my goals and ambitions",
   "Completely: I would struggle to do anything at all"], "values")
S("How much does the idea that you exist by pure chance affect you?",
  ["It never crosses my mind",
   "I find it an interesting fact, nothing more",
   "It makes me feel lucky and grateful",
   "It overwhelms me when I really think about it"], "personality")
S("How much do you think people's sense of right and wrong is inborn?",
  ["Not at all: it is entirely taught",
   "A little: some basics like fairness may be inborn",
   "A lot: the core is inborn, culture adds detail",
   "Almost entirely: conscience comes built in"], "values")
S("How much do you think humans are still shaped by instincts from our distant past?",
  ["Not at all: culture has replaced instinct",
   "A little, in things like fear of snakes",
   "A lot, in how we love, fight, and form groups",
   "Almost entirely: we are ancient animals in modern clothes"], "values")
S("How much do you think a single person can change the course of history?",
  ["Not at all: history is moved by forces, not individuals",
   "Only a handful of people in all history ever did",
   "Quite a few people, at the right moment",
   "Anyone, given the right moment"], "values")
S("How much do you think people's happiness depends on believing life has meaning?",
  ["Not at all: happy people rarely think about meaning",
   "A little: it helps in hard times",
   "A lot: most people need some sense of meaning to be happy",
   "Completely: no one is truly happy without it"], "social")
S("How much do you talk with others about big questions of existence?",
  ["Never: those topics don't come up",
   "Only late at night or on rare occasions",
   "Every so often with a few close friends",
   "Regularly: it is a favorite topic of conversation"], "personality")
S("How much do you feel part of one shared human story?",
  ["Not at all: I just live my own life",
   "A little: I feel it at big events",
   "Quite a lot: I often feel connected to people across the world",
   "Deeply: I see my life as a thread in humanity's story"], "personality")
S("How much do you think nature, left alone, tends toward harmony?",
  ["Not at all: nature is endless struggle and cruelty",
   "Rarely: harmony is a brief pause between struggles",
   "Often: ecosystems find balance over time",
   "Always: nature is a finely balanced whole"], "values")
S("How much do you think new things can truly come into existence, rather than old things rearranged?",
  ["Nothing is ever new; everything is rearrangement",
   "Only new arrangements, never truly new stuff",
   "Genuinely new things like life and minds do emerge",
   "The universe constantly creates genuinely new things"], "values")
S("How much do you think people should question the way they were taught to see the world?",
  ["Not at all: tradition knows best",
   "Only when something clearly goes wrong",
   "Regularly, as part of growing up",
   "Constantly: nothing should be taken for granted"], "values")
S("How much would you want to live in a world where every mystery had been solved?",
  ["I would hate it; mystery is what makes life interesting",
   "I would find it a bit dull",
   "I would find it appealing, with some loss",
   "I would love it; knowing everything would be wonderful"], "personality")
S("How much do you think human life is a product of blind processes?",
  ["Not at all: life is clearly directed toward something",
   "Partly: blind processes set the stage but something more guides it",
   "Mostly: blind processes with a few open questions",
   "Entirely: we are the result of blind processes and nothing more"], "values")
S("How much do you think the world rewards good people?",
  ["Never: good people tend to lose out",
   "Rarely: goodness is its own reward at best",
   "Often, in the long run",
   "Almost always: goodness pays off"], "values")

# ---------- Extra choices and nouls ----------
C("Which word best captures what life is, at bottom?",
  ["a_gift","a_puzzle","a_game","a_struggle","an_accident","a_story","a_journey"], "values")
C("What would you most want to ask a being that knew all the answers?",
  ["why_anything_exists","what_life_is_for","what_happens_after_we_die","whether_we_are_free","what_is_really_real","nothing"], "values")
C("What is more important for humanity's future: wisdom or knowledge?",
  ["wisdom","knowledge","equally","neither"], "values")
C("What kind of creature is a human, at bottom?",
  ["a_clever_animal","a_social_animal","a_storytelling_animal","a_rational_being","a_spiritual_being","a_unique_puzzle"], "values")
C("Which is the strongest reason to keep living through hard times?",
  ["the_people_who_need_me","curiosity_about_what_comes_next","hope","duty","small_joys","no_single_reason"], "values")
C("If the universe is ultimately indifferent, what should people do?",
  ["care_for_each_other","enjoy_themselves","build_lasting_things","seek_understanding","accept_it_calmly","nothing_in_particular"], "values")

N("Do you think every person's life is equally important from the point of view of the universe?", "values")
N("Do you think humans will ever understand themselves completely?", "values")
N("Would you want to live in a universe where everything happens for a purpose?", "values")
N("Do you think a person can have more than one life purpose over a lifetime?", "values")
N("Do you believe ordinary people have hidden depths most never show?", "social")
N("Do you think the world is more mysterious than most people realize?", "values")

dump('/Users/junzhang/Projects/askjev/scratchpad/phase6_mind1/big_questions.jsonl')
