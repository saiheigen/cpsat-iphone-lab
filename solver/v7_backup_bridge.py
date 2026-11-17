"""Local-only adapter for actual v7 guard-offline-v5 JSON backup.

NO NETWORK I/O. NEVER upload sensitive real-world rosters to GitHub Actions.
The output is a testing interface for a PARTIAL native CP-SAT model, NOT a
certified replacement for the v7 scheduling application.

Source alignment: v7 HTML build(), parseDate(), csvFields(), monthInputs(),
projectBackup(), schedule and pin serialization. No synthetic fields required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
import calendar
import re
from typing import Any

from solver.roster_cp_sat import Person, Shift, Event, History, month_shifts

_EPOCH = date(1970, 1, 1)
_EXCEL = date(1899, 12, 30)
_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_GLOBAL = ("door", "officer", "leave", "training", "duty", "meal",
           "nightcheck", "driver", "exempt", "kitchen", "history")
_EVENT_MAP = {"leave": "leave", "training": "training", "duty": "officer_duty",
              "meal": "meal", "nightcheck": "nightcheck", "driver": "driver"}
_HEADERS = {"人員編號", "編號", "姓名", "級職", "勤務類別", "類型", "日期", "人員", "序號"}
_RANKS = {"二兵", "一兵", "上兵", "下士", "中士", "上士", "士官長",
          "少尉", "中尉", "上尉", "少校", "中校", "上校", "少將", "中將", "上將"}
_SEX = {"男", "女", "其他", "男性", "女性", "M", "F", "X", "male", "female"}


class BridgeError(ValueError):
    """Fail-closed parsing error; original source data must be repaired."""


@dataclass
class BridgeResult:
    month: str
    people: list[Person]
    tasks: list[Shift]
    events: list[Event]
    history: list[History]
    pins: dict[str, str | None]
    weights: dict[str, str]
    carry: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    # Critical caveats are explicit rather than silently claiming parity.
    cross_month_confirmed: bool = False
    compensation_confirmed: bool = False
    operationally_certified: bool = False


def _day_from_serial(raw: Any) -> date:
    if type(raw) is not int:
        raise BridgeError("歷史日期須為 v7 內部整數日期序號")
    try:
        return _EPOCH + timedelta(days=raw)
    except (OverflowError, ValueError):
        raise BridgeError("歷史日期序號超出合理範圍") from None


def _month_date(y: int, m: int, d: int) -> date:
    try:
        return date(y, m, d)
    except ValueError:
        raise BridgeError(f"不存在的日期：{y}/{m}/{d}") from None


def _date_token(raw: Any, target: date) -> date:
    s = str(raw or "").strip()
    if not s:
        raise BridgeError("缺少日期")
    if re.fullmatch(r"\d+(?:\.0+)?", s):
        n = int(float(s))
        if 20000 < n < 90000:
            return _EXCEL + timedelta(days=n)
    s = re.sub(r"[年月.\-]", "/", s).replace("日", "").replace(" ", "")
    vals = [v for v in s.split("/") if v]
    if any(not re.fullmatch(r"\d+", v) for v in vals):
        raise BridgeError(f"日期格式錯誤：{s}")
    if len(vals) == 3:
        y, m, d = map(int, vals)
        if y <= 0:
            raise BridgeError("年份必須大於零")
        if y < 100:
            y += 2000
        elif y < 1911:
            y += 1911
        return _month_date(y, m, d)
    if len(vals) == 2:
        m, d = map(int, vals)
        # A valid leap day in the target year must not be rejected simply
        # because the preceding or following year lacks February 29.
        opts = []
        for yy in (target.year - 1, target.year, target.year + 1):
            try:
                opts.append(date(yy, m, d))
            except ValueError:
                continue
        if not opts:
            raise BridgeError(f"不存在的日期：{s}")
        return min(opts, key=lambda candidate: abs((candidate - target).days))
    raise BridgeError(f"日期欄位不足：{s}")


def _fields(raw: str) -> list[str]:
    """Match v7's tabs, quoted CSV, Chinese commas, semicolons, and spaces."""
    raw = str(raw)
    if '"' not in raw and "\t" in raw:
        return [v.strip() for v in raw.split("\t")]
    if '"' not in raw and not any(x in raw for x in ",，;\t"):
        parts = re.split(r"[\s\u3000]+", raw.strip())
        if len(parts) >= 3 and re.fullmatch(r"[HP]\d+", parts[0], re.I):
            if parts[1] in _RANKS:
                last = parts[-1]
                sex = last.lower() in {x.lower() for x in _SEX}
                return [parts[0], parts[1], " ".join(parts[2:-1] if sex else parts[2:]),
                        last if sex else ""]
            if parts[-1].lower() in {x.lower() for x in _SEX}:
                return [parts[0], "", " ".join(parts[1:-1]), parts[-1]]
        return [x for x in parts if x]
    tab = "\t" in raw
    result, cur, quoted, i = [], "", False, 0
    while i < len(raw):
        ch = raw[i]
        if ch == '"':
            if quoted and i + 1 < len(raw) and raw[i+1] == '"':
                cur += '"'
                i += 1
            else:
                quoted = not quoted
        elif ((ch == "\t") if tab else (ch in ",，;")) and not quoted:
            result.append(cur.strip())
            cur = ""
        else:
            cur += ch
        i += 1
    result.append(cur.strip())
    if quoted:
        raise BridgeError("CSV 引號未成對")
    return result


