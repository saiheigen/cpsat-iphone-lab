# 第 13 階段：不再等待整月 WASM 編譯，先補 v7 公平配額與跨月補償

日期：2026-11-18（台灣）。測試使用完全虛構人員與日期，不含真實軍務資料。

## 重大編譯里程碑：已查證成功

- [Full-month CP-SAT WebAssembly experiment #2](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206220771)：**success**，真正 C++ → WebAssembly，Node 直接執行 2026/12 大門 372／56 人、安官 217／50 人的合成完整月模型，並核對同日間隔、站一歇一、週日留守及固定衝突反例。
- [Package proven full-month CP-SAT WASM demo #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44210728760)：**success**，真正 Node WASM 重跑、SHA-256 與獨立規則驗證後打包 HTML。
- [Real offline 589-shift CP-SAT WASM browser acceptance #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44210761468)：**success**，離線桌面／手機尺寸 Chromium 真正執行 WebAssembly，核對完整月份與衝突反例。**不是 iPhone Safari 實機驗收**。
- 此月度滿班 witness 是刻意讓每班**只有一名候選人**的簡化模型。成功說明引擎、協議和現有部分硬限制可在 WASM 執行，**沒有證明 589 班密集候選或全體真實軍務條件的效能與正確性**。

## 本次新增：逐行依 v7.0 原始碼核對的公平計算模組

本次重新直接閱讀 Project 原始檔《哨務工作台_v7.0_一鍵整月自動最佳化版.html》：
- `calcGoals`（約第 886 行起）：以「靜態合格候選班數 × 人員權重」為比例，按最大餘數法整數分配全部班數；小數餘數相同時按原名冊順序。候選次數不是考慮休息後的實際可達班數。
- `calcActualTargets`（約第 900 行起）：基本目標減去前月 carry 與本月督伙 mealCredit，再把可轉移的班數優先分給沒有補償而仍有候選容量的人；必要時仍可排給已有補償的人。這是**軟性建議值**，不是人員禁排、硬配額或保證滿班。
- `toggleArchive`（約第 3391 行）：封存快照的待減班數為 `max(0, trunc(已站班+督伙折抵+前月待減-基本配額))`，只結轉正數，不追討欠班。
- 自動前月 carry 只有在前月**已封存且資料未過期**時才採用，手動輸入優先。此規則是來源／狀態檢查，不應由外部模型自行假定前月已核准。

新增 `solver/fairness_targets_v7.py`：
- `base_goals_v7`：整數基本配額與名冊順序 tie-break。
- `actual_targets_v7`：督伙、前月補償減額與剩餘班數再分配。
- `archive_compensation_out_v7`：跨月補償快照（只正向結轉）。
- `import_prior_locked_carry_v7`：手動覆蓋、自動封存與資料過期安全判斷。

新增 `tests/test_fairness_targets_v7.py`：測試 1/3 權重、最大餘數、補償的優先級、督伙相加、前月未封存／已過期、手動覆蓋 0、補償者在其他人沒有容量後仍可被排、不可虛構缺班解、非法輸入拒絕。

## 本次新增：兩階段原生 CP-SAT 公平優化原型

新增 `solver/lexicographic_count_fair.py`：
1. 第一階段**最大化合法填班數**，包含所有原先 `prepare()` 的硬限制。
2. 第二階段重新用同一份 `prepare()` 建模，施加「填班數 = 第一階段已取得填班數」的硬限制，只優化每個人的 **L1 班數偏差**。
3. 全部輸出仍以 `independently_check()` 重新驗證；若第二階段無法找到解，保留第一階段合法結果，不能憑空降填班數或放寬休假、跨月、休息及人工固定。
4. `OPTIMAL`、`FEASIBLE`、超時與「只證明在特定填班數下的公平最優」分開標示，避免誤宣稱完整月全域公平最優。
5. 暫不含艱苦哨分配、安官 6 小時長班、業參的每週分布及完整補償跨月動態平衡。

新增 `tests/test_lexicographic_count_fair.py`：雙班公平、誤設目標也不降低覆蓋率、人工固定、休假、站一歇一、強制缺班、錯誤目標拒絕。

### 真正 CI 結果

[Native & baseline CI #106](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44211875616)：**全部 success**，其中：
- 「Verify v7 fairness share targets and archived 1-to-1 credits」success；
- 「Test lexicographic native CP-SAT coverage before soft count fairness」success；
- 「Run real native CP-SAT OPTIMAL test (NOT WASM)」success；
- 基本 WASM baseline success。

先前 #101 的一項測試對補償者完全免排做了錯誤假設，已依來源修正；#105 因 YAML 步驟名稱未加引號包含冒號而解析失敗，也已修正。以 #106 的有效完整 CI 驗證結果為準。

## 仍不可宣稱與下一輪工程順序

- 現在 Python 的公平算術和小型「先最大合法填班，再改善班數公平」已實測，但**尚未移植到整月 C++/WASM**。
- 已通過 589 班 WASM 的是**稀疏虛構 witness**，沒有實測真實休假密集度、複雜補償、跨月歷史、艱苦哨公平或 iPhone 長時間負載。
- 正式優先順序：**密集候選與各類禁排的合成 589 班 WASM 壓力測試 → 兩階段公平在 C++/WASM 的實作與驗證 → 艱苦哨、業參、長班分布 → 真正 iPhone Safari 實測 → v7.0 正式接入前完整安全稽核**。
- 不直接上傳真實姓名、值班日期或由真實軍務推導的資格矩陣到 GitHub。
