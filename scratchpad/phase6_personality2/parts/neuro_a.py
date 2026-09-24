C = []  # (text, [(key, desc), ...])
def c(t, *opts): C.append((t, list(opts)))

# worry / anxiety
c("The weather forecast shows storms on the weekend of an outdoor trip you planned. What do you usually do in the days before?",
  ("check_once","check the forecast once and wait"),("check_often","check the forecast several times a day"),("make_backup","make a backup plan and stop thinking about it"),("dread_trip","spend the week dreading the trip"),("other",None))
c("You hear a rumor that your workplace might cut some jobs. How do you usually react?",
  ("ignore_rumor","ignore it until there is real news"),("ask_around","quietly ask colleagues what they know"),("update_resume","update your resume just in case"),("lose_sleep","lose sleep imagining losing your job"),("other",None))
c("You leave your pet with a sitter for a few days. How do you usually spend the trip?",
  ("enjoy_trip","enjoy the trip without much thought"),("one_check_in","send one message to check in"),("frequent_updates","ask for photos and updates often"),("cut_trip_short","feel uneasy the whole time and think about coming home early"),("other",None))
c("A package you ordered shows as delayed with no new date. What do you usually do?",
  ("wait_calmly","wait and assume it will show up"),("check_tracking","check the tracking page now and then"),("contact_seller","contact the seller right away"),("assume_lost","assume it is lost and feel annoyed all day"),("other",None))
c("You notice a faint smell of something burning at home but can't find the source. What do you usually do?",
  ("check_once_move_on","look around once and move on"),("check_every_room","check every room and appliance"),("keep_sniffing","keep coming back to sniff for hours"),("call_someone","call someone to come check with you"),("other",None))
c("The night before a job interview, what are you usually doing?",
  ("relax_evening","having a normal relaxed evening"),("light_prep","doing a little light preparation"),("rehearse_late","rehearsing answers late into the night"),("imagine_failing","picturing everything that could go wrong"),("other",None))
c("You realize you may have left a light on at home after leaving for the day. What do you usually do?",
  ("forget_it","forget about it within minutes"),("ask_someone","ask someone at home to check"),("keep_thinking","keep thinking about it all day"),("go_back","go back home to check"),("other",None))
c("A plane you're on hits some turbulence. What are you usually doing?",
  ("keep_reading","keep reading or watching without much notice"),("glance_around","glance at the crew to see if they look calm"),("grip_armrest","grip the armrest until it passes"),("imagine_crash","imagine the worst for the rest of the flight"),("other",None))
c("You're walking through an unfamiliar neighborhood as it gets dark. What is your usual state of mind?",
  ("curious","curious about the new streets"),("alert","alert but relaxed"),("uneasy","uneasy and walking faster"),("scared","scared and wishing you were home"),("other",None))
c("A group project partner hasn't replied in two days. What do you usually assume?",
  ("theyre_busy","they are busy and will reply soon"),("gentle_nudge","it's worth a gentle nudge"),("theyre_slacking","they are slacking off"),("project_doomed","the whole project is going to fall apart"),("other",None))
c("You get a notice that your apartment will be inspected next week. How do you usually feel until then?",
  ("unbothered","unbothered"),("mildly_prepare","mildly focused on tidying"),("nervous_all_week","nervous all week about what they will find"),("tense_and_cleaning","tense and cleaning obsessively"),("other",None))
c("You lose phone signal while hiking a trail you know. What usually goes through your mind?",
  ("enjoy_quiet","enjoying the quiet"),("brief_note","a brief note to stay on the path"),("what_if_hurt","what would happen if you got hurt"),("turn_back","an urge to turn back right away"),("other",None))
c("You're starting a new job on Monday. How do you usually spend the weekend before?",
  ("normal_weekend","having a normal weekend"),("quiet_excitement","feeling quietly excited"),("mixed_nerves","switching between excitement and nerves"),("constant_worry","worrying constantly about fitting in"),("other",None))
c("After sending a message with an obvious typo to someone important, what do you usually do?",
  ("ignore_typo","ignore it since they'll understand"),("quick_correction","send a quick correction"),("reread_many_times","reread it many times and cringe"),("apologize_at_length","send an apology explaining the mistake"),("other",None))
