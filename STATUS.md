# 專案唯一現況（2026-11-18）

**分支**：`phase20-budget-safe-rollover`（未合併 `main`；[draft PR #1](https://github.com/saiheigen/cpsat-iphone-lab/pull/1) 的 head 為較早的 `phase5-safari-integration-gates`）。

**定位**：具備真正 OR-Tools CP-SAT WASM 虛構案例求解能力的離線手機工程實驗，**未取得正式 v7.0 軍務全規則與核發認證**。

| 層級 | 有證據的現況 | 尚缺 |
|---|---|---|
| 原生／C++ CP-SAT WASM | 三階段 v4 求解器對指定虛構案例實際執行與稽核成功；例 [Phase 19 CI #44265577734](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44265577734) | 不等於所有密集月份、所有 v7 規則都驗證 |
| 瀏覽器／Worker | 部分合成 Chromium／WebKit 真正 WASM 測試已成功，具離線 Worker 與取消／復原處理 | Linux WebKit ≠ 真正 Safari.app |
| iPhone | 使用者提供從 **Files app embedded-webview** 開啟的合成四案例 JSON 與 589 行預覽結果，四案例成功、預覽填 577／589，0 件觀察到的 JS unhandled error | 不能宣稱獨立驗證 Safari.app 或真正 Wi-Fi／行動網路同時中斷 |
| 完整月規則橋接 | 第 19 階段完整虛構月份 589 行輸入、事件資格與獨立反向稽核通過 [CI](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44265577734) | 尚未驗證正式 v7 `inputSig`、原始 HTML 規則完全一致及核定封存 |
| 階段 20–24 | 階段紀錄中的本機**虛構**測試：16+33+24+24+24＝**121 項通過**；合成合法預排 587／589，L1 偏差 12→8 | 僅 heuristic 合法預覽，不等於 C++ solver 求得最優公平或真實軍務合格 |
| 密集月份效能 | 第 23／24 階段真正 C++ WASM 的密集衛哨案例約 10 秒回傳 `UNKNOWN` | 沒有可靠已求出的班表；安官同次大規模效能測試未完成 |
| 生產資料與發版 | Repo 為 private，程式與實測案例是虛構；有嚴格的 `operationally_certified=false` 等標記 | 原始 v7 來源授權、資料來源完整性、核定輸出與離線存儲安全 |

**前次報告所寫的「尚無任何 CP-SAT WASM 成功」已不適用。** 同樣地，任何合成測試通過也**不能**升格為正式軍務安全驗證。

## 接下來最值得做的事

1. **控制 GitHub Actions 成本**：31 個工作流程中有重複 push／PR 觸發；工作流程重整前，避免為小修改頻繁執行昂貴 WASM 編譯。GitHub Billing 的實際支付保護不在本儲存庫內設定。
2. **修理 JS 整合邊界**：不再從 `tests/` 匯入上線候選程式使用的稽核工具；統一 C++／Python／JS 的人數與協議上限。
3. **完成權威 v7 原始規則與封存核對**：來源真實性、完整性、`inputSig` 與授權使用；公開 GitHub 不得包含敏感人員／勤務資料。
4. **在合理時間預算下查驗真實求解結果**：可研究提高目前 10 秒限制，保留 fail-closed UNKNOWN 語義。
5. **清楚區分歷史實驗與目前產品入口**：暫不刪除可復驗的 v1／v2／v3 C++ 模型與成功證據，避免一次合併所有未核實的新程式。

完整證據、具體優先級與建議新架構請見 [專案全面審查](docs/project-audit-and-simplification-2026-11-18.md)。

**Release gate：BLOCKED。** 不可使用本實驗代替經核定的正式排班、不可宣稱真實 iPhone Safari 驗證，也不可把任何真實軍務資料提交至 GitHub Actions。