def _rows(text: Any, section: str):
    if text is None:
        return
    if not isinstance(text, str):
        raise BridgeError(f"{section} 必須為文字")
    for no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            fields = _fields(line)
        except BridgeError as exc:
            raise BridgeError(f"{section} 第 {no} 行：{exc}") from None
        if fields and re.sub(r"\s+", "", fields[0]) in _HEADERS:
            continue
        yield no, fields


def _expect_fields(fields, minimum, maximum, section, line):
    if not minimum <= len(fields) <= maximum:
        raise BridgeError(f"{section} 第 {line} 行欄位數異常 ({len(fields)})")


def _check_year_suspect(token, year, month, section):
    s = str(token or "")
    values = re.findall(r"\d+", s)
    if len(values) != 3:
        return
    yy, mm, _ = map(int, values)
    if yy < 100:
        yy += 2000
    elif yy < 1911:
        yy += 1911
    if abs(yy - year) == 1 and mm == month:
        raise BridgeError(f"{section} 存在可能誤填前／後一年的紀錄：{s}，請先確認")


def _guard_backup(data: Any, selected: str | None):
    if not isinstance(data, dict) or data.get("format") not in (
        "guard-offline-v5", "guard-offline-v4.2", "guard-offline-v4"):
        raise BridgeError("僅接受 v7 對應的 guard-offline-v5／v4 內部備份 JSON")
    global_text = data.get("global")
    months = data.get("months")
    if not isinstance(global_text, dict) or not isinstance(months, dict):
        raise BridgeError("備份缺少 global 或 months")
    month = selected or data.get("activeMonth")
    if not isinstance(month, str) or not _MONTH.fullmatch(month):
        raise BridgeError("請指定有效 YYYY-MM 月份")
    if "business" in global_text or "carry" in global_text:
        raise BridgeError("舊版共用補償尚未轉到月份設定，請先使用 v7 網站升級備份")
    return month, global_text, months