c("You park in an unfamiliar lot and aren't sure the parking is allowed. What do you usually do?",
  ("park_and_go","park and forget about it"),("read_signs","read the signs once and go"),("keep_worrying","keep worrying about a ticket while you're out"),("move_car","move the car somewhere you're sure about"),("other",None))
c("A friend reads something you wrote and hasn't said anything yet. What do you usually think?",
  ("theyll_say_later","they'll tell me when they're ready"),("mild_curiosity","I'm curious but not worried"),("they_hated_it","they probably didn't like it"),("regret_sharing","I shouldn't have shown it to anyone"),("other",None))
c("You hear dripping from a pipe somewhere in your home late at night. What do you usually do?",
  ("sleep_deal_tomorrow","go to sleep and deal with it tomorrow"),("quick_look","take a quick look and go back to bed"),("lie_awake_listening","lie awake listening and imagining flooding"),("search_until_found","get up and search until you find it"),("other",None))
c("You have an exam in a month. When do you usually start feeling nervous about it?",
  ("day_of","on the day itself, if at all"),("night_before","the night before"),("week_before","about a week before"),("right_away","as soon as you learn the date"),("other",None))
c("A friend says 'we need to talk' but won't say about what until tomorrow. How do you usually spend the evening?",
  ("forget_until_then","mostly forget about it until then"),("wonder_a_bit","wonder about it a little"),("list_possibilities","go through every possible problem"),("cannot_relax","feel unable to relax all night"),("other",None))
c("You booked tickets online and suddenly wonder if you picked the wrong date. What do you usually do?",
  ("trust_yourself","trust that you picked right"),("check_once","open the confirmation and check once"),("check_repeatedly","check it several times over the next days"),("call_to_confirm","call the company to be sure"),("other",None))
c("A storm knocks out the power in the evening. How do you usually feel?",
  ("cozy","cozy, and light some candles"),("mildly_bored","mildly bored"),("uneasy","uneasy until it comes back"),("worried_about_damage","worried about what else might go wrong"),("other",None))
c("Your manager adds an unexpected meeting to your calendar with no agenda. What do you usually assume?",
  ("routine_matter","it's something routine"),("no_assumption","nothing until you get there"),("something_wrong","something might be wrong"),("im_in_trouble","you're in trouble for something"),("other",None))
c("You are asked to give a toast at a friend's celebration in a few weeks. How do you usually handle the time before it?",
  ("barely_think","barely think about it until the day"),("write_and_relax","write something and relax"),("rewrite_often","rewrite it many times"),("dread_it","dread it for weeks"),("other",None))
c("You're waiting in line to board a flight and can't find your passport for a moment. What usually happens?",
  ("calm_search","search calmly, sure it's somewhere"),("quick_panic","feel a quick jolt, then find it"),("heart_racing","heart races long after you find it"),("keep_checking","keep checking your bag for the rest of the trip"),("other",None))

# irritability / anger
c("Someone takes the parking spot you were clearly waiting for. What do you usually do?",
  ("find_another","find another spot and forget it"),("mutter","mutter something to yourself"),("honk_or_gesture","honk or gesture at them"),("stay_angry","stay angry about it for a good while"),("other",None))
c("A neighbor's dog barks on and off all evening. How do you usually respond?",
  ("tune_out","tune it out"),("close_windows","close the windows and carry on"),("grow_irritated","grow more irritated as the night goes on"),("complain_angrily","go over and complain in a temper"),("other",None))
c("Your roommate or family member leaves dirty dishes in the sink again. What do you usually do?",
  ("wash_them","wash them without much thought"),("mention_calmly","mention it calmly later"),("leave_sharp_note","leave a sharp note"),("snap_at_them","snap at them when they get home"),("other",None))
c("You're stuck behind someone walking very slowly on a narrow sidewalk. How do you usually feel?",
  ("patient","patient, there's no rush"),("look_for_gap","look for a gap to pass"),("sigh_loudly","irritated, maybe sigh loudly"),("fuming","fuming until you get past"),("other",None))
c("Autocorrect keeps changing a word you typed correctly. What do you usually do?",
  ("fix_it","fix it and move on"),("laugh_it_off","laugh at it"),("grumble","grumble at the phone"),("lose_temper","get genuinely angry at the phone"),("other",None))
