# 第 7 階段：真正 CP-SAT WebAssembly 已編譯、Node 與離線 Chromium 驗收

日期：2026-11-18（台灣）。

## 已經取得的硬證據

| 關卡 | 結果與來源 | 不能推論 |
|---|---|---|
| 真正 OR-Tools CP-SAT C++ → WASM | **Success**，專案的針對性建置 `cp_sat_probe` 與必要依賴，產生 .js、.wasm；[GitHub run](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126438247) | 不能說能在 iPhone Safari 或可排全月 |
| 真正 Node.js 載入 WASM 求解 | **Success**，`run_cp_sat_probe` 回傳引擎 Google OR-Tools CP-SAT、`OPTIMAL`、desks=0、tables=3、profit=90，並由迴圈獨立窮舉證實唯一最大值；同 run | 不能說已接受任意名冊／勤務規則 |
| 單檔離線 HTML 打包 | **Success**，Node 重跑且透過 SHA-256 檢查 .js/.wasm；產物 `iphone_cp_sat_real_smoke.html` 9,308,017 bytes；[包裝 run](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44136847953)，Artifact `iphone-genuine-cp-sat-smoke-test` | 不能說手機已按下測試鍵 |
| Chromium 真實離線瀏覽器 | **Success**，透過 Playwright 開啟 `file://` HTML、強制 offline 模式，實際按下本機求解按鈕；[Chromium run #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44197662038) | Chromium 非 Safari |
| Chromium 手機尺寸模擬 | **Success**，390×844 觸控／手機模式，CP-SAT 回傳正確 OPTIMAL，0 外部 HTTP 請求，0 JS pageerror，同 run | 視窗與輸入模擬不等於 Apple 裝置 |
| Linux Playwright WebKit | 已新增獨立測試與 CI，**結果以最新 GitHub run 為準**；[WebKit CI run](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44197824629) | 即使通過也不等於 iOS Safari 實機通過 |
| 正式 589 班 WASM 排班引擎 | **未完成**，目前 WASM 模組只有虛構兩變數數學題，尚未提供任意排班資料及動態 CP-SAT 建模 C++ 介面 | 原生 Python 589 班合法構造／分池測試不能代替 WASM 測試 |
| 真實 iPhone Safari 與軍務資料 | **未驗收** | 不得把測試頁當成已核定排哨系統 |

## Chromium 真實測試數值（CI Linux，非手機）

- 桌面 Chromium：結果 OPTIMAL、0 桌子、3 張桌、利潤 90；啟動 WASM 並求解約 249 ms，網路請求 0，未處理 JS 錯誤 0。
- 模擬手機 Chromium：同樣正確，約 247 ms，網路請求 0，未處理 JS 錯誤 0。
- 這是極小規模求解，不可拿來估計 589 班月排班需要 0.25 秒。
- `tests/browser_real_cpsat.py` 使用真正 Playwright 引擎與離線檔，不是 JS mock。WebKit 測試加入後需另查其 CI 運行結果。

## 安全與工作流程

- 本案的單檔 HTML 僅包含原版 OR-Tools 引擎以及虛構數學問題，未含任何真實軍務姓名、休假、夜查或勤務資料。
- 在取得使用者的 iPhone 上實測證據前，不聲稱 iPhone Safari 已通過。
- GitHub Actions 中的離線測試已設定 `offline=True` 並檢查 HTTP 請求清單，保證 CI 驗收腳本不使用遠端求解服務。
- 下個工程門檻：可接受動態模型的 C++/WASM 介面；與 v7 當月名冊／休假／跨月／公平資料對接；589 班求解效能與完整規則驗收；真正 iPhone Safari 實機測試。

## 取得測試產物

在 [包裝 run](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44136847953) 的 Artifacts 下載 `iphone-genuine-cp-sat-smoke-test`，解壓後單一 HTML 是 `dist/iphone_cp_sat_real_smoke.html`。它只能驗證本機 CP-SAT 是否能運作，不會匯入或覆寫既有排班資料。
