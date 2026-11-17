"""Synthetic tests for the independent native CP-SAT roster prototype.

These do not assert that the full v7.0 system or 589-shift model is complete.
"""
from datetime import date, timedelta
import unittest

from solver.roster_cp_sat import (
    Event, History, Person, Shift, conflicts, independently_check,
    month_shifts, prepare, solve, static_reason,
)

D = lambda n, month=12: date(2026, month, n)


class TaskSchemaTests(unittest.TestCase):
    def test_november_2026(self):
        tasks = month_shifts(2026, 11)
        self.assertEqual(len(tasks), 570)
        self.assertEqual(sum(t.pool == "door" for t in tasks), 360)
        self.assertEqual(sum(t.pool == "officer" for t in tasks), 210)

    def test_december_2026(self):
        tasks = month_shifts(2026, 12)
        self.assertEqual(len(tasks), 589)
        self.assertEqual(sum(t.pool == "door" for t in tasks), 372)
        self.assertEqual(sum(t.pool == "officer" for t in tasks), 217)
        self.assertEqual(len({t.key for t in tasks}), 589)

    def test_v7_time_slots(self):
        self.assertEqual((Shift("door", D(1), 1).start,
                          Shift("door", D(1), 1).end), (22, 24))
        self.assertEqual([Shift("officer", D(1), i).hours
                          for i in range(1, 8)], [2, 2, 2, 2, 6, 6, 4])


class AvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.p = Person("H001", "door")
        self.q = Person("P001", "officer")

    def check_event(self, kind, start, end, day_num, num, blocked=True, person=None):
        p = person or self.p
        e = Event(p.id, kind, start, end)
        reason = static_reason(p, Shift(p.pool, day_num, num), [e])
        self.assertEqual(bool(reason), blocked, (kind, day_num, num, reason))

    def test_leave_return_day_and_night_before(self):
        for n in (4, 5, 6):
            self.check_event("leave", D(4), D(5), D(n), 6)
        self.check_event("leave", D(4), D(5), D(3), 1)
        self.check_event("leave", D(4), D(5), D(3), 6, False)
        self.check_event("leave", D(4), D(5), D(7), 6, False)

    def test_nightcheck_three_days(self):
        for n in (11, 12, 13):
            self.check_event("nightcheck", D(12), D(12), D(n), 6)
        self.check_event("nightcheck", D(12), D(12), D(14), 6, False)

    def test_driving_and_training(self):
        self.check_event("driver", D(12), D(12), D(11), 1)
        self.check_event("driver", D(12), D(12), D(11), 6, False)
        for n in (12, 13):
            self.check_event("driver", D(12), D(12), D(n), 6)
        for n in (9, 10, 11):
            self.check_event("training", D(10), D(11), D(n), 6)
        self.check_event("training", D(10), D(11), D(12), 6, False)

    def test_officer_duty_and_meal(self):
        for kind in ("officer_duty", "meal"):
            for n in (11, 12, 13):
                self.check_event(kind, D(12), D(12), D(n), 6, person=self.q)
            self.check_event(kind, D(12), D(12), D(14), 6, False, self.q)

    def test_exemptions_and_kitchen(self):
        self.check_event("exempt_night", D(1), D(31), D(3), 1)
        self.check_event("exempt_night", D(1), D(31), D(3), 6, False)
        self.check_event("exempt_noon", D(1), D(31), D(3), 8)
        self.check_event("exempt_noon", D(1), D(31), D(3), 6, False)
        self.assertEqual(static_reason(Person("K", "door", kitchen=True),
                         Shift("door", D(3), 6), []), "kitchen")

    def test_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            Event("H001", "unknown", D(1), D(2))
        with self.assertRaises(ValueError):
            prepare([Shift("door", D(1), 6)], [self.p],
                    [Event("MISSING", "leave", D(1), D(2))])

    def test_rest_and_sunday(self):
        a = Shift("door", D(3), 3)
        self.assertTrue(conflicts(a, Shift("door", D(4), 10)))
        self.assertFalse(conflicts(a, Shift("door", D(3), 10)))
        self.assertTrue(conflicts(Shift("door", D(3), 6),
                                  Shift("door", D(3), 8)))
        self.assertTrue(conflicts(a, Shift("door", D(5), 3)))
        self.assertFalse(conflicts(a, Shift("door", D(6), 3)))
        self.assertTrue(conflicts(Shift("officer", D(3), 5),
                                  Shift("officer", D(3), 7)))
        self.assertTrue(conflicts(Shift("door", D(15, 11), 5),
                                  Shift("door", D(22, 11), 11)))
        self.assertTrue(conflicts(Shift("officer", D(15, 11), 7),
                                  Shift("officer", D(22, 11), 7)))