c("People behind you in a movie theater keep talking. How do you usually respond?",
  ("ignore","ignore it"),("move_seats","move seats"),("ask_politely","ask them politely to stop"),("seethe","seethe and struggle to enjoy the movie"),("other",None))
c("A coworker replies to all on an email thread that didn't need it, again. How do you usually react?",
  ("delete_it","delete it without thinking"),("mild_eye_roll","roll your eyes a little"),("vent_to_someone","vent about it to someone"),("stay_irritated","stay irritated for a while"),("other",None))
c("Someone cuts in front of you in a queue. What do you usually do?",
  ("let_it_go","let it go"),("point_it_out","point it out calmly"),("confront_sharply","confront them sharply"),("stew_silently","say nothing but stew about it"),("other",None))
c("A video you're watching keeps buffering. How do you usually react?",
  ("wait_it_out","wait it out patiently"),("do_something_else","do something else meanwhile"),("keep_restarting","keep restarting it in frustration"),("give_up_annoyed","give up in a bad mood"),("other",None))
c("Someone tells you to 'calm down' when you're mildly annoyed. What usually happens?",
  ("calm_down","you do calm down"),("laugh","you laugh it off"),("get_more_annoyed","you get more annoyed"),("flare_up","you flare up at them"),("other",None))
c("The same person asks you a question you've already answered twice. What do you usually do?",
  ("answer_again","answer again patiently"),("write_it_down","write it down for them"),("answer_curtly","answer curtly"),("show_frustration","openly show your frustration"),("other",None))
c("An appliance keeps beeping to tell you something is done. How do you usually feel?",
  ("dont_notice","barely notice it"),("go_turn_off","go turn it off calmly"),("irritated","irritated by the noise"),("very_agitated","agitated until it stops"),("other",None))
c("You can't find the remote control you just had in your hand. What is your usual reaction?",
  ("amused","amused at yourself"),("calm_search","search calmly"),("frustrated","frustrated and a bit short with others"),("very_angry","disproportionately angry"),("other",None))
c("You lose a close online game because of a lag spike. What do you usually do?",
  ("shrug","shrug and queue again"),("take_break","take a short break"),("complain_loudly","complain loudly"),("quit_upset","quit for the day in a bad mood"),("other",None))
c("A group chat keeps buzzing while you're trying to focus. How do you usually respond?",
  ("mute_it","mute it without a second thought"),("check_later","check it later"),("keep_getting_annoyed","get more annoyed with each buzz"),("snap_in_chat","post something short and irritated"),("other",None))
c("A car horn blares at you when you hesitate at a green light. How do you usually feel afterward?",
  ("unbothered","unbothered"),("slightly_embarrassed","slightly embarrassed"),("angry_for_minutes","angry for a few minutes"),("rattled_for_hours","rattled for hours"),("other",None))
c("Someone at home borrows your things without asking. What do you usually do?",
  ("dont_mind","don't really mind"),("ask_next_time","ask them to check next time"),("get_irritated","get irritated and say so"),("blow_up","blow up at them"),("other",None))
c("A recipe you followed carefully turns out badly. How do you usually react?",
  ("laugh_and_eat","laugh and eat it anyway"),("figure_out_why","figure out what went wrong"),("sulk","sulk for the evening"),("throw_it_out_angry","throw it out in frustration"),("other",None))
c("Flat-pack furniture you're assembling turns out to be missing a piece. What do you usually do?",
  ("contact_calmly","contact the store calmly"),("improvise","improvise a fix"),("curse_and_stop","curse and stop for the day"),("stay_furious","stay furious about it all evening"),("other",None))
c("You've been on hold with customer service for a long time. What state are you usually in when someone finally answers?",
  ("perfectly_calm","perfectly calm"),("a_little_impatient","a little impatient"),("clearly_irritated","clearly irritated"),("ready_to_argue","ready to argue"),("other",None))
c("Someone kicks the back of your seat on a long bus or plane ride. How do you usually respond?",
  ("ignore_it","ignore it"),("polite_request","turn and ask politely"),("glare","glare back at them"),("grow_furious","grow more furious each time"),("other",None))
c("Someone spoils the ending of a show you were about to watch. How do you usually react?",
  ("dont_care","don't really care"),("mild_groan","groan and move on"),("annoyed_for_a_day","stay annoyed with them for a day"),("very_upset","get quite upset"),("other",None))
