import sys
fixes = {
"How often do you feel left out by your friends?": "I can't remember the last time I felt left out ; I feel left out when I miss one event ; I often see photos of plans I wasn't told about ; I feel like an outsider in most of my friend groups",
"How often do you give friends advice they didn't ask for?": "I only give advice when asked ; I offer advice only when I see a real danger ; I offer advice when I think I know better ; I give my opinion on almost everything they tell me",
"How often do you tell friends you appreciate them?": "I never say it out loud ; I say it only in birthday cards ; I say it after they help me with something ; I tell them regularly, even for no reason",
"How fast do new friendships become close for you?": "I rarely get close to new people at all ; It takes me years to feel close ; It takes several months of regular contact ; I feel close after a few good conversations ; I feel close to someone after one evening",
"How much do you share photos of your friends online?": "I never post friends ; I post friends only at weddings or big events ; I post group photos from most outings ; I post friends almost every time we meet",
"How often do you invite a friend you don't know well to hang out?": "I never invite someone I don't know well ; I invite them only as part of a group ; I invite them one-on-one if we clicked ; I invite new acquaintances out all the time",
"How much do you enjoy meeting strangers through friends?": "I skip events where I won't know people ; I go but stick to my friend ; I chat with a few new people ; I go hoping to make new friends",
"How much do you rely on social media to know what friends are up to?": "I learn everything directly from them ; I check their posts now and then ; I learn most of their news from their posts ; I would know almost nothing without social media",
"How often do you think about friends you've lost touch with?": "They rarely cross my mind ; I think of them on their birthdays ; I think of them when a song or place reminds me ; I think about them most weeks",
"How often do you remember friends' birthdays without reminders?": "I rely completely on reminders ; I remember one or two without help ; I remember most close friends' birthdays ; I remember nearly everyone's birthday",
"How often do you reach out to old friends you haven't heard from in years?": "I never reach out to old friends ; I reach out only if I need something ; I reach out when something reminds me of them ; I regularly reach out to keep old ties alive",
"How often do you reconnect with childhood friends?": "I have no contact with childhood friends ; I see them only at reunions or weddings ; I catch up with one about once a year ; I still see childhood friends regularly",
"How much do you enjoy friends' inside jokes that you weren't part of?": "I feel shut out when they come up ; I smile along without getting them ; I ask for the story and enjoy it ; I start using the jokes myself",
"How do you feel about long phone calls with friends?": "I let calls go to voicemail and text back ; I take a call only if it's short ; I enjoy a long call now and then ; I spend hours on the phone with friends regularly",
"How competitive are you with your friends?": None,
}
out=[]
for line in open("friendship.txt"):
    p=line.rstrip("\n").split(" | ")
    if len(p)>=3 and p[2] in fixes and fixes[p[2]]:
        p[3]=fixes[p[2]]; line=" | ".join(p)+"\n"
    out.append(line)
open("friendship.txt","w").writelines(out)