class NativeCpSatTests(unittest.TestCase):
    def test_one_worker_cannot_fill_every_day(self):
        person = [Person("H001", "door")]
        tasks = [Shift("door", D(n), 6) for n in (1, 2, 3)]
        result = solve(tasks, person, seconds=5)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual((result["filled"], result["missing"]), (1, 2))
        self.assertTrue(independently_check(tasks, person, result["assignments"]))

    def test_two_days_are_not_double_booked(self):
        people = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", D(n), 6) for n in (1, 2)]
        result = solve(tasks, people, seconds=5)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["filled"], 2)
        self.assertEqual(set(result["assignments"].values()), {"H001", "H002"})

    def test_officer_cannot_double_shift(self):
        people = [Person("P001", "officer")]
        tasks = [Shift("officer", D(1), 5), Shift("officer", D(1), 7)]
        result = solve(tasks, people, seconds=5)
        self.assertEqual(result["filled"], 1)
        self.assertEqual(result["missing"], 1)

    def test_valid_pin_preserved(self):
        people = [Person("H001", "door"), Person("H002", "door")]
        tasks = [Shift("door", D(1), 6), Shift("door", D(2), 6)]
        result = solve(tasks, people, pins={tasks[0].key: "H001"}, seconds=5)
        self.assertEqual(result["assignments"][tasks[0].key], "H001")
        self.assertEqual(result["assignments"][tasks[1].key], "H002")

    def test_ineligible_pin_rejected(self):
        tasks = [Shift("door", D(6), 6)]
        ev = [Event("H001", "leave", D(5), D(5))]
        with self.assertRaisesRegex(ValueError, "violates hard rule"):
            solve(tasks, [Person("H001", "door")], events=ev,
                  pins={tasks[0].key: "H001"})

    def test_prior_month_rest_blocks_assignment(self):
        person = [Person("H001", "door")]
        tasks = [Shift("door", D(1), 6)]
        history = [History("H001", Shift("door", date(2026, 11, 30), 3))]
        result = solve(tasks, person, history=history, seconds=5)
        self.assertEqual((result["filled"], result["missing"]), (0, 1))

    def test_forced_blank(self):
        task = Shift("door", D(1), 6)
        result = solve([task], [Person("H001", "door")],
                       pins={task.key: None}, seconds=5)
        self.assertEqual(result["filled"], 0)

    def test_independent_audit_rejects_tampering(self):
        person = [Person("H001", "door")]
        tasks = [Shift("door", D(1), 6), Shift("door", D(2), 6)]
        with self.assertRaisesRegex(ValueError, "Duty conflict"):
            independently_check(tasks, person,
                                {tasks[0].key: "H001", tasks[1].key: "H001"})

    def test_bad_history_rejected(self):
        person = [Person("H001", "door")]
        history = [History("H001", Shift("door", D(28, 11), 6)),
                   History("H001", Shift("door", D(29, 11), 3))]
        with self.assertRaisesRegex(ValueError, "Conflicting prior"):
            prepare([Shift("door", D(1), 6)], person, history=history)



class BoundaryOptimizationTests(unittest.TestCase):
    def test_three_spaced_door_shifts_allowed(self):
        who = [Person("H001", "door")]
        shifts = [Shift("door", D(1), n) for n in (2, 6, 10)]
        result = solve(shifts, who, seconds=5)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["filled"], 3)

    def test_four_daily_door_shifts_forced_is_impossible(self):
        who = [Person("H001", "door")]
        shifts = [Shift("door", D(1), n) for n in (2, 6, 10, 12)]
        result = solve(shifts, who, seconds=5)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["filled"], 3)

    def test_sunday_standby_cannot_repeat_next_week(self):
        people = [Person("H001", "door")]
        shifts = [Shift("door", D(15, 11), 5),
                  Shift("door", D(22, 11), 11)]
        result = solve(shifts, people, seconds=5)
        self.assertEqual(result["filled"], 1)

    def test_prev_month_two_day_same_slot_block(self):
        people = [Person("H001", "door")]
        shifts = [Shift("door", D(2), 6), Shift("door", D(3), 6)]
        history = [History("H001", Shift("door", D(30, 11), 6))]
        result = solve(shifts, people, history=history, seconds=5)
        self.assertIsNone(result["assignments"][shifts[0].key])
        self.assertEqual(result["filled"], 1)


if __name__ == "__main__":
    unittest.main()