c("You lose a friendly board game you were winning most of the way. What do you usually do?",
  ("congratulate","congratulate the winner"),("ask_rematch","ask for a rematch"),("go_quiet","go quiet and sulky"),("get_short","get short with the other players"),("other",None))

# low mood
c("It rains every day of a short vacation. How do you usually feel by the end?",
  ("made_the_best","glad you made the best of it"),("mildly_disappointed","mildly disappointed"),("pretty_down","pretty down"),("trip_ruined","like the trip was ruined"),("other",None))
c("On your birthday, what mood are you usually in by the evening?",
  ("happy","happy"),("content","content"),("a_bit_flat","a bit flat"),("sad_or_empty","sad or empty"),("other",None))
c("When the holiday season ends and normal life resumes, how do you usually feel?",
  ("glad_for_routine","glad to be back in routine"),("neutral","neutral"),("a_bit_blue","a bit blue for a few days"),("low_for_weeks","low for weeks"),("other",None))
c("You finish a book you really loved. What do you usually feel afterward?",
  ("satisfied","satisfied"),("eager_for_next","eager for the next one"),("a_little_empty","a little empty"),("down_for_days","down for days"),("other",None))
c("You hear a song that reminds you of an old chapter of your life. How does it usually leave you?",
  ("warmly_nostalgic","warmly nostalgic"),("neutral","mostly unaffected"),("wistful","wistful for a while"),("sad","sad for the rest of the day"),("other",None))
c("Late in the year, when you think about goals you didn't reach, how do you usually feel?",
  ("motivated","motivated for next year"),("accepting","accepting"),("disappointed","disappointed in yourself"),("hopeless","like nothing will change"),("other",None))
c("When the days get shorter and darker in winter, how does your mood usually change?",
  ("no_change","it doesn't change"),("slightly_slower","slightly slower"),("noticeably_lower","noticeably lower"),("gloomy_all_season","gloomy all season"),("other",None))
c("After a visit with family ends and everyone leaves, how do you usually feel?",
  ("relieved_or_happy","relieved or happy"),("calm","calm"),("lonely_for_a_bit","lonely for a bit"),("sad_for_days","sad for days"),("other",None))
c("You scroll past an old friend's big achievement online. What is your usual reaction?",
  ("happy_for_them","happy for them"),("indifferent","mostly indifferent"),("a_twinge","a small twinge about your own life"),("feel_behind","a heavy sense of being behind"),("other",None))
c("On a quiet evening with nothing to do, where does your mind usually drift?",
  ("pleasant_plans","to pleasant plans or daydreams"),("nothing_much","nowhere in particular"),("old_regrets","to old regrets"),("dark_what_ifs","to gloomy thoughts about the future"),("other",None))

# self-consciousness
c("Everyone at a table starts singing to someone and you're expected to join. What do you usually do?",
  ("sing_loudly","sing along loudly"),("sing_normally","sing along normally"),("mouth_words","mouth the words quietly"),("stay_silent","stay silent and feel awkward"),("other",None))
c("You want a photo of yourself at a scenic spot while strangers are around. What do you usually do?",
  ("pose_freely","pose freely without caring"),("quick_photo","take a quick photo"),("wait_till_empty","wait until nobody is around"),("skip_it","skip it because people might watch"),("other",None))
c("You hear a recording of your own voice. What do you usually feel?",
  ("fine","fine with it"),("mildly_odd","it sounds a little odd"),("cringe","a strong cringe"),("cant_listen","you can't bear to keep listening"),("other",None))
c("At a wedding, the dance floor fills up. What do you usually do?",
  ("dance_freely","dance freely"),("join_with_friends","join once friends do"),("dance_stiffly","dance stiffly, feeling watched"),("stay_seated","stay seated to avoid being seen"),("other",None))
c("You have a question during a large lecture or talk. What do you usually do?",
  ("ask_out_loud","ask it out loud"),("ask_after","ask the speaker afterward"),("hope_someone_else","hope someone else asks it"),("never_ask","never ask for fear of sounding silly"),("other",None))
c("You wear a bold new piece of clothing for the first time. How do you usually feel when you're out?",
  ("confident","confident"),("mostly_fine","mostly fine"),("keep_checking","keep checking how it looks"),("regret_it","regret it and want to change"),("other",None))
