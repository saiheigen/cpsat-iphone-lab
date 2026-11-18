# 排班網站專案全面工程審查與精簡建議（2026-11-18）

> 對象：私人 GitHub `saiheigen/cpsat-iphone-lab` 的 `main` 與 `phase20-budget-safe-rollover`。
> 本次是**原始碼與 GitHub workflow 的結構審查**，沒有重新執行全套 CI、重新編譯 WASM 或取得原始 v7.0 HTML。所有已完成測試都依附既有 GitHub 工作紀錄和階段文件；不能推論正式軍務排班已可使用。不得把真實人員、夜查／車勤／休假、勤務矩陣或軍務備份提交到 GitHub。

## 1. 已核對的專案現況

| 項目 | 可驗證觀察 |
|---|---|
| GitHub 儲存庫 | **private**，預設分支為 `main` |
| main | 24 個歷史 GitHub Actions workflow；README/STATUS 多數仍描述最早期算術／兩變數 CP-SAT smoke test |
| 工作分支 `phase20-budget-safe-rollover` | 31 個 workflow，32 個 docs，18 個 `solver/` Python 檔，46 個 `tests/` 檔；對比 main **ahead 105、behind 0**（本審查前） |
| PR #1 | 仍為 draft，指向較早的 `phase5-safari-integration-gates`，**沒有包括新的 phase20–24 分支頭** |
| 真正 C++ CP-SAT WASM | v4 三階段合成案例：原有 GitHub 成功證據 [#44265577734](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44265577734)；不能外推所有正式規則 |
| iPhone | 使用者以 Files／嵌入式 WebView 回報真正 WASM 虛構案例成功；**沒有獨立驗證 Safari.app，也沒有官方離線狀態儀器證明** |
| 階段 20–24 | 階段文檔記錄 **121 個本機虛構測試通過**；不是這次重新執行 GitHub CI |
| 密集 C++ 求解 | v4 第一階段寫死 **10 秒**；第 23／24 階段的密集虛構衛哨案例約 10 秒 `UNKNOWN`，即沒有可信可交付的求解器結果 |
| 正式 v7 | 原始 v7.0 HTML **不在目前儲存庫**，`inputSig` 實際新鮮度、授權封存與全規則一致性**未驗證** |

## 2. 應優先修正（按風險排序）

### P0｜把 GitHub Actions 整理成低費用流程

**確定現象**：提交 `b179867c9d699cf6065ccc9247b57f51e6aa92af` 曾同時有 **7 個 workflow runs**。`phase5-offline-ui-e2e.yml`、`phase5-offline-webkit.yml`、`phase5-real-wasm-integration.yml`、`phase19-fictional-v7-hard-rule-gate.yml` 等具有 `push`＋`pull_request` 事件且多數無 cancel-in-progress。`cp-sat-wasm-harsh.yml` 及同類編譯流程保留 **120 分鐘**的單一 job 上限；這是超時上限，不是每次一定消耗 120 分鐘。

**建議方案**：
1. 保留一個「一般程式修改」的**輕量單元測試** workflow，設定 `concurrency.cancel-in-progress: true` 並避免同一分支 push/PR 重複。
2. 把真正的 OR-Tools/Emscripten 編譯、WebKit/Chromium 完整驗收改為**手動 workflow_dispatch** 或經明確選擇的 release gate；保留成功證據，勿直接刪掉。
3. 共用固定版本的 genuine WASM artifact + SHA256/reproducible release。下方 static run ID 應改成受控、可追溯的產物版本，而不是只抓特定舊工作 ID。
4. 添加各流程執行次數、runner 實際分鐘數的月度量測，再決定哪些可合併或轉手動；**不要承諾具體節省百分比**。
5. **預算與付款開關是 GitHub 帳戶設定**，此程式變更不會自動設定支出上限；必須由使用者在 Billing/Budgets 檢查。

**安全護欄**：不要讓停用自動編譯順帶停用發版前的必要檢查，也不要將真實資料用於 CI。

### P0｜先完成真正 v7 來源、封存與資料權限核驗，再談正式上線

`solver/v7_backup_bridge.py` 已能處理 v7 類備份資料的一部分，但會明確對未驗證前月 `inputSig`／封存補償拒絕或提出警示。階段 20–24 都是 `SIM_...` **完全虛構**資料；不能替代真正原始 v7 來源驗證。建議先確定：來源版本／輸入簽章、核定操作權限、歷史資料完整性、勤務資格列、手機本地保管與資料回復。**不可把真實敏感資料放進 private/public GitHub 或 Actions。**

### P1｜建立唯一可信的「當前狀態」，處理主分支落後問題

`README.md` 和 `STATUS.md` 仍寫著「尚未取得 GitHub Action 綠燈」與「真正 CP-SAT WASM 未完成」，和後續 synthetic 實測不一致。建議改為簡單四層驗收表：**模型單元測試 / 真正 C++ WASM / 實體手機測試 / 正式 v7 授權軍務整合**，每層只引用具體證據。主分支落後約 105 個提交，PR #1 只到 phase5；應整理審查範圍，分批合併有證據的核心修改，而非把大量歷史實驗一次性合入 `main`。

### P1｜修正程式層級依賴與協議不一致

- `integration/phase5_synthetic_adapter.cjs` **直接 require `../tests/month_real_wasm.cjs`** 取得 `independentlyAudit`。可先抽出 `integration/shared_month_audit.cjs` 或 `lib/` 可重用的純稽核函式，原測試改用同一庫；額外保留獨立 Python 反向稽核，避免只靠同一份實作驗證自己。
- `integration/phase5_synthetic_adapter.cjs` 限 `staff <= 100`，`solver/full_month_wire_v2.py`／v4 C++ 允許 **106 名／池**。當前 56／50 人未受影響，但這是明確的協議上限不一致，應提取單一 versioned contract 並加 100、101、106、107 邊界測試。
- `solver/roster_cp_sat.py` 和 phase21 等獨立 auditor 有重複時間／衝突規則；**不應盲目合併到同一個核對器**（會失去獨立性）。應以固定規格、共同虛構測試基準與跨語言差異測試（Python vs JS vs C++）確保沒有語義漂移。
- `src/CMakeLists.txt` 有 5 個歷史 WASM targets，鏈結參數與封裝設定重複。可定義共用 CMake 函式再分別產生 targets；先跑等價性和 artifact checksum/解碼測試再更換 release 管線。

### P1｜不再把「快」當作主要解鎖條件

第 23／24 階段的合法合成預排，可以保持填班 **587/589** 並將 **L1=12 → 8**，但那是 heuristic preview，**並非求解器已驗證成功**；v4 C++ 在密集案例 10 秒回報 `UNKNOWN`。建議設計**分階段可設定時間上限**（例如 15–60 秒作為待測設定，不是現有性能事實），在 Worker 上持續顯示進度、允許取消；未知結果嚴禁冒稱合法已批准的班表。優先驗證填班合法性，再嘗試公平與艱苦最適化；把實際 iPhone 電力、前景／背景、記憶體狀態列入驗收。

### P2｜收斂階段性實驗文件與重複建置

- 舊 `stage1–stage19`、`phase5`、`phase19–24` 等文件保留歷史依據，但把主頁收斂為一份可維護的 `STATUS.md` + 一份「全規則驗收矩陣」。
- 把 v1 固定數學 probe、v2 完整填班、v3 公平兩階段與 v4 三階段版本明列為 **legacy experiments vs current candidate**；先封存，再評估刪除，不宜逕行刪除能復驗的 provenance。
- 包裝器與測試物件應明確區分：虛構驗收測試、合格預排候選、真實 WASM 回傳且重新稽核的班表、已核定可發布班表。不要混用 `accepted`／`verified`／`operationally_certified`。

## 3. 必須保留的部分

- 真正 OR-Tools C++/WASM 及 Node/Chromium/WebKit 的既有**可查證實測**，不回退為純 JS 假解。
- 法規／勤務 hard constraints 優先於公平、缺班明列，禁止自動放寬。
- 單一月份完整欄位、兩組勤務獨立 pool、跨月事件／歷史反向檢查。
- Worker、WASM 驗證、離線單檔打包、取消／重啟、錯誤隔離與獨立後驗驗證。
- 過期／未鎖定／不完整封存拒絕、人工固定班次不變、成本控管及真實勤務資料不出本機。

## 4. 建議的新「5 個子系統」架構

1. **Local Input/Archive**：原始 v7 授權轉換、資料完整性、輸入版本、封存鎖定、使用者權限。
2. **Rules & Availability**：唯一的版本化規則清單；由本機規則編譯成匿名候選矩陣、人工固定、歷史邊界，保留**獨立**規則稽核實作。
3. **Solver**：現有 v4 genuine CP-SAT WASM、分階段填班/公平/艱苦處理、可取消的 Worker 和設定過的時間上限。
4. **Independent Audit**：原始事件與完整回傳班表逐筆核對；狀態證據分離；不可把 `UNKNOWN` 當合格排班。
5. **Mobile UI/Export**：真正離線 iPhone 操作、本機存檔、明示缺班／理由、核定前預覽、批准後才輸出正式版本。

## 5. 最小修改順序（不要再次演變成無止境階段）

| 順序 | 一次性可驗收工作 | 不觸碰的部分 |
|---|---|---|
| 1 | 修 README/STATUS；列出唯一最新版與四級驗收狀態 | 不改求解器 |
| 2 | 縮減 CI 重複觸發並保留手動全量驗收；先量測費用 | 不關閉必要發版 gate |
| 3 | 抽出 JS 稽核庫，統一 100/106 人員上限 | 不刪現有有效測試 |
| 4 | 鎖定 canonical v7 規格與來源完整性，補齊 differential tests | 不使用真實機密資料上雲 |
| 5 | 改可設定的求解階段預算與安全輸出語義 | 不把 heuristic/UNKNOWN 視為真正解 |
| 6 | 達成經核准的實機離線演練後，整理主分支與發版流程 | 不一次合併無驗證原型 |

## 6. 本次審查動作與聲明

- 僅使用連線 GitHub 取得既有 repository metadata、compare、README/STATUS、流程 YAML、Python/C++/JS 原始碼與階段文件。
- **未執行新編譯、未改 GitHub Budgets、未上傳任何真實人員資料、未自動停用 CI 工作流程。**
- 以上是經證據支持的程式審查和待辦計畫；**沒有聲稱第 1–6 項修改已完成。**