def convert_v7_backup(data: dict, month: str | None = None) -> BridgeResult:
    """Convert a v7 backup locally. Does NOT run CP-SAT or transmit data."""
    month, global_text, months = _guard_backup(data, month)
    y, m = map(int, month.split("-"))
    first = date(y, m, 1)
    last = date(y, m, calendar.monthrange(y, m)[1])
    prior = first - timedelta(days=1)
    prior_key = prior.strftime("%Y-%m")
    target = first
    entries = months.get(month, {})
    if not isinstance(entries, dict):
        raise BridgeError("所選月份設定有誤")
    settings = entries.get("settings", {})
    if not isinstance(settings, dict):
        raise BridgeError("月份 settings 必須為物件")
    people, names, ids = [], {}, {}
    for pool in ("door", "officer"):
        for no, fields in _rows(global_text.get(pool, ""), pool):
            _expect_fields(fields, 2, 4, pool, no)
            ident = fields[0].strip()
            rank = fields[1].strip()
            full_name = fields[2].strip() if len(fields) >= 3 else rank
            # Exactly mirror v7 normalizeRosterFields(): a 3-column row
            # "ID,姓名,性別" must not silently become name="男/女".
            if (len(fields) == 3 and rank not in _RANKS
                    and full_name.lower() in {s.lower() for s in _SEX}):
                full_name = rank
                rank = ""
            if not ident or not full_name or ident in ids:
                raise BridgeError(f"{pool} 第 {no} 行：缺少姓名或編號重複")
            if not re.fullmatch(r"[A-Za-z]\w{0,40}", ident):
                raise BridgeError(f"{pool} 第 {no} 行：人員編號格式無效")
            p = Person(ident, pool)
            ids[ident] = p
            people.append(p)
            names.setdefault(full_name, []).append(p)
    if not ids or not any(p.pool == "door" for p in people) or not any(p.pool == "officer" for p in people):
        raise BridgeError("大門與安官名冊都不能是空白")

    def resolve(token, section, pool=None):
        token = str(token or "").strip()
        if not token:
            raise BridgeError(f"{section} 缺少人員")
        if token in ids:
            who = ids[token]
            if pool and who.pool != pool:
                raise BridgeError(f"{section} 人員不屬於 {pool}：{token}")
            return who
        matches = [p for p in names.get(token, []) if pool is None or p.pool == pool]
        if len(matches) != 1:
            raise BridgeError(f"{section} 人員名稱找不到或同名，請用編號：{token}")
        return matches[0]

    kitchen = set()
    for no, f in _rows(global_text.get("kitchen", ""), "固定伙房"):
        _expect_fields(f, 1, 1, "固定伙房", no)
        kitchen.add(resolve(f[0], "固定伙房").id)
    people = [Person(p.id, p.pool, kitchen=p.id in kitchen) for p in people]

    events = []
    for section, kind in _EVENT_MAP.items():
        for no, f in _rows(global_text.get(section, ""), section):
            _expect_fields(f, 2, 3, section, no)
            p = resolve(f[0], section, "officer" if section in ("duty", "meal") else None)
            b = f[1]
            e = f[2] if len(f) > 2 and f[2] else b
            _check_year_suspect(b, y, m, section)
            _check_year_suspect(e, y, m, section)
            start, end = _date_token(b, target), _date_token(e, target)
            if start > end:
                raise BridgeError(f"{section} 第 {no} 行：結束日早於開始日")
            events.append(Event(p.id, kind, start, end))

    exempt_names = {"all": "exempt_all", "night": "exempt_night", "noon": "exempt_noon"}
    for no, f in _rows(global_text.get("exempt", ""), "免哨"):
        _expect_fields(f, 2, 4, "免哨", no)
        p = resolve(f[0], "免哨")
        kind = f[1].strip()
        if any(t in kind for t in ("全面", "全免", "免哨")):
            t = "all"
        elif any(t in kind for t in ("免夜", "不用夜")):
            t = "night"
        elif any(t in kind for t in ("免午", "午間")):
            t = "noon"
        else:
            raise BridgeError(f"免哨第 {no} 行：無法識別免哨類型")
        b = f[2] if len(f) > 2 else ""
        e = f[3] if len(f) > 3 else ""
        if bool(b) != bool(e):
            raise BridgeError(f"免哨第 {no} 行：生效日與結束日必須同時填")
        _check_year_suspect(b, y, m, "免哨")
        _check_year_suspect(e, y, m, "免哨")
        start, end = (_date_token(b, target), _date_token(e, target)) if b else (date.min, date.max)
        events.append(Event(p.id, exempt_names[t], start, end))

    lifecycle = data.get("lifecycle", {})
    if not isinstance(lifecycle, dict):
        raise BridgeError("離單位資料格式不正確")
    for key, raw in lifecycle.items():
        if not isinstance(key, str) or ":" not in key:
            raise BridgeError("離單位人員編號格式錯誤")
        pool, ident = key.split(":", 1)
        if ident not in ids or pool != ids[ident].pool:
            raise BridgeError("離單位紀錄找不到對應名冊人員")
        start = _date_token(raw, target)
        events.append(Event(ident, "exempt_all", start, date.max))

    weights, carry = {}, {}
    for no, f in _rows(settings.get("business", ""), "業參"):
        _expect_fields(f, 1, 2, "業參", no)
        p = resolve(f[0], "業參")
        if p.id in weights:
            raise BridgeError("業參同一人重複登記")
        val = f[1].strip() if len(f) > 1 and f[1] else "0.333333"
        from solver.fairness_cp_sat import _scaled_weight
        if _scaled_weight(val) <= 0:
            raise BridgeError("業參權重必須大於 0")
        weights[p.id] = val
    for no, f in _rows(settings.get("carry", ""), "跨月補償"):
        _expect_fields(f, 2, 2, "跨月補償", no)
        p = resolve(f[0], "跨月補償")
        if p.id in carry or not re.fullmatch(r"\d+", f[1]):
            raise BridgeError("跨月補償同人重複或不是非負整數")
        carry[p.id] = int(f[1])

    tasks = month_shifts(y, m)
    task_keys = {t.key for t in tasks}
    warnings = []
    history = []
    history_seen = {}
    for no, f in _rows(global_text.get("history", ""), "跨月既有班次"):
        _expect_fields(f, 4, 4, "跨月既有班次", no)
        pool = ("door" if f[0] in ("大門", "door", "衛哨")
                else "officer" if f[0] in ("安官", "officer", "安全士官") else None)
        if pool is None:
            raise BridgeError("跨月班次未指定大門或安官")
        when = _date_token(f[1], target)
        if first <= when <= last:
            raise BridgeError("跨月歷史不能包含當月班次")
        if not f[2].isdigit():
            raise BridgeError("跨月班次時段須為整數")
        who = resolve(f[3], "跨月既有班次", pool)
        t = Shift(pool, when, int(f[2]))
        if t.key in history_seen:
            raise BridgeError("跨月歷史班次重複")
        history_seen[t.key] = who.id
        history.append(History(who.id, t))

    previous = months.get(prior_key, {})
    if not isinstance(previous, dict):
        raise BridgeError("前月儲存資料格式不正確")
    if previous.get("schedule"):
        sch = previous["schedule"]
        if not isinstance(sch, dict):
            raise BridgeError("前月已存班表格式不正確")
        # v7 validateBackupMonthShapes() requires a complete month grid. A
        # truncated grid cannot be presented as valid cross-month history.
        py, pm = prior.year, prior.month
        expected_days = calendar.monthrange(py, pm)[1]
        expected_slots = {"door": 12, "officer": 7}
        for pool, slots_per_day in expected_slots.items():
            values = sch.get(pool)
            if not isinstance(values, list) or len(values) != expected_days * slots_per_day:
                raise BridgeError("前月已存班表班次數不符，禁止用不完整歷史判斷")
            seen = set()
            for entry in values:
                if not isinstance(entry, list) or len(entry) != 3:
                    raise BridgeError("前月班次必須為 [日序號, 班號, 編號]")
                serial, num, ident = entry
                when = _day_from_serial(serial)
                if (when.year, when.month) != (py, pm):
                    raise BridgeError("前月班表包含其他月份")
                if type(num) is not int or not 1 <= num <= slots_per_day:
                    raise BridgeError("前月班號無效")
                key = (serial, num)
                if key in seen:
                    raise BridgeError("前月班次日期與時段重複")
                seen.add(key)
                if ident is not None and (not isinstance(ident, str) or
                                          ident not in ids or ids[ident].pool != pool):
                    raise BridgeError("前月班次人員不屬於本月名冊")
        for pool in ("door", "officer"):
            values = sch[pool]
            for entry in values:
                if not isinstance(entry, list) or len(entry) != 3:
                    raise BridgeError("前月班次必須為 [日序號, 班號, 編號]")
                serial, num, ident = entry
                when = _day_from_serial(serial)
                if not first - timedelta(days=14) <= when < first or ident is None:
                    continue
                if type(num) is not int:
                    raise BridgeError("前月班號必須為整數")
                if ident not in ids or ids[ident].pool != pool:
                    raise BridgeError("前月班次人員不屬於本月名冊")
                t = Shift(pool, when, num)
                if t.key in history_seen:
                    if history_seen[t.key] != ident:
                        raise BridgeError("人工跨月紀錄與已存前月班表衝突")
                    continue
                history_seen[t.key] = ident
                history.append(History(ident, t))
        warnings.append("前月已存班表已讀入，但 Python 尚未重新驗證 v7 inputSig 新鮮度；跨月尚未核定")
    else:
        warnings.append("找不到已存前月班表；只有明確人工歷史紀錄，無法證明跨月完整")

    pins = {}
    raw_pins = entries.get("pins", {})
    if not isinstance(raw_pins, dict):
        raise BridgeError("人工固定班次欄位不是物件")
    for k, who in raw_pins.items():
        # v7 uses Unix *day serial* keys, while our native Shift.key uses ISO
        # dates. Never compare the two formats without an explicit conversion.
        match = re.fullmatch(r"(door|officer):(-?\d+):(\d+)", k) if isinstance(k, str) else None
        if not match:
            raise BridgeError("人工固定班次編號格式不符合 v7 日期序號")
        pool, day_serial, shift_num = match.groups()
        day = _day_from_serial(int(day_serial))
        try:
            canonical = Shift(pool, day, int(shift_num)).key
        except ValueError:
            raise BridgeError("人工固定班號無效") from None
        if canonical not in task_keys:
            raise BridgeError("人工固定班次編號不在本月班表")
        if who is not None and (who not in ids or ids[who].pool != pool):
            raise BridgeError("人工固定人員不存在或勤務種類不一致")
        if canonical in pins:
            raise BridgeError("人工固定班次重複")
        pins[canonical] = who

    unverified_auto = previous.get("compensationOut")
    if previous.get("locked") and unverified_auto:
        if not isinstance(unverified_auto, dict):
            raise BridgeError("前月補償資料格式有誤")
        outstanding = [p.id for p in people
                       if isinstance(unverified_auto.get(p.pool), dict)
                       and unverified_auto[p.pool].get(p.id, 0)
                       and p.id not in carry]
        if outstanding:
            raise BridgeError(
                "前月有封存自動補償，但目前不能驗證 inputSig；"
                "請在 v7 本機確認本月補償，再使用此介面。"
                "涉及人數：" + str(len(outstanding)))
        warnings.append("前月補償未直接套用；已使用本月明確的手動補償")

    # Fail closed on a potentially stale existing schedule, without relying on
    # a Python guess of the application's JavaScript signature algorithm.
    if entries.get("schedule"):
        warnings.append("本月備份內含既有班表；轉換器不會覆寫或視為有效排班")
    return BridgeResult(
        month=month, people=people, tasks=tasks, events=events,
        history=history, pins=pins, weights=weights, carry=carry,
        warnings=warnings, cross_month_confirmed=False,
        compensation_confirmed=not bool(unverified_auto),
        operationally_certified=False,
    )
