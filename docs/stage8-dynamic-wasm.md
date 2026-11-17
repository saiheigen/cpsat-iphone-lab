# 第 8 階段：首次真正瀏覽器 CP-SAT 成功與動態排班介面工程

更新：2026-11-18，台灣時間。

## 已驗證成功（可追查）

1. [針對性真正 CP-SAT WASM 建置](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126438247)：OR-Tools C++ 編譯為單執行緒 WebAssembly，完成 Node.js 真正 CP-SAT 求解，獨立窮舉確認 desks=0、tables=3、profit=90、`OPTIMAL`。**不是 589 班排班演算法。**
2. [iPhone 單檔 HTML 打包](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44136847953)：重跑真的 Node WASM、SHA-256 驗證 JS/WASM 相符，輸出 `dist/iphone_cp_sat_real_smoke.html`（9,308,017 bytes）；存成 ZIP Artifact：`iphone-genuine-cp-sat-smoke-test`。
3. [真正 Chromium 瀏覽器離線驗證](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44197662038)：Playwright 真正啟動 Chromium，從 `file://` 載入單檔 HTML，在斷網模式點按按鈕，桌面和手機尺寸模擬均得到真正 CP-SAT `OPTIMAL`，無外部 HTTP 請求或未處理 JS 例外。
   - 桌面 Chromium：WASM 初始化與小題求解約 249 ms。
   - 手機尺寸 Chromium：同樣約 247 ms。
   - **這些不是 iPhone 的實測，也不能估計 589 班需要的時間。**
4. Linux Playwright **WebKit**（接近 Safari 引擎，但非真正 iPhone）：新增第三組離線瀏覽器測試；結果須以 [WebKit 最新 GitHub Run](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44197824629) 實際結論為準。首次只安裝 Chromium 的版本因缺少 WebKit 可執行檔而失敗，這是測試環境設置問題，後續已將工作流程改為安裝 Chromium 和 WebKit。

## 新增動態輸入的 C++/WASM 工程（未通過新編譯前不可宣稱完成）

- `src/cp_sat_assignment_bridge.cc`：新增獨立匯出 `solve_assignment_v1`，使用真實 CP-SAT 對**最小、受限的匿名指派模型**求最大合法填班。支援每一班每一人的 eligibility bit、同一人不可兼任的一對班次（pairwise conflicts）、不可排空班與指定 person index，回傳 `OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN/INVALID_INPUT`。
- **硬限制**：最多 64 個任務、24 名人員、1536 個候選配對、1024 對班次衝突，單執行緒，3 秒求解上限。這不允許直接匯入 589 班，不能將整月截斷後虛稱驗收。
- C++ 不具備軍務規則語義，未自行實作休假、站一歇一、艱苦哨、業參或跨月補償；這些必須由本機前置模型明確產生條件，再用獨立驗證器審核。
- `tests/dynamic_assignment_wasm.cjs` 使用真正 Node WASM 求解幾組小指派案例，與獨立 JavaScript 窮舉比對，並檢查非法輸入；只有成功才上傳新版本的動態求解 artifact。
- [動態 WASM 編譯工作流程](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199192306)：已啟動，真正完成與否、錯誤、產物以該 run 為準。這條 CI 不能被既有固定小題成功所取代。

## Python → 動態 WASM 安全銜接

- 新增 `solver/wasm_assignment_adapter.py`，把現有局部原生排班模型的可排人員、班次衝突及人工固定資訊匯成 `assignment-v1` 匿名索引字串，不包含人員姓名、單位或日期。限制 64 班／24 人，超限**拒絕處理**，不可直接將 589 班分段以免遺失跨段限制。
- 新增 `tests/test_wasm_assignment_adapter.py`，測試正確候選矩陣、跨日站一歇一、前月紀錄、姓名匿名、不合法人工固定和錯誤求解結果拒絕。
- [原生 CI 介面驗證](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199657912) 的 `native-cpsat` 工作已通過。這證明 Python 端資料格式及獨立結果審核，**不表示動態 WASM 本身已成功編譯**。

## 下一個主要關卡

1. 等動態 C++/WASM 真正編譯及 Node oracle 通過，然後做 Chromium/WebKit 離線瀏覽器測試。
2. 由小型動態指派擴大為可接受全月的模型協議，避免丟掉跨月與跨任務限制；先以純虛構資料壓力測試。
3. 再把週日留守、同時段間隔、跨月補償、業參公平等完整規格逐條與既有 v7.0 的模型核對。
4. 在真正 iPhone Safari 上驗證記憶體、耗時、單執行緒與離線可靠性；用戶設備及正式排班仍未驗收。

安全：GitHub 只使用合成資料。不得把軍網名冊、值勤日期、真實人員資料或尚未核定的軍務排班公開。
