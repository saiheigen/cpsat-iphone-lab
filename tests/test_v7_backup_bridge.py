"""Strict local-only tests for actual v7 guard-offline-v5 backup layout.

ALL PERSONNEL AND EVENTS ARE FICTIONAL. NO LIVE MILITARY DATA.
"""
from datetime import date
from copy import deepcopy
import unittest

from solver.v7_backup_bridge import BridgeError, convert_v7_backup
from solver.roster_cp_sat import static_reason, Shift, independently_check, month_shifts
from solver.fairness_cp_sat import solve_layered


def serial(y, m, d):
    return (date(y, m, d) - date(1970, 1, 1)).days


def full_previous_schedule():
    # Exactly the v7 November 2026 shape: 360 guard + 210 officer entries.
    schedule = {"door": [], "officer": []}
    for t in month_shifts(2026, 11):
        schedule[t.pool].append([serial(t.day.year, t.day.month, t.day.day), t.num, None])
    return schedule


def set_previous_shift(schedule, pool, day, num, ident):
    rows = schedule[pool]
    target = [serial(2026, 11, day), num, None]
    for row in rows:
        if row[:2] == target[:2]:
            row[2] = ident
            return
    raise AssertionError("Previous-month fixture task absent")


def fake_backup():
    return {
        "format": "guard-offline-v5",
        "activeMonth": "2026-12",
        "global": {
            "door": "人員編號,級職,姓名,性別\nH001,上兵,模擬甲,男\nH002 上兵 模擬乙 男",
            "officer": "P001\t中士\t模擬丙\t男\nP002,上士,模擬丁,女",
            "leave": "模擬甲,115/12/04,115/12/05",
            "training": "",
            "duty": "",
            "meal": "P001,2026-12-10",
            "nightcheck": "",
            "driver": "",
            "exempt": "P002,免夜哨,,",
            "kitchen": "",
            "history": "大門,115/11/29,6,H001",
        },
        "months": {
            "2026-12": {
                "settings": {
                    "business": "H001,0.333333",
                    "carry": "H002,1",
                },
                "pins": {
                    f"door:{serial(2026, 12, 7)}:6": "H001",
                }
            }
        },
        "lifecycle": {},
    }


