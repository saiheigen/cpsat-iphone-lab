# 排哨工程審查／回歸與交叉驗證紀錄（2026-11-18 台灣）

## 審查範圍

本文件記錄 GitHub 中使用 **虛構測試資料**對既有原生 CP-SAT 部分模型、v7.0 本機備份 JSON 轉換器，以及真正 WebAssembly 編譯鏈的審查結果。不是正式軍務班表驗收，也不能證明 589 班實際合法、充足或公平。

## 確認並修正的問題

1. **不完整前月班表被當成歷史依據的風險：** `solver/v7_backup_bridge.py` 現在要求 v7 前月 schedule 完整覆蓋該月每個班次，且每個日期／班號唯一、時段與人員識別合法。發現截斷、重複、跨月錯置或錯誤身分時拒絕匯入，不擅自認定「前月資料完整」。有對應負面測試。
2. **閏年簡寫日期：** 針對日期 `2/29`，只在候選年確有 2 月 29 日時才納入比較；合法閏年不再因相鄰非閏年例外而整筆失敗；仍拒絕三個候選年份全無效的日期。
3. **名冊三欄格式：** v7 已支援 `編號,姓名,性別`；先前 Python 轉換器會把第三欄「男／女」認成姓名。現已比照 v7 的三欄特例修正，並新增驗證其後續休假、督伙等紀錄可正確對應人員的回歸測試。
4. **第三階段可能回傳較差艱苦哨方案：** `solver/fairness_cp_sat.py` 在保留已證明最大填班與班數公平的同時，新增比較艱苦哨原方案與新方案的偏差分數。後一階段只有 FEASIBLE 但更差時不得覆寫較好方案；後一階段 OPTIMAL 理應不比已知可行 incumbent 差，否則直接報錯。
5. **真實 WASM 打包檔案位置假設過窄：** `.github/workflows/package-iphone.yml` 現在遞迴尋找唯一 JS、WASM 及求解證據檔（不能有重複），重新以 Node 實際求解驗證後才打包。這避免不同建置產物資料夾結構造成假失敗，不降低真實求解驗證門檻。
6. **新增測試自身筆誤：** 最初新加的跨月範例有一個括號錯字，已經被 CI 發現、修正並成功重跑。首次失敗不算產品缺陷，但必須保留在驗收證據中。

## 已取得的真實 CI 證據

- [三組不同種子的交叉審查（第 2 次）](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44125813503)：3 個 CI jobs 全部 success。每組 30 件測試，合計 90 種虛構小型案例，在真正原生 CP-SAT 與暴力窮舉求得的最大填班數之間做比較。
- [三組不同種子的交叉審查（第 3 次）](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126196175)：同 90 種案例重新執行，3 jobs success。
- [三組不同種子的交叉審查（第 4 次）](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126224751)：同 90 種案例重新執行，3 jobs success。
- [擴增為六組不同種子的審查（第 5 次）](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126429037)：6 jobs success，180 種不同虛構案例（各組 30）；也重跑 v7 備份轉換和公平回歸測試。
- 因第 1 次新增的測試程式曾有括號筆誤，[審查第 1 次](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44125653914) failure，不應略去這項事實。
- **覆蓋界線：** 暴力窮舉和 CP-SAT 確實是不同算法，但參照了目前部分模型共用的資格與衝突規則；故這不是第三方獨立認證所有軍務規定，180 案例也不是 180 個完整 589 班月份。

## 真正 WASM 編譯狀態

- [Experimental CP-SAT WebAssembly #5](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44112988121)：**completed / failure**。實際失敗點仍是編譯不需要的 OR-Tools 工具；`linear_solver/solve.cc` 的 `SigintHandler` 與 `sat_runner.cc` 的 `SigtermHandler` 在 WebAssembly 環境無法編譯。與 #4 的主要錯誤同類。
- [Targeted CP-SAT WebAssembly build #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44126438247)：原版 #5 失敗後自動觸發，只建置 `cp_sat_probe` 與必要依賴，避免不需要的工具。建立本文時尚未驗收成功，不可宣稱 iPhone CP-SAT 已可用。
- 原版失敗後的 iPhone 打包工作會被標記為 skipped：這是符合 fail-closed 行為，並非打包成功。

## 待完成的高優先工作

1. 等針對性 WASM 流程實際完成，確認真實 Node 求解 `OPTIMAL` 與獨立數值核對；完成後才跑 iPhone 封裝和實機驗證。
2. 原生 589 班求解效能仍有差距：20 秒僅返回 FEASIBLE 554 班，而獨立的簡化虛構全滿 witness 為 589 班。沒有全域最優證明；不得把缺 35 班誤判為人力不足。
3. v7 → Python 橋接器暫時只做原型驗證，不重新計算 v7 專用 inputSig 或將新結果覆寫原網站；跨月檢查與補償的真正完整性尚待同一執行環境內完整驗證。
4. 所有現有審查資料均為虛構編號，不應上傳真實軍務名冊或班次紀錄到 GitHub。
