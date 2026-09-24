import sys
D='/Users/junzhang/Projects/askjev/scratchpad/phase6_mind2/'
FIX={
'happiness_wellbeing':{
'How often do you feel grateful for small things, like a good meal or a kind word?':'I rarely notice small good things at all ; I feel grateful only when someone points something out ; I notice and appreciate a small thing a few times a week ; I stop to appreciate small things several times every day',
'How often do you find yourself completely absorbed in something you are doing?':'I cannot remember the last time I lost track of time doing something ; I get absorbed only on rare special occasions ; I lose track of time in an activity a few times a week ; I lose myself in something I am doing nearly every day',
'How often do you laugh with other people?':'I go weeks without sharing a real laugh with anyone ; I share a laugh with someone now and then ; I laugh with someone on most days ; I laugh with people many times every day',
'How often do you feel that your life is interesting?':'My days feel dull and the same ; Something interesting happens to me once in a while ; Most weeks bring something that catches my interest ; My life feels interesting nearly all the time',
'How often do you catch yourself thinking you will be happy once some future thing happens?':'I almost never tie my happiness to a future event ; I catch myself thinking it now and then ; I often think I will be happy once something changes ; I am almost always waiting for the next thing to make me happy',
'How much do you enjoy your daily routine?':'My daily routine drains me ; I put up with my routine to get through the day ; I like most parts of my daily routine ; I genuinely look forward to my daily routine',
'How often do you feel a sense of wonder or awe?':'I cannot remember ever feeling true awe ; I have felt awe only a few times in my life ; I feel awe now and then, usually on trips or in nature ; I feel wonder often, even in ordinary moments',
'How much do you enjoy celebrations like birthdays and holidays?':'I would rather skip celebrations altogether ; I go along with celebrations but get little from them ; I enjoy celebrations when they come around ; Celebrations are the highlights of my year',
'How often do you notice beauty in ordinary things, like light through a window?':'I almost never notice beauty in ordinary things ; I notice it once in a while when I slow down ; I stop to notice ordinary beauty fairly often ; I notice something beautiful nearly every day',
'How often do you have days you would happily live again?':'I almost never have a day I would want to repeat ; I have such a day a few times a year ; I have such a day a few times a month ; I have a day I would gladly relive most weeks',
'How often do you feel you have enough of what you need?':'I almost always feel I am short of something I need ; I feel I have enough only in good stretches ; I feel I have enough most of the time ; I nearly always feel I have all I need',
'How often do you tell people you appreciate them?':'I almost never tell people I appreciate them ; I tell people I appreciate them only on birthdays or holidays ; I tell someone I appreciate them every so often ; I tell people I appreciate them often, without any special reason',
'How often do you feel that life is going in a good direction?':'I feel my life is heading the wrong way ; I feel my life is going well only in brief stretches ; I feel my life is heading in a good direction most of the time ; I nearly always feel my life is on a good path',
'How much do you enjoy your mornings?':'I dread getting up every morning ; I just get through my mornings ; I like my mornings ; Mornings are my favorite part of the day',
'How much joy do pets bring to your life?':'I do not care for animals and get no joy from pets ; I like other people\'s pets in passing ; Pets brighten my days noticeably ; Pets are one of my biggest sources of happiness',
'How much does a friend\'s good news make your own day better?':'A friend\'s good news does not change my day ; A friend\'s good news gives me a brief lift ; A friend\'s good news puts me in a good mood for the day ; A friend\'s good news feels almost like my own',
'How often do you do something just for fun, with no other purpose?':'I almost never do anything purely for fun ; I do something just for fun now and then ; I do something just for fun a few times a week ; I do something just for fun every day',
'How often do you feel carefree?':'I cannot remember the last time I felt carefree ; I feel carefree only on holidays ; I feel carefree on a fair number of ordinary days ; I feel carefree most of the time',
'How much do you think your happiness is shaped by your childhood?':'My childhood has little to do with how happy I am now ; My childhood set a few patterns I still notice ; My childhood shaped much of how happy I am ; My happiness today comes almost entirely from my childhood',
'How often do you end a day feeling it was worthwhile?':'I rarely end a day feeling it was worthwhile ; I feel a day was worthwhile now and then ; I feel most days were worthwhile ; I end nearly every day feeling it was worthwhile',
'How often do you share a meal with people you care about?':'I almost always eat alone ; I share a meal with loved ones only on special occasions ; I share a meal with loved ones a few times a month ; I share a meal with loved ones several times a week',
'How much do you enjoy learning something new?':'I find learning new things tedious ; I learn new things only when I need to ; I enjoy picking up something new ; Learning new things is one of my great loves',
'How free do you feel to live the way you want?':'I feel trapped in a life I did not choose ; I feel held back in many parts of my life ; I feel free in most parts of my life ; I feel completely free to live as I want',
'How often do you feel proud of how you spent your day?':'I rarely feel proud of how I spent a day ; I feel proud of a day now and then ; I feel proud of how I spent most days ; I feel proud of how I spent nearly every day',
'How much of your day do you spend doing things you enjoy?':'I spend almost none of my day doing things I enjoy ; I get a small slice of each day for things I enjoy ; I spend about half my day on things I enjoy ; I spend most of my day doing things I enjoy',
},
'time_mortality':{
'How much do you look forward to your later years?':'I dread my later years ; I avoid thinking about my later years ; I have no strong feelings about my later years ; I look forward to parts of my later years ; I am eager for my later years',
'How comfortable are you with the idea of growing old alone?':'The idea of growing old alone terrifies me ; The idea of growing old alone worries me often ; The idea of growing old alone concerns me a little ; I would be at ease growing old alone',
'How often do you think about the people you have lost?':'I almost never think about people I have lost ; I think of them on anniversaries and holidays ; Someone I lost comes to mind most weeks ; I think of someone I lost nearly every day',
'How often do you reread letters or messages from people who are no longer in your life?':'I never reread old letters or messages ; I reread one once in a long while ; I reread old letters a few times a year ; I reread old letters and messages often',
'How often do you think about what you would do if you had very little time left?':'I never think about it ; I think about it only after hearing sad news ; I think about it now and then ; I think about it often enough that it shapes my choices',
'How often do you catch yourself saying things were better in the old days?':'I never say things were better in the old days ; I say it only as a joke ; I say it when something new annoys me ; I say it most days',
'How much should people prepare for their own death while healthy?':'People need not prepare anything while healthy ; People should cover the basics, like naming who gets what ; People should write a clear will and wishes ; People should plan everything down to the music',
'How often do you visit graves of relatives?':'I never visit graves of relatives ; I visit graves only when attending a service ; I visit graves on special anniversaries ; I visit graves of relatives several times a year',
'How much should birthdays be celebrated as adults get older?':'Adult birthdays should pass unmarked ; Adult birthdays deserve a quiet acknowledgment ; Adult birthdays deserve a nice dinner ; Adult birthdays deserve a big celebration every year',
'How often do you imagine what your life will look like in old age?':'I never imagine my life in old age ; I imagine it once in a great while ; I imagine it every few months ; I imagine it every week or more',
'How much should older people step aside to make room for the young?':'Older people should never step aside because of age ; Older people should step aside in a few roles ; Older people should step aside from most leadership roles ; Older people should step aside completely once they reach old age',
'How much would you want to know about your future if a reliable source offered it?':'I would want to know nothing about my future ; I would want to know only whether I will be happy ; I would want to know the major events ; I would want to know every detail',
'How often do you think about how much time you spend on screens?':'I never think about my screen time ; I think about my screen time once in a while ; I think about my screen time every week ; I regret my screen time every day',
'How often do you think about a younger version of yourself?':'I never think about my younger self ; I think about my younger self only on birthdays ; I think about my younger self now and then ; I think about my younger self often',
'How much would you want to be kept alive by machines if you could not recover?':'DROP',
'How much do you plan your weekends in advance?':'DROP',
'How much should people take big risks while they are young?':'Young people should avoid big risks entirely ; Young people should take only small risks ; Young people should take a few meaningful risks ; Young people should take as many bold risks as they can',
'How often do you think you have plenty of time left?':'I feel time is running out for me ; I rarely feel I have plenty of time ; I usually feel I have plenty of time ; I feel I have all the time in the world',
'How do you feel when a year comes to an end?':'I barely notice the year ending ; I feel mild surprise at how fast the year went ; I sit down and reflect on the year ; I write a detailed review and plans for the next year',
},
}
for n,fx in FIX.items():
    L=open(D+n+'.txt').read().splitlines(); out=[]; used=set()
    for l in L:
        f=l.split(' | ')
        if len(f)>2 and f[2] in fx:
            used.add(f[2])
            if fx[f[2]]=='DROP': continue
            f[3]=fx[f[2]]; l=' | '.join(f)
        out.append(l)
    print(n,set(fx)-used)
    open(D+n+'.txt','w').write('\n'.join(out)+'\n')
