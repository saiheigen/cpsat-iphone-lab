# iPhone 單檔離線介面：一鍵虛構跨月整合驗收（2026-11-18）

## 交付內容

本階段**不新增求解器**、不修改 C++ / Python hard rules，不允許輸入實際勤務或私人資料。只使用之前已驗證的真實 C++ OR-Tools CP-SAT WASM 單檔 HTML 作為基底，插入一個新、獨立的手機操作區塊：

- 一鍵先解「大門衛哨」再解「安全士官」，使用兩份由 Python Phase 22/27 虛構跨月來源產生並驗證過、內嵌在頁面的完整月匿名 v4 frame。
- 沿用基底 HTML 已有的 `solveWithMode`、原本的背景 Worker、90 秒等待防護、主執行緒退路、取消／重啟和同月 `independentlyAudit`，不另外製作假求解器。
- 兩個 pool 必須各自得到 `FEASIBLE` 或 `OPTIMAL`，並通過獨立 JS 勤務資格、人工固定、同日間隔、隔日、兩日同時段與週日留守規則，**才會顯示雙勤務結果**。其中任一回傳 `UNKNOWN`、不合法或取消，全部拒絕。
- 逐日切換大門／安官班次；缺班只歸類為 **固定缺班、候選為零、還有候選但未填班**。不能由候選遮罩反推出確切休假／車勤／夜查原因，因此不編造理由。
- 只輸出彙總的虛構求解狀態；沒有真名、原始備份匯入、上傳網路、核定班表或可被正式 v7 匯入的按鈕。

## 檔案

- `src/fictional_iphone_e2e_ui.js`：新增手機 UI 互動、日期／勤務切換、缺班分類、求解與取消／重啟安全狀態。
- `build/package_fictional_iphone_e2e.py`：對**原有單檔 HTML**內含的 6.9MB genuine WASM 及原始 Emscripten JS 做 SHA-256 驗證；要求之前 proof 的 WASM/JS SHA 逐 byte 一致；要求 Phase 27 原始虛構來源的 **589 班、4 填 585 缺**、兩組 frame SHA 與本機獨立跨月稽核相符。任何不符直接拒絕。
- `tests/test_package_fictional_iphone_e2e.py`：6 個虛構／微型假 WASM 安全打包測試（**不能視為真實 WASM 成功證據**）。
- `tests/test_fictional_iphone_e2e_ui.cjs`：Node DOM 模擬測試，涵蓋成功、清空、`UNKNOWN` 及偽造填班數。正式 CI 依然只使用虛構資料。
- `ci-fast.yml`：加入 UI 腳本語法、Node DOM 模擬及打包測試。
- `package-month-hardship-wasm.yml`：**手動觸發**的、原本完整 WASM 證明後的打包流程，額外執行 Phase 27 真實 Node WASM + 原始跨月 Python 稽核，再產出 **第二個** `iphone_fictional_crossmonth_e2e.html`。原 `experimental_full_month_hardship_cp_sat.html` 沒有被覆寫或取代。

## 本機已核對

- 使用前期已驗證的真正 v4 C++ WASM，SHA-256：`8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d`，重新求解 **大門 3/372、安官 1/217，兩組 `OPTIMAL`**，原始現有網頁 JS audit 也通過。
- 真正 WASM 的 JS glue SHA-256 和打包證據逐 byte 相同；整個 6.9MB WASM 從已打包 HTML 解碼後重新計算 SHA-256，再對照已保存的來源證據。
- 新增 6/6 Python 打包測試、3/3 Node UI 狀態測試通過；人工竄改原始二進位、證據、虛構來源 SHA、重複注入時均會拒絕。
- 單檔 HTML 在本機實際產生並通過 Node JavaScript 語法檢查。**Playwright/Chromium 的瀏覽器測試因執行環境對 `file://` 和 localhost 導航的限制，改用大頁注入亦未完成，不能宣稱實體 iPhone Safari 或新頁面瀏覽器自動驗收通過。**

## 執行與發版限制

`build/package_fictional_iphone_e2e.py` 僅可在已完成 genuine WASM proof 與 `tools.fictional_offline_pipeline`（虛構來源）的前提下產生新檔案。直接使用 `--wasm` 等任意上傳參數或使用實際軍務封存皆不支援。

本次只在 `phase20-budget-safe-rollover` 開發分支提交；**主分支和 GitHub Billing 未調整**。新的 `package-month-hardship-wasm.yml` 仍需先將相關程式經審查合入預設分支，才可在 Actions UI 正常手動選擇執行。

**正式軍務部署：BLOCKED。** 真正 v7 原始 `inputSig`、前月封存核定與權限、全規則一致性、密集月份求解及實體 Safari.app 仍未完成驗收。
