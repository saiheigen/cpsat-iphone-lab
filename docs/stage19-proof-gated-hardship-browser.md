# 第十九階段｜第三階段艱苦哨 WASM 的證據綁定、離線打包與瀏覽器驗收

更新：2026-11-18（台灣）。僅使用完全虛構名冊索引、日期與休假禁排，**絕不提交真實軍務或由真實勤務推得的資格矩陣到公開 GitHub**。

## 實際完成的工程

### 1. 真正三階段 C++／WASM 驗收程式

- `tests/month_hardship_real_wasm.cjs` 增加 `browserFixtureManifest()`、`browserFixtureBytes()` 及 `--emit-browser-fixtures`。
- 四組離線情境：2 位虛構人員分 4 班的窮舉最優小案例、372 班大門／56 人合成密集禁排、217 班安官／50 人合成密集禁排、372 班大門指定整日空班（360 班）。
- Node 只有在**真正載入 `cp_sat_month_hardship_bridge.wasm`、呼叫 `solve_guard_month_harsh_v4`、計算完整月份獨立規則與艱苦分類**成功後，才生成 `guard-month-harsh-v4` proof。
- Proof 將上述四組案例的**完整 JSON bytes** 做 SHA-256，輸出 `fixture_sha256`；小型案例的 `oracleBest` 由獨立窮舉程式計算，不由 CP-SAT 自己聲稱。

### 2. 僅在真正 Node proof 完成後的獨立離線 HTML

- `build/package_month_hardship_wasm.py`：嚴格檢查 `js_sha256`、`wasm_sha256` 和 `fixture_sha256` 一致；包含三階段、填班位置保護、班數公平保護、密集 589 班合成測試、獨立窮舉小題，以及所有目標未惡化的證據。
- HTML 內禁止輸入真實名冊，四種匿名情境預先寫死；僅用本機 WASM 執行。
- 瀏覽器頁面獨立用 JavaScript 重算每人總班數、L1 目標偏差、四段夜哨／午間、安官實站時數與六小時長班負擔。若回傳結果不符合，報錯且不宣稱通過。
- 對 inline script 內 JSON 案例將 `<`、`>`、`&` 做 Unicode escape，防止特殊情境文字跳出 script 標籤。
- 新離線頁預定檔名：`experimental_full_month_hardship_cp_sat.html`；**只有真正 WASM 驗證成功才允許產生並發布**，不能把假的小 WASM 標頭測試當正式檔案。

### 3. 證據自動化鏈

- `.github/workflows/package-month-hardship-wasm.yml`：等待 [真正 v4 C++／WASM 編譯與 Node 測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44223914115) **success**，下載原始 JS/WASM/proof，重新使用真實 Node WASM 跑四組及反例，核對 SHA-256 與原始證據，才封裝離線頁。
- `tests/browser_month_hardship_wasm.py` + `.github/workflows/browser-month-hardship-wasm.yml`：只有前述打包成功後，在**真實離線 Linux Chromium** 的桌面與手機尺寸／觸控模式各跑四種場景（共八組）；比對班數、三階段狀態、艱苦哨初始／最終偏差。**不代表 iPhone Safari 實機驗收**。
- `tests/test_package_month_hardship_wasm.py`：使用**假的最小 WASM 標頭**測試拒絕錯誤來源、WASM 被替換、fixture 被置換、缺少 SHA、冒稱 iPhone 已驗收、宣稱艱苦哨最佳解卻無證據、L1 變差、捏造填班／最優解、HTML `</script>` 攻擊。亦檢查打包產出的頁面 JavaScript 能通過 `node --check`，**不冒充實際 WASM 求解**。
- `.github/workflows/verify.yml`：加入 Node `--preflight`、四組案例 manifest（含 589 班池形狀）預檢與 Python 防錯測試；即使昂貴的 C++ 編譯尚在進行，也能先攔下明確錯誤。

## 已驗收與待驗收分級

1. **已驗收：原生第三階段 CP-SAT（Python）**。 [CI #141](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44222864822) 與 [CI #145](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44223696850) 已通過。小型獨立窮舉、跨日時段、固定班次、休假及負擔分數核對正常。
2. **已驗收：離線頁打包器的防錯、證據格式與 JS 語法**。 [CI #151](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44225246851) 成功（此為新實際 `node --check` 前的版本）；後續版本加入更嚴格的測試，實際狀態請見 CI。所有 fake fixture 都只是包裝安全測試，不是新的 C++ WASM 成功證據。
3. **尚未驗收：真正三階段 C++／WASM**。 [Three-stage v4 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44223914115) 初步已通過前置測試與 CMake 設定，真正編譯與 Node 三階段求解在本段落撰寫時**尚未取得最終結果**。依 workflow run 最終狀態更新，不得猜測成功。
4. **尚未驗收：v4 真正離線 HTML 與 Chromium 的 8 組案例**。需由上游真正 v4 成功後觸發，尚不能宣稱結果。
5. **尚未驗收：真正 iPhone Safari 與 v7.0 業務資料整合**。在真實裝置上開啟 `file://` 單檔、可用記憶體、背景切換、停止按鈕、過熱及電池尚無裝置證據。

## 注意：公平的適用範圍

目前 v4 使用依總班數正規化的分類艱苦負擔 `abs(F*c_p - C*n_p)`（加權 L1），**並非原 v7.0 的平方公平函式**；且第三階段把已填／空白位置、已取得的總班數公平 **完整鎖定**，避免用夜哨均勻交換失去既有合法班次。這只能證明在已實作的硬限制與獲得的前兩階段結果固定下的局部／條件最佳化；尚不代表完整軍務規章、跨月艱苦平衡、週內業參日期、公平退補及單位簽核已驗收。

## 下一階段優先順序

**先等真正 v4 Node 證據結束並除錯，而不是為進度好看預告已可用。** 只有 v4 真正成功、8 組離線 Chromium 成功之後，才評估 iPhone Safari 本機壓力與 v7.0 安全整合。過程中不能向公開 GitHub 提交實際班表或人員。
