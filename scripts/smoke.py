from askjev.model import Question, HumanDist
from askjev.ingest import ingest_questions
qs = [
  Question("Which season is the best?", "choice", "self", "synthetic", "smoke", {"spring":None,"summer":None,"autumn":None,"winter":None}, kind="taste", node_hint="self.lifestyle.favorites"),
  Question("Is a hot dog a sandwich?", "noul", "world", "synthetic", "smoke", None, kind="evaluative", node_hint="world.food"),
  Question("Who is the greater basketball player?", "choice", "world", "synthetic", "smoke", {"michael_jordan":"Michael Jordan","lebron_james":"LeBron James"}, kind="taste", node_hint="world.sports.basketball.nba", human=[HumanDist("smoke poll", {"michael_jordan":0.6,"lebron_james":0.4}, 100)]),
  Question("How well does this statement describe you: \"I am the life of the party.\"", "score", "self", "synthetic", "smoke",
           ["This does not describe me at all","This describes me a little","This describes me moderately well","This describes me well","This describes me very well"], kind="personality"),
  Question("Does `message` request a refund?", "noul", "machine", "synthetic", "smoke", None, state={"message":"I was charged twice, please give me my money back."}, shape="detect", truth=True),
  Question("Is the Great Wall of China visible from space with the naked eye?", "noul", "world", "synthetic", "smoke", None, kind="factual", truth=False),
]
print("ingested", ingest_questions(qs))
