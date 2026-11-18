# 第十階段：完整月份匿名協議、真正 C++/WASM 月排班模型（待編譯驗收）

日期：2026-11-18（台灣）。**沒有使用或上傳真實軍務名冊、休假或勤務紀錄。**

## 這一輪的已驗收工作

### A. 完整月份傳輸協議（Python，CI 已通過）

- `solver/full_month_wire_v2.py` 新增獨立於 `assignment-v1` 的 **`guard-month-v2`** 協議，嚴格使用完整、按日／班號排序的月份：
  - 2026/12 大門：372 班，56 名虛構人員；
  - 2026/12 安官：217 班，50 名虛構人員；
  - 合計 589 班與 106 名虛構人員，但依兩個互不重疊勤務池分別編碼及求解。
- 協議只傳出月份、勤務池、資格位元矩陣、人工固定位置和可選合法初稿提示；不輸出姓名、人員編號、詳細事件或前月勤務日期。**即使匿名，真實軍務可排資格矩陣仍可能敏感，不得提交至 GitHub。**
- `prepare()` 先檢查歷史、資格與人工固定；`validate_full_month_v2_export()` 重新按原資料核對資格矩陣，若班次被截斷、日期不符、可排資格被竄改、前月限制被忽略、固定人員被改動，就拒絕。
- `tests/test_full_month_wire_v2.py` 涵蓋全月 589/106、休假收假日、夜查前後日、出車前夜夜哨、月初跨月休息、人工固定、閏年、改寫矩陣和固定班次的負面測試。
- **實證：** [GitHub native + baseline CI #81 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44203437133)。這是資料協議／Python 原生測試成功，不是整月 WASM 求解成功。

### B. 全月 C++／真正 WASM 實驗模型（已提交，仍未驗收）

- `src/cp_sat_month_bridge.cc`：新建真正 OR-Tools C++ CP-SAT 模型入口 `solve_guard_month_v2`，和既有已成功的 `cp_sat_probe` 以及 `cp_sat_assignment_bridge` 分開。
- 輸入完整月份位元矩陣，內建與 v7.0 已核對的硬限制：
  - 大門每班一人、同日最多 3 班且 6 小時休息；安官同日只能一班；
  - 站一歇一（相鄰兩個日曆日）；
  - 相同班號 2 日內不重複；
  - 週日 06–20 大門及安官 18–22 留守，連續兩星期週日不得留守，但**同週日若間隔充足可合法站兩班**；
  - 人員資格／休假／車勤／受訓／夜查／既有跨月紀錄已由本機 Python 資料層折算為候選資格，並保留人工固定和合法初稿 hint。
- 限單執行緒、10 秒求解時限、輸出保持 `OPTIMAL`、`FEASIBLE`、`INFEASIBLE`、`UNKNOWN` 明確分級；未有結果時絕不憑空產生班表。
- **尚未完成：** 權重／業參每週分布、艱苦哨公平、長班時數公平、跨月補償的 C++ 模型；正式 v7.0 網頁整合；真實 iPhone Safari 實測。故此求解器不是已核定的正式排班引擎。

### C. 不造假的真正 WASM 對照測試（已提交，待編譯）

- `tests/month_real_wasm.cjs` 準備了**真實 WebAssembly** 的 Node 執行和獨立 JS 逐人衝突審核：
  - 372 大門／56 人、217 安官／50 人，合計 589 班合成**稀疏資格矩陣**（每班僅一名已知合法候選），驗證真正全月資料尺寸、C++ 硬規則和可填班上限。
  - 人工固定相鄰日期同人應 `INFEASIBLE`；
  - 同週日兩個足夠間隔的大門班次應合法；
  - 相鄰兩週日留守同人應 `INFEASIBLE`；
  - 截斷月份、錯誤格式必須拒絕。
- 這些案例刻意簡化，因此**即使成功，依然不能證明密集矩陣、實際事件眾多時的 589 班求解效能，更不能證明完整公平最佳化。**
- `.github/workflows/verify.yml` 已加入 `node --check` 語法驗證，成功紀錄：[baseline CI #85](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44204500924)。

### D. 編譯安排與避免重複浪費

- [既有動態 64/24 WASM #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199192306) 持續編譯；後續兩個執行也已因既有 workflow 觸發被啟動。
- 現已移除不必要的 CMake 路徑觸發；在 [全月 WASM 專用 workflow](https://github.com/saiheigen/cpsat-iphone-lab/actions/workflows/cp-sat-wasm-month.yml) 中，選擇**動態實驗第 3 次真正成功後**才自動啟動整月建置（也支援手動啟動），以防三次幾乎相同的昂貴編譯都重複觸發整月版本。
- 自動建置只編譯 `cp_sat_month_bridge` 與其必要依賴，不重新編譯非必要的 OR-Tools 命令列工具；Node 實測審核成功才上傳 artifact。
- **截至記錄建立：整月 C++/WASM 尚無成功編譯證據，不能與 Python 資料協議 CI 混淆。**

## 正式可用之前的必要關卡

1. 動態 C++/WASM 編譯完成且取得真實 Node CP-SAT 驗證，再編譯 `guard-month-v2`。
2. 真正 WASM 以虛構、完整 589 班資料通過獨立限制檢查；再加入密集候選矩陣、休假、車勤、夜查等條件測試記憶體、速度與上限。
3. 補上完整公平、業參與跨月補償，與 v7.0 的全部硬規則逐條校驗。
4. 產生真正瀏覽器測試頁，在 Chromium、WebKit 和**真實 iPhone Safari** 各自驗證，再與 v7.0 正式網站安全整合。

此階段不產出、也不冒稱可以直接用於軍務的 589 班自動排哨檔案。
