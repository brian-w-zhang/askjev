import sys
R={
'big_questions':{
"N|values|Do you think every person is creative in some way?":"S|values|How many people do you think are creative in some real way?|Almost nobody is truly creative ; Only a gifted few are creative ; Many people are creative ; Most people are creative ; Every single person is creative in some way",
"N|values|Do you think art can make progress over time the way science does?":"C|values|Which is closest to your view of whether art progresses over time?|it_progresses_like_science;it_changes_but_does_not_improve;it_has_declined;each_era_has_its_own_peak;other",
"N|values|Do you think love is the most important thing in a human life?":"S|values|How central is love to a good human life?|Love is optional for a good life ; Love is one good among many ; Love is one of the most important goods ; Love is the most important good ; Nothing else matters much without love",
"N|values|Is it possible to understand another person completely?":"S|values|How well can one person ever understand another?|Barely at all ; Only on the surface ; Fairly well ; Very well ; Completely",
"N|social|Do most people think their generation understands life better than older generations did?":"C|social|How do most people rate the wisdom of their own generation compared with older ones?|wiser;less_wise;about_the_same;wise_in_different_ways",
},
'thought_experiments':{
"N|social|Would most people rather live in the harsh real world than a pleasant cave of shadows, once they knew the difference?":"C|social|If most people could switch off all physical pain for a day with no side effects, what would they do?|switch_it_off;keep_it_on_for_safety;switch_it_off_only_for_a_hard_task;not_trust_the_offer",
"N|values|If you could never feel bored again, would your life become less creative?":"S|values|A device lets you spend a day with a small child's sense of wonder. How much would you want to try it?|Not at all ; A little ; Somewhat ; A lot ; More than almost anything",
"N|values|If every copy and memory of a song were lost, would the song still exist?":"C|values|If every copy and memory of a song were lost, what would be true of the song?|it_would_no_longer_exist;it_would_exist_as_a_possibility;it_would_still_exist_somehow;the_question_makes_no_sense",
},
'consciousness_ai':{
"N|values|Do you think animals play just for fun?":"S|values|How much do you think animals play just for the fun of it?|Animals never play for fun ; Only a few animals play for fun ; Many animals play for fun ; Most mammals play for fun ; Nearly all animals play for fun",
"N|values|Do you think a fly experiences time as passing more slowly than people do?":"C|values|Which animal do you think experiences time most differently from us?|a_fly;a_tortoise;a_hummingbird;a_whale;a_mayfly;other",
"N|values|Do you think a sleepwalker is conscious?":"S|values|How conscious do you think a sleepwalker is?|Not conscious at all ; Only dimly conscious ; Partly conscious ; Mostly conscious ; Fully conscious",
"N|values|Do you think a bee's dance to its hive is a kind of language?":"C|values|Which animal communication comes closest to language?|bee_dances;whale_songs;bird_calls;dolphin_whistles;ape_gestures;none",
},
'epistemics':{
"N|values|Do you think being very smart makes a person better at spotting their own mistakes?":"S|values|How much does being very smart help a person spot their own mistakes?|It does not help at all ; It helps a little ; It helps somewhat ; It helps a lot ; It makes a person almost immune to mistakes",
"N|personality|Do you usually read the full instructions before trying something new?":"S|personality|How carefully do you read instructions before trying something new?|I never read them ; I skim them after I get stuck ; I skim them first ; I read most of them first ; I read every word first",
"N|values|Is it possible to be certain that a memory of your own is accurate?":"C|values|Which of your memories do you trust most?|recent_ones;emotional_ones;ones_with_photos;ones_others_share;none_completely",
},
'luck_fate':{
"N|values|Do you believe people act strangely during a full moon?":"S|values|How much do you think a full moon affects how people behave?|Not at all ; A tiny bit ; Somewhat ; Noticeably ; A great deal",
"N|values|Do you believe that animals can sense a coming storm before people can?":"C|values|Which folk weather sign do you trust most?|red_sky_at_night;cows_lying_down;aching_joints;swallows_flying_low;none",
"N|values|Do you think some people attract drama wherever they go?":"S|values|How much do you think some people attract drama wherever they go?|Nobody attracts drama ; A rare few people do ; Some people do ; Many people do ; Drama follows certain people everywhere",
},
'time_mortality':{
"N|values|Should young children be told the truth when a pet dies?":"C|values|What is the best way to remember a pet that has died?|a_photo_on_display;planting_something;keeping_its_collar;a_small_ceremony;getting_another_pet;other",
"N|values|Do people become more alike as they grow old?":"S|values|How much do you think people become more alike as they grow old?|People become far more different ; People become a little more different ; People stay as different as ever ; People become a little more alike ; People become far more alike",
"N|values|Is it better to spend your time on a few long projects than many short ones?":"C|values|Which is the better way to spend a working life?|a_few_long_projects;many_short_projects;a_mix;one_life_work",
"N|values|Should adult birthdays still include a birthday cake?":"C|values|Which is the best way to mark an adult birthday?|a_cake_and_candles;a_meal_out;a_trip;a_quiet_day;no_marking_at_all",
},
'happiness_wellbeing':{
"N|values|Can being too positive about everything make a person less happy?":"C|values|Which is the kindest response to a friend's bad day?|cheer_them_up;listen;help_fix_it;distract_them;leave_them_be",
"N|values|Is it possible to be happy without ever feeling excitement?":"S|values|How much does a happy life need excitement?|It needs none at all ; A little now and then ; A fair amount ; A lot ; Constant excitement",
"N|values|Is happiness better when it is quiet rather than exciting?":"C|values|Which kind of happiness do you think lasts longer?|quiet_contentment;bursts_of_excitement;both_equally;neither_lasts",
"N|values|Would people be happier if they owned fewer clothes?":"S|values|How much happier would most households be with far fewer possessions?|Not happier at all ; A little happier ; Somewhat happier ; Much happier ; Dramatically happier",
"N|values|Do you think happiness is easier to find in small towns than in big cities?":"C|values|Where do you think happiness is easiest to find?|a_small_town;a_big_city;the_countryside;a_suburb;it_does_not_depend_on_place",
},
}
for n,d in R.items():
    L=open(n+'.txt').read().splitlines()
    c=0
    for i,l in enumerate(L):
        if l in d: L[i]=d[l]; c+=1
    assert c==len(d),(n,c,len(d))
    open(n+'.txt','w').write('\n'.join(L)+'\n')
print('ok')
