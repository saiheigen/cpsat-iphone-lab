# CI 費用保護與 JS 獨立稽核整理（2026-11-18）

**分支：** `phase20-budget-safe-rollover`，尚未合併 main。此變更只涉及虛構資料的實驗程式與工作流程，**不動 C++ 求解器、不放寬任何硬限制**。

## 這次實際修正

1. 新增 `integration/month_audit.cjs`：將 `tests/month_real_wasm.cjs` 裡原有的 `HOURS`、`sunday()`、`independentlyAudit()` **原樣搬到可重用的純 JS 稽核模組**。原測試程式仍重匯出 `independentlyAudit`，保持其他既有測試與工具的呼叫介面。
2. `integration/phase5_synthetic_adapter.cjs` 改從真正的 `integration/month_audit.cjs` 讀取獨立稽核；不再在整合層依賴 `tests/`。限制仍以原始合成候選矩陣／固定班／休息規則為準，沒有修改排班資格。
3. 修正 JS 接口每個 pool 的 staff 上限 **100 → 106**；與既有 `solver/full_month_wire_v2.py` 的 `MAX_STAFF=106`、v4 C++ 編碼協議一致。測試 100、101、106 人可編碼，107 人被拒絕；原本的固定缺班、非法指派、同日休息、跨日限制測試保留。

## 這次改成「明確手動」的 10 條工作流程

| 類型 | 工作流程 |
|---|---|
| 舊版基礎 C++ 編譯 | `cp-sat-wasm-experimental.yml` |
| 動態排班 C++ 編譯 | `cp-sat-wasm-dynamic.yml` |
| v2 整月 C++ 編譯 | `cp-sat-wasm-month.yml` |
| v3 公平 C++ 編譯 | `cp-sat-wasm-fair.yml` |
| v4 艱苦勤務 C++ 編譯 | `cp-sat-wasm-harsh.yml` |
| 輕量 JS 整合測試 | `phase5-synthetic-adapter.yml` |
| 現有真正 WASM 整合驗收 | `phase5-real-wasm-integration.yml` |
| Chromium 完整離線頁驗收 | `phase5-offline-ui-e2e.yml` |
| Linux WebKit 完整離線頁驗收 | `phase5-offline-webkit.yml` |
| 虛構事件硬規則 + genuine WASM | `phase19-fictional-v7-hard-rule-gate.yml` |

這十條修改只保留 `on: workflow_dispatch`，保留原有 job、permissions、步驟、驗證與 artifact 規格。**沒有刪掉測試，也沒有將失敗測試改成自動通過。** 更改 trigger 是成本權衡：它們**不會再自動替每個提交驗收**，需要發版前明確重新執行。

**重要剩餘風險**：
- 倉庫其他 **21 條** workflow（包括舊版 `workflow_run` 連鎖下載／打包／瀏覽器測試、以及 `verify.yml`）**未修改**。手動執行舊編譯時仍可能因下游 `workflow_run` 自動觸發其他流程，所以**不能聲稱全倉庫已完全停止 Actions**。
- `workflow_dispatch` 在 GitHub UI 的可用性受預設分支上是否已有相應 workflow 影響；新工作流程若仍只存在開發分支，可能要先整合至 main 或經核准方式部署，才能在 Actions UI 選擇分支手動執行。不要為了點得動而直接把未驗證內容併入 main。
- 多個整合 workflow 目前仍依賴歷史 `run-id: 44223914115` 的 WASM artifact。Artifact 可能過期，且來源不同步會使測試中斷；未來應建立版本化、校驗 SHA-256 的穩定 release 資產。
- GitHub Billing／Budgets／是否允許超額付費是**帳戶層級**，這些 workflow 原始碼變更**不會替使用者設定 $0 付費上限**。
- 如需強制合併前驗證，還必須設定 branch protection／required checks，不能以這次手動化取代必要安全檢查。

## 驗證事實與限制

- 已在本機 Node.js v22 執行新 `integration/month_audit.cjs` 與改版 `integration/phase5_synthetic_adapter.cjs` 的語法檢查，以及原有 phase5 合成整合測試加上 100／101／106／107 人數邊界案例：**通過**。
- 改動中的 JS audit 是從原測試原始碼**逐字抽取、沒有重新設計規則**，因此原本使用的 `tests/month_real_wasm.cjs` 仍保留相同語義及對外導出。未在這次重新跑完整 GitHub CI、瀏覽器整合與真實 WASM 全月驗收。
- 沒有修改 `main`、既有 PR、GitHub Billing，沒有提交實際軍務資料。
- 本地 Node 測試不代表此提交已取得 CI 驗收；進一步 PR／release 前應手動選擇必要測試並明確保存執行證據。

## 下一輪小範圍工作（不是盲目追加功能）

1. 在可控成本前提下跑一輪完整 JS 單元測試和現有獨立 Python 對照，確保新的共用稽核模組行為沒有偏差。
2. 處理剩餘 `workflow_run` 連鎖觸發、長期 artifact 來源與 SHA256 驗證，然後量測實際 GitHub Actions 分鐘。
3. 使用**經授權、只留本機的正式 v7 原始碼**建立來源／封存 `inputSig` 的對照測試，仍不得把軍方資料上雲。

**Release decision: 預覽／實驗性，禁止正式軍務排班部署。**
