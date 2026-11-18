# 第十五階段｜兩階段填班優先、公平其次的 C++／WASM 原型（編譯驗證中）

更新日期：2026-11-18。所有情境使用公開 GitHub 上的**完全虛構**班次、人員索引與勤務禁排，未上傳真實軍務資料。

## 為什麼需要新版本

[第十四階段已通過的 589 班密集 WASM](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44214006711) 在真實離線 Chromium 的桌面和手機尺寸模擬各測六組（共 12 組），都達到 OPTIMAL，通過獨立逐班稽核；但目前 C++ 只最大化合法填班，**並未真正平均人員班數**。

本階段不動已通過的 `guard-month-v2` 及其 `cp_sat_month_bridge.cc`。新增**獨立** `guard-month-fair-v3` 和 `cp_sat_month_fair_bridge.cc`。

## 新 C++ 解法：真正兩階段求解

1. 從完整月份 372 大門／56 人或 217 安官／50 人的**匿名資格矩陣**、人工固定、合法初稿與每人公平目標建模。先用 OR-Tools CP-SAT 單執行緒最大化合法填班數，最長搜尋 10 秒。
2. 若第一階段取得合法可行解，記住實際填班數 `locked`，新增硬限制 `sum(all_assignments) == locked`，然後在**相同硬限制**下最小化 `sum(abs(person_month_count - target))`，第二階段也最長 10 秒。
3. 若第二階段回傳 UNKNOWN、未找到更好解或未證明最優，保留第一階段合法結果；若第二階段變差不予採用。輸出 `fill_phase`、`fair_phase`、`fill_optimal_proven`、`fair_optimal_proven_given_fill`，避免誤把「已找到可行解」宣稱全域公平最優。
4. 若第一階段填滿所有可填上限，有獨立的填班最優上界；若第一階段只回傳 FEASIBLE 且尚有可能增加填班，第二階段的「公平最優」只限於當下鎖定的班數。
5. 原本的強制資格位元、同日勤務數／休息、站一歇一、同時段間隔、兩週日留守、跨月歷史的前置禁排和人工固定，在新版 C++ 中照舊保留，不能因公平目標而放寬。

## 協議與原生驗證已完成

- `solver/full_month_fair_wire_v3.py`：先獨立驗證原 `guard-month-v2` 全月資料，再依 v7 已建立的配額、1/3 權重、督伙與前月 carry 規則，產生每人整數軟目標。完整 v3 協議只有**八行**，前七行是 v2 匿名月份、班數、資格矩陣、人工固定與提示（只換版本標頭），第八行是對應人員順序的目標整數，不包含姓名、證號或詳細休假。
- `audit_full_month_fair_v3_response`：用原 Python 排班規則獨立驗證輸出的每一班、個人班數、絕對偏差、固定與休息限制；若字串聲稱 OPTIMAL，也**不單靠外來 JSON 證明 CP-SAT 真的執行或證明最公平**。
- `tests/test_full_month_fair_wire_v3.py`：核對 2026/12 完整兩勤務池 589/106、1/3 權重、前月補償、人工固定、匿名索引順序、竄改目標、偽造最優與假造偏差等負面案例。[原生 CI #120](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216462958) 的相應測試步驟成功。
- `tests/month_fair_preflight.cjs`：在編譯前檢查整月密集資料、八行協議，以及「兩名虛構人員分兩班、理論最公平偏差應為 0」的小型算例。**此步是資料與 JS 語法預檢，不是真正 C++ WASM 求解。**

## 真正 WASM 新實驗（不能先宣稱成功）

- [Full-month two-stage fair CP-SAT WASM experiment #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216350348) 已真正啟動，使用 Emscripten 建置 `cp_sat_month_fair_bridge` 的單獨 target，並執行 `tests/month_fair_real_wasm.cjs`。
- Node 真正測試要求：完成兩階段小型公平精確算例；密集虛構 372／56 與 217／50，及大門指定整日缺班的反例；每一班獨立審核；若未達第一階段填班數應直接失敗；若公平較第一階段更差也應失敗。對不可行固定雙班應回傳 INFEASIBLE，對非法目標應回傳 INVALID_INPUT。
- **編譯未結束前**，不得宣稱 v3 C++／WASM 已通過、Fairness OPTIMAL 已驗證或已在瀏覽器/iPhone 執行。

## 尚未實作／下一步門檻

- 這個公平目標只計算**每人整月班次總數的絕對偏差**。尚不包括艱苦夜哨（22–06 四個時段分配）、12–14 午間哨、安官長班時數、每週業參的實際工作日分布與其他細部品質。
- 1/3 業參權重是**用來產生軟目標**，不代表已把完整每週業參排程放進 C++ 規則；跨月補償仍需本地資料驗證後才能影響本月目標。
- 真正全月公平 CP-SAT 可能耗時較先前只求最大填班更久；兩階段各設 10 秒上限，若第二階段超時須如實標記 FEASIBLE/UNKNOWN，不得虛構公平最優。
- 真正 iPhone Safari 的單檔載入、RAM／CPU 與使用者操作體驗尚待實機驗收；不能把 Chromium 的手機尺寸模式叫做 iPhone 實測。
- 新版尚未接回 v7.0 網站，也不能處理或核定實際軍務班表。正式使用前仍需完整規則對照與權限／軍網資料保護檢查。

**建議下階段**：以真正 C++ WASM 的編譯與 Node 稽核結果為準修正錯誤；通過後產出獨立公平測試 HTML，再測 Chromium/WebKit，最後進行真實 iPhone 裝置驗收。只要沒有實證，不能把原生 Python 成功當成 WASM 成功。
