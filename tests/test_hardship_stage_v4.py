"""All fictional: independent exact hardship oracle and no-regression guards."""
from datetime import date
from itertools import product
import unittest

from solver.roster_cp_sat import Person, Shift, Event, independently_check
from solver.hardship_stage_v4 import (
    shift_burdens, hardship_score, solve_three_stage_hardship)


def d(day, slot):
    return Shift("door", date(2026, 12, day), slot)


def o(day, slot):
    return Shift("officer", date(2026, 12, day), slot)


def exact_brute_hardship(tasks, people, targets, expected_count_cost, pins=None,
                         occupied=None):
    """Exhaustively enumerate only tiny cases, independent of all CP-SAT."""
    pins = pins or {}
    expected = set(occupied) if occupied is not None else {t.key for t in tasks}
    optimal = None
    for combo in product([None] + [p.id for p in people], repeat=len(tasks)):
        chosen = dict(zip([t.key for t in tasks], combo))
        if {k for k,v in chosen.items() if v is not None} != expected:
            continue
        try:
            independently_check(tasks, people, chosen, pins=pins)
        except ValueError:
            continue
        counts = {p.id: sum(who == p.id for who in combo) for p in people}
        cost = sum(abs(counts[k] - val) for k,val in targets.items())
        if cost != expected_count_cost:
            continue
        harsh = hardship_score(tasks, chosen, people)["score"]
        optimal = harsh if optimal is None else min(optimal, harsh)
    if optimal is None:
        raise AssertionError("No brute-force feasible reference")
    return optimal


class HardshipThirdStageTests(unittest.TestCase):
    def test_four_independent_night_slots_and_noon_categories(self):
        expected = {
            1: {"night_total": 1, "night_22_24": 1},
            2: {"night_total": 1, "night_00_02": 1},
            3: {"night_total": 1, "night_02_04": 1},
            4: {"night_total": 1, "night_04_06": 1},
            8: {"noon": 1},
            5: {},
        }
        for slot,cats in expected.items():
            self.assertEqual(shift_burdens(d(1,slot)),cats)

    def test_officer_six_hour_and_noon_are_not_confused(self):
        self.assertEqual(shift_burdens(o(1,5)),
                         {"officer_hours":6,"officer_six_hour":1})
        self.assertEqual(shift_burdens(o(1,6)),
                         {"officer_hours":6,"noon":1,"officer_six_hour":1})
        self.assertEqual(shift_burdens(o(1,7)),{"officer_hours":4})
        self.assertEqual(shift_burdens(o(1,2)),
                         {"officer_hours":2,"night_total":1})

    def test_two_day_toy_matches_exhaustive_optimum_and_never_worsens(self):
        tasks = [d(1,1),d(1,8),d(4,2),d(4,8)]
        people = [Person("H001","door"),Person("H002","door")]
        targets = {"H001":2,"H002":2}
        result = solve_three_stage_hardship(
            tasks,people,targets,seconds_fill=3,
            seconds_fair=3,seconds_hardship=5)
        self.assertEqual(result["filled"],4)
        self.assertEqual(result["missing"],0)
        self.assertEqual(result["final_abs_count_deviation"],0)
        self.assertTrue(result["fixed_occupied_positions"])
        self.assertTrue(result["hardship_optimal_proven_given_locked_predecessors"])
        self.assertFalse(result["stage3_wasm_executed"])
        self.assertFalse(result["operationally_certified"])
        oracle=exact_brute_hardship(tasks,people,targets,0)
        self.assertEqual(result["hardship_final_score"],oracle)
        self.assertLessEqual(result["hardship_final_score"],
                             result["hardship_initial_score"])
        self.assertEqual(result["hardship_final_score"],
                         hardship_score(tasks,result["assignments"],people)["score"])
        self.assertTrue(independently_check(tasks,people,result["assignments"]))

    def test_officer_long_hours_toy_matches_brute_force(self):
        tasks=[o(1,5),o(1,6),o(3,1),o(3,7)]
        people=[Person("P001","officer"),Person("P002","officer"),
                Person("P003","officer")]
        targets={"P001":2,"P002":1,"P003":1}
        result=solve_three_stage_hardship(
            tasks,people,targets,seconds_fill=3,
            seconds_fair=3,seconds_hardship=5)
        self.assertEqual(result["filled"],4)
        self.assertEqual(result["final_abs_count_deviation"],0)
        self.assertTrue(result["hardship_optimal_proven_given_locked_predecessors"])
        oracle=exact_brute_hardship(tasks,people,targets,0)
        self.assertEqual(result["hardship_final_score"],oracle)

    def test_forced_blank_and_fixed_person_protected(self):
        tasks=[d(1,1),d(1,8),d(4,2),d(4,8)]
        people=[Person("H001","door"),Person("H002","door")]
        pins={tasks[0].key:None,tasks[1].key:"H001"}
        result=solve_three_stage_hardship(
            tasks,people,{"H001":1,"H002":2},pins=pins,
            seconds_fill=3,seconds_fair=3,seconds_hardship=5)
        self.assertEqual(result["filled"],3)
        self.assertIsNone(result["assignments"][tasks[0].key])
        self.assertEqual(result["assignments"][tasks[1].key],"H001")
        self.assertEqual(result["final_abs_count_deviation"],0)
        self.assertTrue(independently_check(
            tasks,people,result["assignments"],pins=pins))

    def test_eligibility_and_rest_override_night_balance(self):
        tasks=[d(1,1),d(2,2)]
        people=[Person("H001","door"),Person("H002","door")]
        events=[Event("H001","leave",date(2026,12,1),date(2026,12,1))]
        result=solve_three_stage_hardship(
            tasks,people,{"H001":2,"H002":0},
            events=events,seconds_fill=3,seconds_fair=3,
            seconds_hardship=5)
        self.assertEqual(result["filled"],1)
        self.assertEqual(result["missing"],1)
        self.assertTrue(independently_check(
            tasks,people,result["assignments"],events=events))

    def test_all_forced_blank_does_not_invent_staff(self):
        tasks=[d(1,1),d(1,8)]
        people=[Person("H001","door")]
        pins={x.key:None for x in tasks}
        result=solve_three_stage_hardship(
            tasks,people,{"H001":2},pins=pins,
            seconds_fill=3,seconds_fair=3,seconds_hardship=3)
        self.assertEqual(result["filled"],0)
        self.assertEqual(result["hardship_final_score"],0)
        self.assertEqual(result["hardship_initial_score"],0)
        self.assertFalse(any(result["assignments"].values()))

    def test_bad_time_limit_and_mixed_pools_fail(self):
        tasks=[d(1,1)]
        people=[Person("H001","door")]
        with self.assertRaisesRegex(ValueError,"time limit"):
            solve_three_stage_hardship(
                tasks,people,{"H001":1},seconds_hardship=0)
        with self.assertRaisesRegex(ValueError,"one duty pool"):
            solve_three_stage_hardship(
                [d(1,1),o(1,1)],people,{"H001":1})

    def test_independent_auditor_rejects_fake_person_and_missing_task(self):
        tasks=[d(1,1),d(1,8)]
        with self.assertRaisesRegex(ValueError,"Unknown assignment"):
            hardship_score(tasks,{tasks[0].key:"H900",tasks[1].key:None},
                           [Person("H001","door")])
        with self.assertRaisesRegex(ValueError,"Missing or extra"):
            hardship_score(tasks,{tasks[0].key:"H001"})


if __name__=="__main__":
    unittest.main()
