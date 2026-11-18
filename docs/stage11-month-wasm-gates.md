# 第十一階段：動態 CP-SAT WASM 三層實證、整月 C++ 實驗啟動與結果獨立稽核

日期：2026-11-18（台灣時間）；所有人員、休假、勤務與班表均為虛構資料，未上傳任何真實軍務資訊。

## 一、已經真正通過的結果

### 動態 C++ OR-Tools CP-SAT WASM

- [Dynamic assignment CP-SAT WebAssembly build #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199192306)：**completed / success**。
- 真正 Emscripten 編譯 `src/cp_sat_assignment_bridge.cc`，Node 載入生成的 `.wasm`，呼叫 `solve_assignment_v1`。
- `tests/dynamic_assignment_wasm.cjs` 使用獨立窮舉核對四組合成指派情境：
  - 四班兩人，全部合法填滿，`OPTIMAL`，4/4。
  - 單人衝突＋強制空班，`OPTIMAL`，1/3。
  - 資格限制與人工固定，`OPTIMAL`，2/3。
  - 互相衝突的固定班次，正確回報 `INFEASIBLE`。
- 另有四組非法輸入拒絕檢查；證據包含 JS／WASM SHA-256。
- **限制：** 仍是最多 64 班／24 人的匿名原型，不能處理真實 589 班，也未實作完整軍務公平補償與跨月規則。

### 動態離線測試頁與真實 Chromium

- [Package verified dynamic CP-SAT WASM offline demo #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206068288)：**completed / success**，再次 Node 實跑四組，按 SHA-256 重新驗證後生成 `dynamic_cp_sat_offline_demo.html`。
- [Dynamic offline CP-SAT WASM browser acceptance #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206110133)：**completed / success**，Playwright 斷網模式，真正桌面與手機尺寸 Chromium，點選四種情境並執行實際求解與獨立窮舉比對。
- 單一 HTML 為 9,324,012 bytes，GitHub Artifact `genuine-dynamic-cpsat-offline-demo`，可在打包 workflow 的 Artifacts 下載。
- 這**不是**真正 iPhone Safari 實測，Chrome 手機尺寸模擬不等於 Apple 裝置。

## 二、新增整月 589 班 C++／WASM 實驗：正在建置

- 既有 `guard-month-v2` 對應完整月份、不截斷資料：2026/12 大門 372 班／56 人；安官 217 班／50 人。
- `src/cp_sat_month_bridge.cc` 以 C++ CP-SAT 實作目前模型的站一歇一、同日最多 3 班（安官最多 1 班）、同日 6 小時休息、兩日內同時段、連續兩星期日留守、人工固定與候選資格位元矩陣。
- `tests/month_real_wasm.cjs` 將真正 Emscripten 求解結果與獨立 JavaScript 衝突審核比對，含人力不足／固定違規反例；測試用的 589 班矩陣刻意每班只給**一名**合法候選，這是協議與求解器模型幾何驗收，不是密集候選矩陣的效能證據。
- `tests/month_fixture_preflight.cjs` 已將 589/106 合成滿班 witness、週日留守及休息限制反例在不編譯 C++ 前先驗證，GitHub CI **已通過**。
- [Full-month CP-SAT WebAssembly experiment #2](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206220771)：已**真正觸發並進入 CMake 設定階段**，最後編譯與 Node 月排班驗收仍需依該 run 的終態確認，尚不得宣稱成功。
- 已修正 workflow 原本上傳錯誤 proof 路徑：`full_month_wasm_proof.json`。

## 三、整月 WASM 返回結果的第二道審核

新增 `solver/full_month_wire_v2.py::audit_full_month_v2_response`：
- 不相信 WASM 單方面回傳的「合法」或「OPTIMAL」字樣；按既有可信的 Python 原始資料重建 589 班的班號→人員編號，再檢查每一班的候選資格、前月歷史、夜查、休假、人工固定、站一歇一、週日留守與填班計數。
- `UNKNOWN`、`INFEASIBLE`、截斷／無效人員索引、偽造 filled/missing 或違規人工固定，一律拒絕當班表輸出。
- 即使 JSON 字串聲稱 `OPTIMAL`，若仍有缺班，本地稽核只能證明**可行**，不能單靠外來文字證明全域最大填班；只有每班填滿（自然上界）才能由此層獨立證明填班數達上限。
- 標示 `actual_wasm_execution_proven=false`，因單獨的 Python 函數不可能證明呼叫者真的執行了 WASM；真正求解證據必須另經 GitHub Node／瀏覽器流程。
- `tests/test_full_month_wire_v2.py` 新增反例：竄改 hint、非法跨日同人、跨月禁排、指定空班遭覆寫、偽裝 OPTIMAL、錯誤型態、輸出缺班數與資料截斷。
- [原生 CI #89 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44205797132)：第二道獨立驗證與來源真偽提示測試成功。
- [原生 + baseline CI #92 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44206002071)：新增月度測試程式語法、合成完整 witness preflight 與 589 班資料協議均成功。

## 四、仍不能宣稱的事項

- 真正完整 589 班 WASM 編譯與 Node 月排班求解仍**未驗收**：本輪最新 full-month 編譯正在進行。
- 無人測試過 iPhone Safari 對這一版動態 HTML 的實際記憶體用量與長時間求解。需使用者實機結果。
- 真實軍務完整規則、跨月補償、業參／艱苦哨公平尚未移植進整月 WASM，因此目前工具不能用於正式排哨。
- 匿名化的可排班次矩陣可能仍具有軍務敏感性，**不得將實際資料上傳公開 GitHub**。
- 目前 589 班是刻意建構的合成滿班個案；不可推論實際勤務同樣排得滿。

## 五、下個驗收門檻

等待真正整月 C++ WASM 的編譯及 Node 589 班審核結果，以實測失敗點修正；成功後才產出手機離線測試頁並實測。後續再把公平、補償與經驗證的完整跨月規則移植，而不是只增加月份班數上限。
