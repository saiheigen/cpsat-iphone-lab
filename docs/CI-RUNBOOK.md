# CI ／交付整併作業手冊（2026-11-18）

## 預期成果（必須合併到 main 後才會實際生效）

- 候選分支 `phase20-budget-safe-rollover`：**31 條舊版工作流程全部改為 `workflow_dispatch`**，原有 job 和驗證腳本仍保留，沒有刪掉過往實測的證據。
- 新增唯一一般自動入口 `.github/workflows/ci-fast.yml`：僅 `main` 的相關檔案 push，或以 `main` 為目標的 PR，執行虛構 JS／Python 快速測試；設定 `concurrency.cancel-in-progress` 與 job 超時 7 分鐘。這是超時上限，不是預估實際分鐘數。
- `tools/check_ci_budget.py` 在 fast CI 中強制拒絕其他 workflow 偷偷新增 `push`、`workflow_run`、`schedule` 等自動觸發。這是**原始碼策略**，不是使用者帳戶的超額帳單防護。
- 現用 Phase 5／19 的四條 genuine v4 WASM 測試不再固定抓舊執行編號 `44223914115`，需要填入明確的 `source_run_id` 才能重新測試（如原本含有來源 proof 檢驗，依舊保留）。
- 測試用 Actions checkout 與 setup-node 採用**透過 GitHub 官方 tag API 核對的完整 commit SHA**；既有 31 條舊工作流程仍有 tags 和浮動 OR-Tools `stable`，尚待版本化改造。

## release 操作順序（使用的都只能是虛構資料）

1. 確認 `main` 已合併並通過 Fast synthetic regression；本次審查**不會自動合併 main**。另外檢查 GitHub 帳號 Billing/Budgets，限制可計費工作流。
2. **手動**執行 `cp-sat-wasm-harsh.yml`，成功後保存這次的 run ID、GIT SHA、OR-Tools upstream SHA 及產出的 JS/WASM/proof hash。
3. **手動**執行 `package-month-hardship-wasm.yml`，`source_run_id` 指向第 2 步**已成功**的編譯。重新運行真實 Node WASM + proof hash，成功後保存新的 package run ID。
4. **手動**執行 `browser-month-hardship-wasm.yml`，`source_run_id` 指向第 3 步**已成功**的打包。這只能證明 Chromium／Linux WebKit 合成測試，不等於實體 iPhone Safari。
5. 如要測整合，手動執行 `phase5-real-wasm-integration.yml`、`phase5-offline-ui-e2e.yml`、`phase5-offline-webkit.yml`、`phase19-fictional-v7-hard-rule-gate.yml` 並輸入第 2 步 WASM 編譯 run ID；如果 proof 不符，必須失敗而不是自動改抓其他來源。

## 不可跳過的限制

- **GitHub 的 `workflow_dispatch` 必須存在於預設分支**才能在 Actions UI 手動啟動。這些變更目前只在開發分支，**尚未控制 main 的舊自動觸發**。
- 原先 `workflow_run` 串接是自動的；現在改成顯式手動交接，避免同一提交反覆啟動昂貴測試。**發布前要確實跑完必要手動 gate**，不能只看快測試綠燈。
- `source_run_id` 是來源線索，**不是數位簽章**；下游還必須驗證傳入產物的真正 Node／WASM 內容及 proof，正式版需鎖定 OR-Tools commit 並建立可重現的 artifact 發行機制。
- GitHub private repo 的付款設定、branch protection／rulesets 並未修改；Free 計畫對私有儲存庫的 branch protection 能力可能受限，不應為此把軍務專案改成公開。
- 原始 v7 HTML、`inputSig`、正式授權核定、跨月全規則與實體 Safari 測試仍然缺少。**正式軍務發版狀態：BLOCKED**。真實人名、勤務日期、休假和輸出備份絕對不能提交 GitHub／Actions。

## 本次無計費驗證

執行 `python3 tools/check_ci_budget.py`、`python3 -m unittest discover -s tests -p 'test_ci_budget_policy.py' -q` 和既有本機虛構回歸測試。GitHub Actions 的真正運行需要在適合的預算與授權下另行啟動，不應宣稱本次改動已取得雲端 CI 證明。
