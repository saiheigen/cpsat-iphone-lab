# iPhone 離線虛構資料編輯器｜安全模擬整合（2026-11-18）

## 本次做成的產品功能

在**上一階段已通過本機 proof 校驗的真正 C++ CP-SAT WASM 單檔 HTML**中，新增可直接點選的「本機模擬調整」區，保留全部舊版四個測試情境、兩組完整月份預覽、背景 Worker、取消／重啟及同月獨立反向稽核。

手機可選擇**大門／安官 → 12 月日期 → 時段 → 虛構人員 → 額外禁排或指定固定空班**，再按「一鍵求解目前的虛構條件」查看新的填班數、缺班分類及逐日虛構班表。有**撤銷上一項、全部還原**和「**套用示範：10 項禁排**」；所有修改只存在當前頁面的 JavaScript 記憶體，關閉或重新開啟即消失，**不使用 localStorage、不上傳、不提供真實名冊匯入或正式匯出功能**。

## 必須維持的工程不變式

1. 只接受先前 Phase 22/27 來源校驗過、打包在 HTML 中的**虛構** `2026-12` 資料：兩組 589 班，門衛 56 人／安官 50 人。
2. 編輯只能將原始合法遮罩 `1 → 0`，或將原本未固定的 `pin=-2 → -1`（強制空班）。**不得將禁排 `0 → 1`、解除人工固定班、修改固定缺班或更動真正事件來源**；上限 40 項。
3. 每次修改立即使本介面的前次求解與預覽**失效**。求解期間禁止修改、重複求解或採用取消後的舊結果。任一組回傳 `UNKNOWN`、人員違反限制、偽造填班數，則**兩組結果都不採用**。
4. 真正 C++ 返回 `FEASIBLE/OPTIMAL` 後，使用既有 HTML 的独立 `independentlyAudit` 完整檢查選人、同日休息、隔日、相隔兩天同時段、連續週日與艱苦分類。動態的 `expectedFill` 僅等於求解器實際填班數，**不是已證實最優填班數**；增加禁排後不得比原始虛構已證實的 4 班多。
5. 即使本機 HTML 顯示可行結果，也不代表真實 v7 封存、來源 `inputSig`、全部軍務規則或人員核定已驗證；報告仍保留 `operationally_certified=false`、`importable_as_v7_backup=false`、`real_iphone_safari_verified=false`。

## 實際本機驗收與限制

- 原本 Phase 20–24 **121／121** Python 虛構測試、**6／6** UI 打包安全測試通過；Node.js 虛構 UI 狀態測試含新增禁排、固定班保護、撤銷、全還原、快速示範及偽造結果拒絕均通過。
- 用**真正的 C++ OR-Tools WASM** `8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d` 執行四組輸入，全部 `OPTIMAL` 且完成獨立同月稽核：原始大門 **3/372**、安官 **1/217**；將虛構大門 10 個原本合法的候選排除後，大門變 **2/372**、安官維持 **1/217**。**這只是刻意極度稀疏的 589 班虛構驗收，不是正常月份的填班率或性能。**
- 以 390px 手機寬度在 headless Chromium **只有編輯器面板**做 DOM 點按：新增／撤銷、無 JavaScript 頁面錯誤；此瀏覽器測試**故意使用 mock solver**，不能當真正 WASM 或 Safari 實機證據。
- 原始 **9.5 MB 單檔 HTML**已經用具源頭 SHA-256 校驗的真正原版 Emscripten JS/WASM 重打包，新產物 HTML SHA-256 可見於本機 release manifest。執行環境限制 Chromium 的 `file://` 導覽，**尚無新完整 HTML 的實際瀏覽器／實體 iPhone Safari 驗收**。
- **沒有重新編譯 C++，沒有呼叫 GitHub Actions，沒有接觸或上傳真實軍務資料。**

## 開發與手動發版的路徑

- `src/fictional_iphone_e2e_ui.js` 與 `build/package_fictional_iphone_e2e.py`：既有 proof-gated HTML 上的新模擬編輯器，保留舊介面和 WASM。
- `tests/test_fictional_iphone_e2e_ui.cjs`：Mock solver 的純 UI 邏輯、偽造／`UNKNOWN` 與限制回歸。
- `tests/test_package_fictional_iphone_e2e.py`：不依賴真正 WASM 的六項打包負面測試。
- `tests/real_fictional_whatif_wasm.cjs`：**只在手動發版**執行，使用之前已編好的真正 v4 WASM 和簽名雜湊／來源證據，跑原始＋示範限制兩個 pool，獨立稽核並生成只含虛構摘要的 JSON。
- `ci-fast.yml`：只做 JS 語法、UI／Python 小型測試；**不自動編譯或執行真正 WASM**。
- `package-month-hardship-wasm.yml`：仍為手動啟動；打包原本 `dist/iphone_fictional_crossmonth_e2e.html` 後，加做真正 WASM 的改前／改後求解，附上 `proof/real_fictional_whatif_wasm_smoke.json`。新的 HTML 會保留原本的檔名，供舊測試流程繼續定位；後續 release 應使用新版本號管理。

## 使用步驟

下載本次交付的 `iphone_fictional_whatif_offline.html`，在 iPhone 的檔案檢視器開啟後，展開「🧪 本機模擬調整」。可以直接按示範按鈕套用十項虛構禁排，再按「一鍵求解目前的虛構條件」，對比原始 **4/589** 和示範 **3/589**。如果檔案預覽器沒有啟用 Worker，會退回原本的主執行緒求解模式，可能短暫失去回應；不能把這種模式宣稱成可中斷運算。操作前務必分清楚是**虛構驗收工具**。

## 仍未完成

真正正式 v7 HTML、`inputSig` 新鮮度、跨月封存核定、完整 leave／車勤／夜查業務規則以及真實資料本機保存／加密／正式輸出，均未取得可用於實務核發的證據。GitHub 目前仍是 private 開發分支，**尚未合併 `main`，CI 雲端未驗證**。真正 iPhone Safari 的離線持續運作仍需使用者在實機自行測試。正式軍務發版狀態：**BLOCKED**。
