# 排哨 CP-SAT｜第 5 階段：缺班安全回退與 v7 預覽銜接

更新：2026-11-18（台灣時間）

## 工程實作（不是正式排哨產品）

1. 新增 `solver/split_fill_cp_sat.py`：在目前模型的兩個勤務池與人員集合完全獨立的前提下，**分池**呼叫原生 OR-Tools CP-SAT。
   - 第一段施加「所有班次都必須有人」作為滿班可行性測試，並用原本的所有硬限制求解。
   - 若得到可行滿班，獨立 Python 審核後以一班最多一人、全班都有人的上界證明填班數已達最大；即使底層狀態僅 FEASIBLE，也不會虛構其底層狀態為 OPTIMAL。
   - 若第一段 INFEASIBLE 或 UNKNOWN，必須重新建立模型**移除滿班限制**，改求最大合法填班數；不能放寬休息、休假或人工固定班次。
   - 若求解第二段超時但找到 FEASIBLE，只報 PARTIAL_FEASIBLE，不能聲稱已證明全部缺班不可補；只有第二段 OPTIMAL 才報 PARTIAL_OPTIMAL。
   - 若任何勤務池沒有可行求解結果，整月不輸出完整班表，以 INCOMPLETE_NO_COMBINED_SCHEDULE 回報；防止無意把未知結果寫成空白班表。
   - 含可核對分池的第一階段／回退狀態、缺額及時間；所有輸出註明 operationally_certified=false。
2. 新增 `tests/test_split_fill_cp_sat.py`：驗證滿班、站一歇一、人力不足的缺班回退、夜查、休假、人工固定空白、非法固定、跨月站哨紀錄、輸入錯誤與獨立審核等。已由原生 CP-SAT GitHub CI 通過。
3. 新增 `solver/v7_preview.py`：將已經獨立驗證的排班映射為 v7 的 `[Unix 日序號, 班號, 人員編號或 null]` 形狀，要求整月每個時段都存在、所有人工固定相符且班數／OPTIMAL 狀態前後一致。
   - 刻意標記為 **guard-cpsat-preview-v1**，不是 `guard-offline-v5`，不能作為正式網站備份還原。
   - 不讀寫真實名冊、不使用網路，也不覆寫已封存月份。
   - 新增 `tests/test_v7_preview.py`，回歸違規人員、連日站哨、缺失班次、假成功狀態與人工固定不得被覆寫的情形；GitHub CI 通過。
4. `tests/test_synthetic_bruteforce.py` 更新：將新的分池回退求解器一併與獨立窮舉最大填班值比較。6 組固定不同種子，每組 30 例，總計 180 個虛構小型案例；原生真實 CP-SAT CI 全部通過。
   - https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44129121611
5. 新增 `benchmarks/split_absence_589.py` 與 `.github/workflows/benchmark-absences.yml`：在全部 589 班、106 名完全虛構人員中加入休假、受訓、夜查、車勤、值星、督伙、免夜哨及前月既有班次。這是**獨立效能壓力測試**，其數值必須以 GitHub CI 實際輸出為準。
   - https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44129295716

## 真正 WASM 的狀態與待驗證門檻

- 前次 OR-Tools 全功能編譯因不需要的命令列工具使用不相容的訊號處理器而失敗。
- 目前針對性 WASM 流程只編譯 `cp_sat_probe` 與必要依賴。這一步雖已有 CMake 設定通過，但需要**完成 C++ 編譯、Node 跑出真的 CP-SAT OPTIMAL 並通過獨立數值核對**，才能打包手機 HTML。
- 該流程進度：https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126438247
- 測試通過的原生 Linux Python OR-Tools **不等於** WebAssembly/iPhone 真正求解已驗收。

## 嚴格不宣稱的內容

- 不聲稱完整軍務排班規定、實際資料與人力充足已驗證。
- 不聲稱 v7 備份 JSON 的來源簽章及跨月補償已於此 Python 求解器獨立重現。
- 不聲稱「第一段滿班求解 INFEASIBLE」與「搜尋超時 UNKNOWN」相同。
- 不聲稱分池必然適合未來新增的跨池互相限制；若加入跨池共享人力或聯動規則，必須重新審查拆分等價性。
- 不上傳任何真實軍中勤務名冊、勤務紀錄到 GitHub；CI 使用完全虛構資料。

## 下一個有意義的門檻

優先取得真正 CP-SAT WASM 的 Node 數值驗證成功；同時檢查帶有多種虛構禁排的整月效能與缺班結果。接著在本機將全規格獨立審核器與 v7 正式網站安全整合，而不是直接把預覽當成已核定的正式排班。