c("You have to order food in a language you barely speak. What usually happens?",
  ("try_happily","try it happily"),("point_at_menu","point at the menu with a smile"),("rehearse_nervously","rehearse nervously before your turn"),("let_others_order","ask someone else to order for you"),("other",None))
c("It's your first visit to a new gym full of regulars. How do you usually feel?",
  ("at_ease","at ease"),("mildly_awkward","mildly awkward at first"),("very_watched","like everyone is watching"),("leave_early","uncomfortable enough to leave early"),("other",None))
c("Your stomach growls loudly in a silent room. What do you usually do?",
  ("laugh","laugh it off"),("ignore","ignore it"),("blush","blush and hope nobody heard"),("apologize_repeatedly","apologize and feel embarrassed for a while"),("other",None))
c("You need to return an item to a store without a receipt. How do you usually feel beforehand?",
  ("no_big_deal","it's no big deal"),("slightly_hesitant","slightly hesitant"),("rehearse_what_to_say","nervous enough to rehearse what to say"),("avoid_returning","uneasy enough that you keep the item instead"),("other",None))
c("Someone looks over your shoulder while you type a message. How do you usually react?",
  ("keep_typing","keep typing normally"),("tilt_screen","tilt the screen a little"),("start_making_typos","get flustered and start making typos"),("stop_entirely","stop until they leave"),("other",None))
c("On a video call, you notice your own camera view. What do you usually do?",
  ("ignore_it","ignore it"),("glance_occasionally","glance at it now and then"),("watch_yourself","keep watching how you look"),("turn_camera_off","turn the camera off if you can"),("other",None))
c("You're the only one who dressed formally for a casual event. How do you usually feel?",
  ("dont_care","don't care"),("joke_about_it","joke about it"),("self_conscious","self-conscious all evening"),("want_to_leave","want to leave or change"),("other",None))
c("Someone mispronounces your name and you'd need to correct them in front of others. What do you usually do?",
  ("correct_easily","correct them easily"),("correct_later","correct them later in private"),("let_it_slide","let it slide to avoid awkwardness"),("dwell_on_it","let it slide but dwell on it later"),("other",None))
c("You have to read something aloud to a group. What usually happens?",
  ("read_smoothly","you read smoothly"),("minor_nerves","minor nerves at the start"),("rush_through","you rush through it"),("stumble_badly","your voice shakes and you stumble"),("other",None))

# impulsiveness / cravings
c("Late at night you think of your favorite takeout. What do you usually do?",
  ("dont_order","think about it and go to bed"),("plan_tomorrow","plan to get it tomorrow"),("snack_instead","eat a snack from home instead"),("order_right_away","order it right away"),("other",None))
c("Candy and snacks are stacked next to the checkout. What usually happens?",
  ("walk_past","walk past without thinking"),("look_but_skip","look but skip"),("grab_one","grab one on a whim"),("grab_several","grab a few, sometimes regretting it"),("other",None))
c("A limited edition item you like goes on sale with a countdown timer. What do you usually do?",
  ("ignore","ignore it"),("sleep_on_it","sleep on it even if you miss it"),("buy_fast","buy it fast to not miss out"),("buy_extra","buy it and add more to the cart"),("other",None))
c("You open a new bag of chips intending to have a few. What usually happens?",
  ("have_a_few","you have a few and close it"),("have_a_bowl","you pour a bowl and stop"),("keep_going","you keep going longer than planned"),("finish_the_bag","you finish the bag"),("other",None))
c("When the dessert menu arrives after a big meal, what do you usually do?",
  ("decline","decline"),("share_one","share one with someone"),("order_own","order your own"),("order_even_if_full","order even though you're too full"),("other",None))
c("You pass a bakery and smell fresh bread. What do you usually do?",
  ("keep_walking","keep walking"),("note_for_later","make a note to come back"),("step_in_buy_one","step in and buy one thing"),("buy_more_than_planned","go in and buy more than you meant to"),("other",None))
c("You're working and feel the urge to check your phone. What usually happens?",
  ("ignore_urge","ignore the urge"),("wait_until_break","wait until a break"),("quick_peek","take a quick peek"),("lose_time_scrolling","end up scrolling for a long time"),("other",None))
c("A travel site shows a cheap last-minute trip. What do you usually do?",
  ("close_the_tab","close the tab"),("save_for_later","save it to think about"),("check_calendar","check your calendar seriously"),("book_on_the_spot","book it on the spot"),("other",None))
