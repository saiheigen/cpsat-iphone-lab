# iPhone 離線 CP-SAT 排班實驗室

> **私人實驗專案，尚非可核發的正式軍務班表系統。** 本儲存庫只應包含公開 OR-Tools 建置程式、虛構人員與合成勤務案例。勿上傳真實名冊、休假、夜查、車勤、值勤矩陣或其他敏感資料到 GitHub／Actions。

## 先看哪份資料？

- **唯一當前狀態：** [STATUS.md](STATUS.md)
- **完整工程健檢與精簡順序：** [2026-11-18 專案審查](docs/project-audit-and-simplification-2026-11-18.md)
- **工作分支：** `phase20-budget-safe-rollover`，尚未合併至 `main`；既有 [draft PR #1](https://github.com/saiheigen/cpsat-iphone-lab/pull/1) 的分支仍較舊。

## 已有什麼？

1. **真正的 OR-Tools C++ CP-SAT WASM**：`src/cp_sat_month_hardship_bridge.cc` 為完整月份 v4 合成模型，三階段依序處理合法填班、總班數公平、艱苦勤務；經 Node／瀏覽器虛構案例實測，不等於真實軍務合規。
2. **離線手機測試頁**：`build/package_month_hardship_wasm.py`、`src/phase5_hardship_worker.js` 和 `src/phase5_iphone_selfcheck.js`。使用者回報在 iPhone Files 內嵌檢視器成功測試四組虛構案例；**未獨立驗證 Safari.app**。
3. **規則與完整月份輸入**：`solver/roster_cp_sat.py`、`solver/full_month_wire_v2.py`、`solver/full_month_fair_wire_v3.py`、`solver/v7_backup_bridge.py`。只實作可核對的部分 v7 規則；原始完整 v7 HTML 不在此儲存庫。
4. **階段 20–24 的本機合成實驗**：跨月封存／補償、跨月勤務稽核、匿名 solver 格式、合法預排與公平改善。文件記載 121 項本機測試通過；不是正式 v7 全規則，也不是這份 README 更新時重跑的 CI。

## 現階段最重要的限制

- 密集候選月份使用目前 10 秒第一階段上限，CP-SAT 可能回傳 `UNKNOWN`；**不能把合格預排草案宣稱為真正求解器已完成的班表**。
- 來源封存 `inputSig`、完整跨月規則、授權核定、正式匯出、本地保管及所有原始 v7.0 規則一致性尚未驗證。
- 工作分支包含多個舊編譯、打包和瀏覽器工作流程；**修改某些程式仍可能自動觸發 GitHub Actions**。預算與阻擋超額使用必須在個人 GitHub Billing 設定確認；不會因 README 更新而自動調整。

**工程原則：先驗證 hard rules → 盡量合法填班 → 公平／艱苦勤務 → 獨立稽核 → 人員授權核定。任何階段都不得為了排滿而放寬禁排。**