class V7BridgeTests(unittest.TestCase):
    def test_real_v7_field_shapes_and_roc_dates(self):
        x = convert_v7_backup(fake_backup())
        self.assertEqual(x.month, "2026-12")
        self.assertEqual(len(x.people), 4)
        self.assertEqual(len(x.tasks), 589)
        self.assertEqual(x.weights, {"H001": "0.333333"})
        self.assertEqual(x.carry, {"H002": 1})
        self.assertEqual(len(x.history), 1)
        self.assertEqual(x.history[0].shift.day, date(2026, 11, 29))
        self.assertEqual(x.pins, {"door:2026-12-07:6": "H001"})
        self.assertEqual(len(x.events), 3)
        self.assertFalse(x.operationally_certified)
        self.assertFalse(x.cross_month_confirmed)
        who = next(p for p in x.people if p.id == "H001")
        self.assertTrue(static_reason(who, Shift("door", date(2026, 12, 6), 6), x.events))
        self.assertIsNone(static_reason(who, Shift("door", date(2026, 12, 7), 6), x.events))

    def test_officer_no_night_exemption_and_meal(self):
        x = convert_v7_backup(fake_backup())
        p = next(p for p in x.people if p.id == "P002")
        self.assertTrue(static_reason(p, Shift("officer", date(2026, 12, 12), 1), x.events))
        self.assertIsNone(static_reason(p, Shift("officer", date(2026, 12, 12), 5), x.events))
        meal = next(p for p in x.people if p.id == "P001")
        self.assertTrue(static_reason(meal, Shift("officer", date(2026, 12, 9), 5), x.events))
        self.assertTrue(static_reason(meal, Shift("officer", date(2026, 12, 10), 5), x.events))
        self.assertTrue(static_reason(meal, Shift("officer", date(2026, 12, 11), 5), x.events))

    def test_duplicates_are_rejected_before_solve(self):
        data = fake_backup()
        data["global"]["officer"] += "\nH001,中士,虛構重複,男"
        with self.assertRaisesRegex(BridgeError, "編號重複"):
            convert_v7_backup(data)

    def test_ambiguous_name_cannot_silently_choose(self):
        data = fake_backup()
        data["global"]["officer"] += "\nP003,中士,模擬甲,男"
        with self.assertRaisesRegex(BridgeError, "同名"):
            convert_v7_backup(data)

    def test_day_before_night_and_return_day(self):
        data = fake_backup()
        who = next(p for p in convert_v7_backup(data).people if p.id == "H001")
        x = convert_v7_backup(data)
        self.assertTrue(static_reason(who, Shift("door", date(2026, 12, 3), 1), x.events))
        self.assertIsNone(static_reason(who, Shift("door", date(2026, 12, 3), 6), x.events))
        self.assertTrue(static_reason(who, Shift("door", date(2026, 12, 6), 6), x.events))

    def test_lifecycle_is_full_exemption_from_date(self):
        data = fake_backup()
        data["lifecycle"] = {"door:H002": "115/12/16"}
        x = convert_v7_backup(data)
        p = next(p for p in x.people if p.id == "H002")
        self.assertIsNone(static_reason(p, Shift("door", date(2026, 12, 15), 6), x.events))
        self.assertTrue(static_reason(p, Shift("door", date(2026, 12, 16), 6), x.events))

    def test_invalid_or_suspicious_year_fails_closed(self):
        data = fake_backup()
        data["global"]["leave"] = "H001,114/12/04,114/12/05"
        with self.assertRaisesRegex(BridgeError, "可能誤填"):
            convert_v7_backup(data)
        data["global"]["leave"] = "H001,115/02/30"
        with self.assertRaisesRegex(BridgeError, "不存在"):
            convert_v7_backup(data)

    def test_unbalanced_quotes_and_invalid_month(self):
        data = fake_backup()
        data["global"]["door"] = 'H001,上兵,"模擬甲,男'
        with self.assertRaisesRegex(BridgeError, "引號"):
            convert_v7_backup(data)
        data = fake_backup()
        with self.assertRaisesRegex(BridgeError, "YYYY-MM"):
            convert_v7_backup(data, month="2026-13")

    def test_existing_previous_schedule_imported_but_not_certified(self):
        data = fake_backup()
        schedule = full_previous_schedule()
        set_previous_shift(schedule, "door", 30, 2, "H002")
        set_previous_shift(schedule, "officer", 30, 5, "P002")
        data["months"]["2026-11"] = {
            "schedule": schedule,
            "inputSig": "cannot-recompute-here",
        }
        x = convert_v7_backup(data)
        self.assertEqual(len(x.history), 3)
        self.assertTrue(any("inputSig" in w for w in x.warnings))
        self.assertFalse(x.cross_month_confirmed)

    def test_previous_history_conflict_refused(self):
        data = fake_backup()
        schedule = full_previous_schedule()
        set_previous_shift(schedule, "door", 29, 6, "H002")
        data["months"]["2026-11"] = {"schedule": schedule}
        with self.assertRaisesRegex(BridgeError, "衝突"):
            convert_v7_backup(data)

    def test_auto_compensation_requires_local_confirmation(self):
        data = fake_backup()
        data["months"]["2026-11"] = {
            "locked": True,
            "compensationOut": {"door": {"H001": 2}, "officer": {}},
        }
        with self.assertRaisesRegex(BridgeError, "不能驗證 inputSig"):
            convert_v7_backup(data)

    def test_previous_month_truncated_schedule_rejected(self):
        data = fake_backup()
        data["months"]["2026-11"] = {
            "schedule": {"door": [[serial(2026, 11, 30), 2, "H002"]],
                         "officer": []}
        }
        with self.assertRaisesRegex(BridgeError, "班次數不符"):
            convert_v7_backup(data)

    def test_previous_month_duplicate_shift_rejected(self):
        data = fake_backup()
        schedule = full_previous_schedule()
        schedule["door"][1] = list(schedule["door"][0])
        data["months"]["2026-11"] = {"schedule": schedule}
        with self.assertRaisesRegex(BridgeError, "重複"):
            convert_v7_backup(data)

    def test_leap_day_shorthand_does_not_fail_on_neighbor_years(self):
        from solver.v7_backup_bridge import _date_token
        self.assertEqual(_date_token("2/29", date(2028, 2, 1)), date(2028, 2, 29))
        with self.assertRaisesRegex(BridgeError, "不存在"):
            _date_token("2/29", date(2026, 2, 1))

    def test_invalid_previous_month_identity_rejected(self):
        data = fake_backup()
        schedule = full_previous_schedule()
        set_previous_shift(schedule, "officer", 30, 5, "H001")
        data["months"]["2026-11"] = {"schedule": schedule}
        with self.assertRaisesRegex(BridgeError, "不屬於本月名冊"):
            convert_v7_backup(data)

    def test_invalid_pin_rejected(self):
        data = fake_backup()
        data["months"]["2026-12"]["pins"] = {"door:2026-12-07:6": "H001"}
        with self.assertRaisesRegex(BridgeError, "格式不符合 v7 日期序號"):
            convert_v7_backup(data)

    def test_kitchen_and_half_width_delimiters(self):
        data = fake_backup()
        data["global"]["kitchen"] = "H002"
        data["global"]["nightcheck"] = "H001，115/12/12"
        x = convert_v7_backup(data)
        self.assertTrue(next(p for p in x.people if p.id == "H002").kitchen)
        self.assertTrue(static_reason(next(p for p in x.people if p.id == "H001"),
                                      Shift("door", date(2026, 12, 11), 6), x.events))

    def test_no_v7_source_modification_or_actual_schedule_claim(self):
        x = convert_v7_backup(fake_backup())
        self.assertFalse(x.operationally_certified)
        self.assertIsInstance(x.warnings, list)
        self.assertIsNone(x.pins.get("officer:missing"))

    def test_small_subset_adapter_to_real_native_cp_sat(self):
        x = convert_v7_backup(fake_backup())
        two_days = [Shift("door", date(2026, 12, 7), 6),
                    Shift("door", date(2026, 12, 8), 6)]
        selected = {two_days[0].key: "H001"}
        result = solve_layered(two_days, x.people, events=x.events,
                               history=x.history, pins=selected,
                               weights=x.weights, carry=x.carry,
                               seconds_per_stage=3)
        self.assertEqual(result["filled"], 2)
        self.assertEqual(result["assignments"][two_days[0].key], "H001")
        self.assertTrue(independently_check(two_days, x.people, result["assignments"],
                                            x.events, x.history, selected))


if __name__ == "__main__":
    unittest.main()
