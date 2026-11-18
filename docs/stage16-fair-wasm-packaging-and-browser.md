# 第十六階段｜真正公平 WASM 後續驗收管線完成，編譯仍未通過前不得釋出

日期：2026-11-18（台灣時間）。本階段繼續在 `saiheigen/cpsat-iphone-lab` 開發，GitHub 僅存放**虛構**人員／勤務資料，未改動 v7.0 正式班表。

## 已確認的既有成果

- 已通過 [589 班真正 WASM 密集 Node 測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44213148151)：六組虛構 372 大門、217 安官，最大填班皆達獨立 witness 的上限，狀態 OPTIMAL。
- 已通過 [真正離線 Chromium 瀏覽器密集測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44214006711)：桌面和手機尺寸模擬共 12／12 組獨立核對成功。仍**不等於 iPhone Safari 實機測試**。
- [第十五階段兩階段公平 C++/WASM 編譯 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216350348) 正在執行中；目前的成功僅限於 C++ 資料協議與 Python／JS 靜態回歸，**尚無真正公平版 WASM 的成功求解證據**。

## 本輪新增的交付門檻

1. `tests/month_fair_real_wasm.cjs` 增加 `--emit-browser-fixtures`：使用一致的固定虛構範例，輸出兩人兩班、372 大門／56 人、217 安官／50 人、指定空班等四種靜態離線情境；不含真實名冊。
2. `build/package_month_fair_wasm.py`：嚴格驗證真實 OR-Tools + Node WASM 解題的 SHA-256、**兩階段填班優先／公平其次**標記、兩班獨立精確公平 oracle，以及三組完整月份稽核。隨後驗證所有虛構案例的規格、目標向量與人工固定，再把已驗證 JS/WASM 打包成 `experimental_full_month_fair_cp_sat.html`（單檔離線測試頁）。
3. `tests/test_package_month_fair_wasm.py`：**12 項特意使用假的最小 WASM 標頭的打包器測試**，只驗證防錯開關，**不能充當真正 WASM 的求解證據**。包含竄改 hash、偽造 iPhone 驗收、未驗證精確最佳解、非法目標形狀、偷換勤務池、偽造減班與公平反惡化等。
4. [原生／基本 WASM CI #125](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44217969944)：**全部成功**，其中包含新加入的打包器 12 項拒絕測試。
5. `.github/workflows/package-month-fair-wasm.yml`：**只有新公平 C++／WASM 真正編譯、Node 兩階段公平 oracle 及獨立排班檢查都 success 後**，才自動下載相應的 WASM artifact，核對原始 SHA，**再一次真正 Node 求解**，執行打包防錯測試並輸出離線 HTML。若上游失敗，這條路徑不會發布測試頁。
6. `tests/browser_month_fair_wasm.py` + `.github/workflows/browser-month-fair-wasm.yml`：上一步成功後，才用**真實 Playwright Chromium，完全離線**，在桌面及手機尺寸／觸控模擬各點選四個公平版情境，讀取回傳成果、核對填班數、L1 公平偏差及 OPTIMAL／FEASIBLE 分級，留存 JSON 和失敗截圖。依然**不是** iPhone Safari 實機驗收。

## 目前工程狀態

- **已完成**：全月 v3 匿名資料協議、前月補償與督伙折抵衍生軟目標、原生資料安全驗證、真正 WASM 公平核心程式提交、12 項打包防錯測試與編譯成功之後的打包／瀏覽器實跑管線。
- **進行中，未驗收**：[真正公平 WASM #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216350348) 正在編譯 C++；需由實際 Node 求解測試回報而非只看編譯 success。
- **尚未完成**：公平版真正 Node 兩階段成功、真正公平 HTML、真正公平版 Chromium 實跑、夜哨四段／午間／安官長班艱苦公平、完整業參工作日分布及實際 iPhone Safari。
- **正式軍務使用**：目前版本尚未核定、不可將虛構測試與已排上實際勤務的人員姓名／名冊混淆；GitHub 不得存放真實軍務資料或由實際名冊推算的候選資格矩陣。

## 下一道決策

檢查兩階段 C++／WASM 真實編譯及 Node 結果：若失敗，先依明確編譯錯誤或求解反例修正；若成功，確認自動產出的單檔 HTML 與真實離線 Chromium 測試，不可只報綠色 GitHub CI。優先看是否**保持 589 班合法覆蓋數、是否公平有改善、是否公平階段 timeout**，再判斷增設艱苦哨第三階段及 iPhone Safari 設備端效能優化。
