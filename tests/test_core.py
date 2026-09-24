from askjev.authored import round_trip_ok, slug
from askjev.jev import Request, pack, parse_answer, gateway_question
from askjev.measure import brier, ece, top, truth_key, tvd
from askjev.model import Question


def test_parse_answers():
    a = parse_answer({"type": "boolean", "probability": 0.8})
    assert a.type == "noul" and a.p_yes == 0.8
    c = parse_answer({"type": "choice", "choice": "x", "probabilities": {"x": 0.7, "y": 0.3}, "confidence": 0.5})
    assert c.dist["x"] == 0.7 and c.confidence == 0.5


def test_request_hash_stable_and_repeat_distinct():
    q = {"a": gateway_question("noul", "Is it?")}
    assert Request({"s": 1}, q).hash == Request({"s": 1}, q).hash
    assert Request({"s": 1}, q).hash != Request({"s": 1}, q, repeat_idx=1).hash


def test_pack_respects_budget():
    qs = {f"q{i}": gateway_question("noul", "x" * 400) for i in range(100)}
    reqs = pack({"s": 1}, qs, budget=2000)
    assert len(reqs) > 1 and sum(len(r.questions) for r in reqs) == 100


def test_measures():
    assert tvd({"a": 1.0}, {"b": 1.0}) == 1.0
    assert top({"a": 0.6, "b": 0.4})[0] == "a"
    assert truth_key("noul", True) == "true"
    assert abs(brier({"true": 1.0, "false": 0.0}, "true")) < 1e-9
    assert ece([(0.9, True)] * 10 + [(0.9, False)] * 10) is not None


def test_question_validation_and_id():
    q = Question("Best season?", "choice", "self", "synthetic", "t", {"a": None, "b": None}, kind="taste")
    assert q.validate() == []
    assert len(q.id) == 24
    bad = Question("x", "score", "self", "synthetic", "t", ["only one"], kind="taste")
    assert bad.validate()


def test_round_trip_rule():
    assert round_trip_ok("self.love.friendship", "self.love.friendship")
    assert round_trip_ok("self.love", "self.love.friendship")
    assert not round_trip_ok("self.love.friendship", "world.food")
    assert slug("Hip hop!") == "hip_hop"
