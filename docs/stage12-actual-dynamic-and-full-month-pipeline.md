# 第十二階段｜真正動態 WASM 已可用於離線小型指派；589 班 C++ WASM 建置與驗收管線

更新：2026-11-18（台灣）。本資料只使用完全虛構人員與勤務，禁止上傳真實軍務資訊到 GitHub。

## 已取得的實際成功證據

1. [動態 CP-SAT WASM 實際編譯 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199192306)：**success**。C++ OR-Tools Emscripten 真正 WASM，Node 執行四組動態班次指派模型，取得正確 `OPTIMAL`（4 班滿班、1 班、2 班）與已證明無解的 `INFEASIBLE` 案例；與獨立 JS 窮舉比對一致。
2. [動態 WASM 離線 HTML 打包 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206068288)：**success**。重新 Node 實跑，對照 JS/WASM SHA-256，輸出 `dynamic_cp_sat_offline_demo.html`（9,324,012 bytes）；GitHub Artifact `genuine-dynamic-cpsat-offline-demo`。
3. [動態 WASM 真正離線 Chromium 瀏覽器 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206110133)：**success**。Playwright 在斷網下於桌面和手機尺寸 Chromium 按下按鈕，測試四種動態指派、合法／無解狀態；不是 JS mock，也不是 iPhone Safari 實機。
4. [全月匿名資料層 + C++/JS 合成前置測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206002071)：**success**，包含 2026/12 大門 372、安官 217、虛構 56+50 人、前月禁排、固定班次及完整月形狀，不截斷資料。沒有執行真正 589 班 WASM。
5. [獨立月度回傳資料第二次驗證](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44205797132)：**success**。即使求解器聲稱 OPTIMAL，如果還有空班，本地稽核不會單憑 JSON 文字判定已證明最大填班；自動擋下跨月禁排、指定空班、連日站哨等範例錯誤。

## 這輪新增的 589 班交付門檻（已提交，等待真正 WASM 編譯成功）

1. [全月 C++ OR-Tools WASM 編譯 #2](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206220771)：已**實際啟動**，正在編譯 `cp_sat_month_bridge`。真正結果以該 GitHub run 的最終狀態為準；沒有結果前不能宣稱 589 班 WASM 可用。
2. `tests/month_real_wasm.cjs`：通過後需真正執行 372 班大門、217 班安官、合法同週日雙班、連續週日留守違規、相鄰日固定違規、非法傳輸等合成情境，對照獨立 JS 規則審核。**589 班滿班案例刻意每班只有唯一合法候選**，證明求解幾何，不等於密集 106 人或完整公平效能。
3. `build/package_full_month_wasm.py`：驗證實際 Node proof 的五組案例、全月 589 班數、106 虛構人員、無虛假軍務驗收宣稱及 JS/WASM SHA-256；僅成功時產生單一離線 HTML `experimental_full_month_cp_sat.html`。
4. `.github/workflows/package-full-month-wasm.yml`：只有 full-month C++ WASM 真正編譯、Node 合成班次獨立審核 success 後才下載神器，再**重新 Node 實跑**才打包。若失敗或跳過，絕不產出冒牌 HTML。
5. `tests/test_package_full_month_wasm.py`：使用刻意假造的極小檔案，測試範圍只限於打包 proof gate 的拒絕行為（Hash 被改動、缺測試、偽造 589 成功、聲稱 iPhone 已測等）。[原生 CI #97](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44207218790) 的此類單元回歸測試已通過；**fake fixture 絕非真正 WASM 求解證據**。
6. `tests/browser_full_month_wasm.py` 和 `.github/workflows/browser-full-month-wasm.yml`：真實 Node 建置與離線打包都成功後，才會在桌面及手機尺寸 Chromium 斷網環境下真的求解五組完整月份相關案例並核對輸出；同樣不是 iPhone Safari 實機驗收。
7. GitHub 基礎 CI 加入 `concurrency.cancel-in-progress`，避免多次連續修改反覆把過期版本重編，保留對最新 commit 的有效驗證。

## 本階段尚未解決的關鍵限制

- 589 班真正 WASM 是否成功編譯、Node 求解及瀏覽器打包，**仍待 GitHub 實際回報**。
- 完整業參權重、艱苦哨公平、跨月補償、現實資料敏感性／來源簽章，還沒有在 C++ 589 班模型完整移植。
- 目前動態 HTML 只支援 64 班／24 人匿名測試，不能直接拿來值勤；完整月的後續 HTML 即使通過也先只是合成效能測試頁，不會匯入或覆寫 v7.0 原有班表。
- 目前的 Chromium、Linux WebKit 成功不等於真正 iPhone Safari 完整月份驗收；使用者可先在自己的 iPhone 測動態小題 HTML 並回報結果，不須把任何真實軍務資料帶出軍網。

優先順序：等真正 full-month WASM 的 Node 驗收通過，再做 589 班密集資格矩陣與合法缺班壓力測試 → 公平補償移植 → 離線 iPhone 實機驗收 → 逐步與 v7.0 安全整合。