c("A promotional email offers a big discount that ends tonight. What do you usually do?",
  ("delete_it","delete it"),("look_but_skip","look but buy nothing"),("buy_something_needed","buy something you needed anyway"),("buy_things_you_dont_need","buy things you don't really need"),("other",None))
c("At an all-you-can-eat buffet, what usually happens?",
  ("eat_normally","you eat a normal meal"),("small_extra","you have a little extra"),("eat_too_much","you eat past full"),("feel_sick_after","you eat so much you feel unwell after"),("other",None))
c("You're trying to save money and see something you want in a shop window. What do you usually do?",
  ("walk_on","walk on"),("add_to_wishlist","add it to a wish list"),("go_in_to_look","go in just to look, then leave"),("buy_it_anyway","buy it anyway"),("other",None))
c("You're tired but a game or show is at a cliffhanger late at night. What do you usually do?",
  ("stop_now","stop and sleep"),("one_more","do one more and stop"),("several_more","keep going for several more"),("until_very_late","keep going until very late"),("other",None))

# stress vulnerability
c("Your laptop crashes the night before a deadline. How do you usually react?",
  ("solve_calmly","work the problem calmly"),("brief_panic","panic briefly, then fix it"),("freeze_up","freeze up for a while"),("fall_apart","fall apart and can't think straight"),("other",None))
c("You realize your wallet is missing while you're out. What do you usually do first?",
  ("retrace_steps","calmly retrace your steps"),("call_places","call the places you've been"),("panic_search","search in a panic"),("assume_the_worst","assume it's stolen and feel sick"),("other",None))
c("You miss a connecting flight. How do you usually handle it?",
  ("go_rebook","go rebook without fuss"),("mild_frustration","feel mild frustration, then rebook"),("very_stressed","get very stressed at the counter"),("fall_apart","feel close to tears"),("other",None))
c("Guests show up an hour earlier than expected while you're still getting ready. How do you usually react?",
  ("welcome_them","welcome them and finish up"),("laugh_it_off","laugh it off"),("flustered","get flustered"),("snap_or_stress","get stressed and a bit short with everyone"),("other",None))
c("Your car breaks down on the way to something important. What is your usual reaction?",
  ("call_for_help","call for help and wait calmly"),("problem_solve","figure out another way to get there"),("very_upset","get very upset"),("overwhelmed","feel overwhelmed and stuck"),("other",None))
c("Your workplace switches to new software with little warning. How do you usually cope?",
  ("adapt_quickly","adapt quickly"),("learn_gradually","learn it gradually"),("stressed_for_weeks","stay stressed for weeks"),("dread_each_day","dread using it every day"),("other",None))
c("Loud construction starts outside while you're trying to work. How do you usually cope?",
  ("tune_out","tune it out"),("put_on_headphones","put on headphones"),("cant_focus","can't focus at all"),("very_frazzled","get frazzled and tense"),("other",None))
c("Your plans for the day get rearranged by someone else at the last minute. How do you usually feel?",
  ("flexible","flexible about it"),("mild_annoyance","mildly annoyed"),("thrown_off","thrown off for the day"),("very_stressed","very stressed"),("other",None))
c("You're moving homes and boxes are everywhere. How do you usually feel during the move?",
  ("excited","excited"),("busy_but_fine","busy but fine"),("frazzled","frazzled"),("overwhelmed","overwhelmed and short-tempered"),("other",None))
c("Two important things fall due on the same day. What usually happens?",
  ("plan_and_do","you plan and do both"),("prioritize","you pick one and ask for more time on the other"),("scramble","you scramble anxiously"),("shut_down","you feel so overwhelmed you shut down for a while"),("other",None))
c("You're hosting a holiday meal and one dish burns. How do you usually react?",
  ("laugh_and_adapt","laugh and adapt"),("quick_fix","make a quick replacement"),("upset_but_hide","feel upset but hide it"),("ruins_the_day","feel it has ruined the day"),("other",None))
c("Someone gives you a task with an unclear deadline. How do you usually feel about it?",
  ("relaxed","relaxed"),("ask_for_clarity","you ask for clarity and move on"),("uneasy","uneasy until it's done"),("anxious","anxious, as if it's due any moment"),("other",None))
