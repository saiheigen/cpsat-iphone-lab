# 排哨求解器瓶頸診斷與首次搜尋策略突破

更新：2026-11-18（台灣）

## 一、兩個獨立瓶頸

**編譯相容性（WASM）**
- 舊版 Experimental CP-SAT WebAssembly #5 失敗：上游 `solve.cc` 的 `SigintHandler` 和 `sat_runner.cc` 的 `SigtermHandler` 在 Emscripten 編譯失敗。
- Targeted CP-SAT WebAssembly build #1 將建置目標縮小為 `cp_sat_probe` 及其依賴，不再編譯非必要的工具。此報告撰寫時仍在編譯步驟，**未取得真實 WASM 求解器可在 iPhone 上執行的證據**。
- https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126438247

**搜尋效率（原生 CP-SAT）**
- 舊的整體最大填班模式：589 班、106 名虛構人員、無額外禁排；單執行緒 20 秒得到 FEASIBLE 554／589 班，缺 35 班，並沒有 OPTIMAL 證明。
- 既有独立構造 witness 已證明同一簡化硬限制下可滿班，該缺口不是已證明人力不足。
- 舊基準 https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44120794867

## 二、分池＋滿班可行性策略：已實際成功

新程式：`benchmarks/native_589_split.py`，流程 `.github/workflows/benchmark-split.yml`。
- 先透過不同勤務池人員互不重疊的**現有部分模型**分為大門（372 班、56 人）、安官（217 班、50 人），兩組各自求解。
- 先建立經獨立審查的虛構滿班 witness 作 warm start，再加入全部班次必須填滿的限制（即先測可行性）；在此前提下 CP-SAT 仍必須真實求解。
- 大門：`OPTIMAL`，372／372 班，求解 14.791 秒，建立模型 1.049 秒。
- 安官：`OPTIMAL`，217／217 班，求解 6.787 秒，建立模型 0.245 秒。
- 兩者各自使用單執行緒、官方 OR-Tools Python 原生版，GitHub Actions 分別的 runner。合計 589／589 在此簡化、無請假等限制的虛構模型下有實際 CP-SAT 求解證據。
- https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44127889291

### 不可誤讀

1. **不可以把這說成完全相同的 benchmark 變快**：舊基準的目標是搜尋最大合法填班，新基準以預知滿班 witness、添加滿班限制測**可行性**，兩者求解目標不同。
2. **沒有解決真實排哨人力缺額**：真實休假、夜查、車勤、值星、督伙、業參、跨月等限制沒有輸入。正式求解不可硬強制填滿不可能的班次，須先嘗試滿班；不可行時退回合法最大填班並明確顯示缺額與驗證狀態。
3. **沒有整月公平證明**：班數與艱苦哨公平優化尚未在上述 589 班整月案例執行；分池也只能在已建模規則跨池互不衝突時安全拆開。
4. **不是 iPhone 本機速度**：所有數字在 GitHub Linux 原生 CP-SAT runner 取得；手機 WASM 性能需實機測試。
5. **未真正連接 v7 正式排班網站**：目前只有 v7 備份轉換器與合成測試，未覆寫任何真實班表。
6. **真正 WASM 的瓶頸尚未宣告解決**：必須先完成 C++／Emscripten 編譯、Node 真正求解、打包與 iPhone 實機四個關卡。

## 三、下一步的工程優先順序

1. 讓針對性 WASM 編譯走到 Node 真正求解；如果失敗按確切錯誤修。
2. 將「按池分解、先滿班可行性、失敗則回退最大填班」做成可重用功能，並為有休假／跨月的虛構案例加對照測試。
3. 完整結轉公平配額與艱苦哨分層求解，逐條與 v7.0 獨立審核器核對。
4. 最後才進手機網頁與真實 iPhone WASM 測試；不以 589 虛構滿班替代實際業務安全驗收。

機密限制：不要把真實軍務名冊、個人資料或勤務日期上傳至 GitHub。
