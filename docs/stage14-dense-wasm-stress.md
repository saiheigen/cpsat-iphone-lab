# 第十四階段：完整 589 班密集候選真 WASM 壓力測試（合成資料）

更新：2026-11-18（台灣）。請勿把真實人員、假勤、車勤、夜查或由真實勤務推導的候選資格矩陣提交公開 GitHub。所有案例皆為完全虛構。

## 已實測：原先編譯完成的 C++ OR-Tools WebAssembly，無重編

[GitHub Dense 589-shift real WASM stress benchmark #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44213148151)：**completed / success**。使用 [已獲得真實編譯與 Node 獨立驗證的原始 WASM artifact](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206220771)，下載後先驗證編譯 JS/WASM 的 SHA-256，再用同一真實 WebAssembly 入口 `solve_guard_month_v2` 真正求解。

| 虛構情境 | 合成候選配對數 | 求解狀態 | 已填／班數 | Linux Node 求解毫秒 |
|---|---:|---|---|---:|
| 大門，有合法提示、虛構禁排 | 8,535 | OPTIMAL | 372/372 | 2,710 |
| 大門，無提示、同樣虛構禁排 | 8,535 | OPTIMAL | 372/372 | 1,195 |
| 大門，人工固定及指定整日缺班 | 8,272 | OPTIMAL | 360/372 | 1,163 |
| 安官，有合法提示、虛構禁排 | 4,166 | OPTIMAL | 217/217 | 389 |
| 安官，無提示、同樣虛構禁排 | 4,166 | OPTIMAL | 217/217 | 397 |
| 安官，人工固定及指定整日缺班 | 4,046 | OPTIMAL | 210/217 | 499 |

- 除第三種刻意指定缺班外，全部完整填滿。指定缺班情境中大門整日 12 班／安官整日 7 班皆固定空班，模型精確保留，沒有把模型給出的意圖假裝成人力不足。
- 每個已填結果都經完全**獨立於 C++ 求解器的 JS 巡檢**，驗證可排資格位元、人工固定、每日最多班數、站一歇一、相同班號兩日內、同日 6 小時間隔及連續週日留守。
- 每一個情境都預先有一份合法且完整的構造 witness。因為合法參考填班數達到每班最多 1 人的自然上界、且被固定的缺班不可排，所以這六個 `OPTIMAL` 亦有獨立的**最大填班數上界佐證**；不只是相信求解器字串。
- 計算在 GitHub Ubuntu Linux **Node.js** 中進行：測試行程 RSS 最高觀察約 **340.2 MB**，Node WASM 初始化／外部記憶體與實際 iPhone Safari 的資源不同，絕不可當成手機實測。無提示跑得更快是這些案例的測試觀察，**不是一般性效能承諾**。
- C++ 求解模型本身採單執行緒，每個 pool 單次求解最多 **10 秒**。若未找到解則狀態為 UNKNOWN，不可以當作班表或 0 班；FEASIBLE 有可行解但不一定證明最佳。

## 合成禁排的精確測試範圍

`tests/wasm_dense_month_benchmark.cjs` 的資料由程式生成；包含假設性的休假與收假日、休假前夜夜哨、受訓前一日、夜查前後一天、出車前夜夜哨及後一天、安官督伙與值星、固定伙房、免夜哨、免午間；不同日期／對象的限制預先折算成允許／禁止位元。這些測試**不證明 C++ 會自行解讀日常中文勤務紀錄**，C++ 只看到已清洗的匿名候選矩陣。歷史跨月與各項資料驗證須由本機前置 Python 模組繼續負責。

## 真正瀏覽器密集驗證

- 另外新增 `tests/browser_dense_month_wasm.py` 和 `tests/audit_browser_dense_wasm.cjs`，以**已真實 Node 驗證過的同一份 WebAssembly**、經過 proof-gate 的離線單檔 HTML，在斷網 Playwright Chromium 桌面及 390×844 手機尺寸觸控模擬中各執行六組（共 12 組）。
- 瀏覽器用真正的 C++ WASM `solve_guard_month_v2`，不是 JS 假求解；輸出的每個班次再交由**另一支 Node 原生稽核程式**按相同已證明合法的虛構輸入重建規則，檢查真假最佳填班與日跨界。
- [GitHub actual offline browser dense workflow](https://github.com/saiheigen/cpsat-iphone-lab/actions/workflows/browser-dense-wasm.yml) 的實際結果、紀錄與錯誤必須以 workflow 完成狀態為準。**在 CI 終結之前，不得聲稱瀏覽器密集測試通過**；此測試仍非真 iPhone Safari。

## 目前仍不會算作驗收的部分

- WASM 的公平目標仍只有最大**合法填班數**，尚沒有在 C++ 模型實作 1/3 業參權重、督伙／前月補償後的二階段公平、夜哨／午間艱苦、安官長時數分配。現有 `solver/fairness_targets_v7.py` 和 `solver/lexicographic_count_fair.py` 的原生 Python 小題成功，不等於公平已移植 WASM。
- 合成案件沒模擬真實人力波動、排班交叉艱難、所有擔任業參的日常輪換或軍網作業風險；滿班成功不代表真實班表也可滿班。
- **真實 iPhone Safari** 的本機 file 開檔、Memory、App 切換後恢復、畫面阻塞、長時間求解、熱與電池都尚未有裝置證據。

下階段建議：先查閱 12 組真正離線瀏覽器密集結果，再實作不犧牲填班數的 C++/WASM 第二階段公平目標；新 C++ 版需獨立編譯、Node 及離線瀏覽器三重驗收。
