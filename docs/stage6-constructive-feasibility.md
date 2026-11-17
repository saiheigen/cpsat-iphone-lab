# 排哨 CP-SAT｜第 6 階段：處理「有合法班表卻搜尋 UNKNOWN」

2026-11-18（台灣時間）；所有人員編號、休假、車勤及跨月資料均為合成範例。

## 真正找到的瓶頸

同一組 2026/12 合成資料：大門 372 班、安官 217 班，56 名 H 人員、50 名 P 人員，另外加入 34 筆合成休假／受訓／夜查／車勤／值星／督伙／免哨資料，以及 4 筆跨月歷史。

**第一版：** https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44129295716

- 大門：滿班可行性 CP-SAT `UNKNOWN`，最大填班回退 CP-SAT 亦 `UNKNOWN`，未取得可行排班結果。這不是已證明人力不足。
- 安官：217/217 班、原生 CP-SAT `OPTIMAL`。
- 最終回報 `INCOMPLETE_NO_COMBINED_SCHEDULE`、filled=null，避免把未知結果寫成合法缺班或核定班表。

## 針對性修正

新增 `solver/constructive_witness.py`：
- 以同一組硬限制與歷史班次產生可能的合法初稿；**先尊重人工固定班次**，再處理每天候選人，所有結果均通過獨立 Python 檢查。
- 初稿若只填部分班，只能是合法的 FEASIBLE incumbent，**不代表最大填班最優**。
- 初稿若完整填滿，則由「每班最多一人」的簡單上界證明該模型**最大填班數**已達成；不代表此初稿的公平分數最優，也不代表軍務全部規定已完成。
- 不得自動放寬休假、同日休息、站一歇一、車勤、值星、夜查、同時段與人工固定等強制限制。

更新 `solver/split_fill_cp_sat.py`：
- 將合法初稿作為原生 CP-SAT 的 hint。
- CP-SAT 若 `UNKNOWN`，但已有**獨立通過的完整初稿**，可以保留該初稿並明確記錄 `solution_source=independent_constructive_witness`，`full_feasibility=UNKNOWN`；不得宣稱 CP-SAT 已自行取得 `OPTIMAL`。
- CP-SAT 若 `UNKNOWN` 且初稿只填部分班，保留部分合法班表並標記 `PARTIAL_FEASIBLE`，不宣稱真實缺班已無解。
- CP-SAT 真正得到 `OPTIMAL` 時，會核對結果不得比已知合法初稿更差。

## 修正後整月合成實測

**第二版：** https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44130044327

- 總計：**589/589 班**、0 缺班、執行約 **32.526 秒**，符合目前已建模硬限制。
- 安官：**217/217 班**，原生 CP-SAT 真正回傳 `OPTIMAL`，約 11.472 秒。
- 大門：**372/372 班**，CP-SAT 滿班可行性仍為 `UNKNOWN`；完整合法方案來自**獨立構造並審核通過的初稿**，不是 CP-SAT 求解器已證明 OPTIMAL，約 21.047 秒。
- 結果的整月「最大填班數」可透過已實際填滿所有班次及每班最多一人的上界證明；**公平、補償、真實軍務規則並未取得最優證明**。
- 下一次回歸已加入 `solution_source` 顯示，讓報告不只說 589/589，也指出各池實際採用哪一種來源。

## 其他測試與銜接

- `tests/test_constructive_witness.py`：合法初稿、人工固定、跨月歷史、禁排、人力不足時不假稱最優等，GitHub CI 成功。
- `tests/test_split_fill_cp_sat.py`：補上刻意模擬 CP-SAT `UNKNOWN` 的回歸，驗證完整初稿及部分初稿的狀態不能混淆。
- `solver/v7_preview.py`：現有網站的 `[Unix 日序號, 班號, 編號或空白]` 格式只提供**不可匯入正式備份**的安全預覽，尚未接入 v7 網站。

## 最重要的剩餘限制

1. 真正 C++ OR-Tools CP-SAT → WASM 的針對性編譯仍需成功、通過 Node 獨立數值驗證、產生 iPhone HTML 並用手機實機驗收。
2. 合成樣本包含部分真實規則類型，但不代表模擬了所有特殊勤務狀態與完整跨月自動補償。
3. 當全滿可行性不確定時，**絕不可把 UNKNOWN 當成 INFEASIBLE**，也不得把構造解稱作 CP-SAT 已成功產出 OPTIMAL。
4. 新求解器目前仍是 Python 原生工程原型，不是手機端可用的完整排班產品；本階段不應上傳實際軍務人員資訊或勤務表到 GitHub。
