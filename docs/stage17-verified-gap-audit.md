# 第十七階段｜排哨系統工程查缺補漏報告（等待公平 WASM 編譯時）

審查日期：2026-11-18（台灣時間）。審查對象為倉庫中的 Python v7 備份轉換、完整月份公平輸入／輸出協議、Node C++/WASM 實測與離線 HTML 打包管線。已逐段對照 Project 提供的《哨務工作台_v7.0_一鍵整月自動最佳化版.html》關鍵函式：`build()`、`staticReason()`、`conflict()`、`calcGoals()`、`calcActualTargets()`、`toggleArchive()`。

**重要：此報告不是軍務勤務安全認證，也未使用、上傳任何真實軍方班次、名冊、夜查或休假資料。所有回歸案例都是虛構。**

## 確認存在且已修改的缺失

| 分類 | 修正前的具體缺失 | 修正方式 | 驗收範圍 |
|---|---|---|---|
| 正確性／狀態 | `solver/full_month_fair_wire_v3.py` 的 `audit_full_month_fair_v3_response` 允許 `fair_phase='UNKNOWN'` 卻宣稱已證明公平最佳，或 `fill_phase='OPTIMAL'` 卻沒有正確證明標記 | 將填班與公平兩階段的 status/boolean 最優證明、覆蓋上限及 UNKNOWN 無改善情形做相容性檢查；新增七種偽造標記反例 | Python 資料回傳驗證，**不能當作實際 WASM 執行證據** |
| 信任鏈／打包 | 已驗證 WASM JS/binary 的 SHA-256 不等於 HTML 採用的**虛構案例內容**也經真正 Node 求解；舊打包器只檢查案例格式 | `tests/month_fair_real_wasm.cjs` 真正 Node 實跑時，將虛構案例完整位元資料序列化做 `fixture_sha256`；`build/package_month_fair_wasm.py` 用原始檔 bytes 再驗證，內容被換掉即拒絕 | 只認最新 Node 實際測試產出的 manifest hash；原先正在編譯的舊版產物不能單靠舊 proof 直接跳過最新重新執行 |
| HTML 安全 | `build/package_month_fair_wasm.py` 用 `json.dumps(...)` 把案例名稱嵌入 `<script>`，未跳脫 `</script>` 相關字元 | 內嵌 JS JSON 中的 `<`、`>`、`&` 一律轉 Unicode escape；加入 `</script><script>...` 惡意名稱反例 | HTML 打包防護；不代表真實軍務資料可以上傳至公開倉庫 |
| 公平折抵遺漏 | `solver/v7_backup_bridge.py` 能讀取安官督伙禁排，但 `BridgeResult` 原先**沒有督伙的已折抵班數**，移到 v3 公平目標時可能遺漏 | 新增 `meal_credit`；依 v7 原始碼使用同人不同**日曆日期**的集合，僅計當月且重疊不重複；`fair_people_from_v7_bridge()` 明確傳遞業參權重、手動 carry、meal credit | 測試含跨月範圍、重複日期、人工補償，以及 217 安官完整月資料對接；不等於前月自動補償已被核定 |

## 原有且應保留的安全性

- **先合法，再覆蓋，再公平**：資格、休假、受訓、夜查、車勤、值星督伙、人工固定、跨日休息和週日留守不可為公平而放寬。
- 前月已存 schedule 的存在**不等於** `inputSig` 已經過期重算確認；目前 v7 轉換器明確 `cross_month_confirmed=False`，對未核對的前月封存自動補償會拒絕直接套用。
- 先前 [v2 真正 WASM 密集 Node 589 班測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44213148151) 和 [12 組離線 Chromium 合成測試](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44214006711) 已經 success；只是**純填班部分硬限制**，不可以延伸宣稱 v3 兩階段公平已驗證。
- 所有可排資格矩陣即使經過索引匿名化，仍可能透露軍務人力／輪班資料，**不能提交公開 GitHub**。

## 仍未驗證、不可聲稱已完成的事項

1. **真正公平 C++／WASM（v3）**：本輪審核時，[編譯 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216350348) 仍在編譯；任何新 Python/JS 單元測試 success 都不代表真正 Node CP-SAT 公平求解已成功。
2. **完整跨月正確性**：前月班表的 `inputSig` 新鮮度、封存前後有無更動與操作權限，仍需在原 v7.0 本機確認；`cross_month_confirmed=False` 不能擅改為 True。
3. **軟公平不完整**：新版目前目標僅「每個人整月總班數與軟性目標的 L1 偏差」。夜哨四段、午間、安官長班時數、週內業參工作日期分布與跨月長期艱苦均衡仍未在 v3 C++ 目標全部實作。
4. **手機真實性**：離線 Chromium 桌面／手機尺寸模擬不是 iPhone Safari。真實 iPhone 記憶體上限、`file://` 開啟、長時間瀏覽器背景切換、操作凍結尚需實機測試。
5. **部署**：真正實際名冊或勤務不能進入公開 GitHub 及雲端 CI；目前沒有正式可用的軍務人員輸入、核定、跨月新鮮度及版本回復完整簽核流程。

## 驗收依據與禁止跳過的流程

- `tests/test_full_month_fair_wire_v3.py`：驗證矛盾的 `OPTIMAL`／`FEASIBLE`／`UNKNOWN` 狀態不能通過。
- `tests/test_v7_backup_bridge.py`：驗證督伙重複／跨月折抵與 v7→公平目標交接。
- `tests/test_package_month_fair_wasm.py`：驗證 manifest 更換、SHA 不符與 HTML script 逃逸攻擊會被阻擋。
- `.github/workflows/verify.yml`：加跑虛構完整月份公平案例的 Node 靜態預檢（明標非真正 WASM）。
- `.github/workflows/package-month-fair-wasm.yml`：**真正 v3 C++ 編譯 success → 實際 Node 求解＋獨立班次稽核 success → 重新產生並證明案例 hash → 打包 HTML**。任一步失敗，不應產生可下載的「成功公平測試頁」。


## 審查後新增的實證（同日 2026-11-18）

原有「待公平版編譯」狀態已在本輪工作期間更新，**以以下最新實測結果為準**：

- [真正兩階段 v3 C++ OR-Tools WASM 編譯與 Node 驗收 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44216350348)：**completed/success**。小型公平精確 oracle 通過；密集合成大門 372／372（L1 偏差 444 → 4）、安官 217／217（166 → 10）、固定缺班大門 360／372（150 → 6），各組填班與公平階段都回報 `OPTIMAL`，通過獨立排班限制與統計稽核。這些數字僅對虛構模型成立。
- [公平 v3 真正 WASM 離線頁打包 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44221379106)：**completed/success**。在發布前重新呼叫真正 Node WASM，驗證與編譯來源相同的 JS/WASM SHA-256，且核對這次新增的虛構案例完整 SHA-256 和 HTML 字元防護。
- [公平 v3 真正離線 Chromium 驗收 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44221443285)：**completed/success**。四個虛構場景 × 桌面／手機尺寸觸控模擬 = **8/8 成功**，實際 browser WASM 返回合法班數、未惡化且已改善的 L1 偏差；整批桌面約 23.673 秒，手機尺寸模擬約 21.039 秒。**仍不是實體 iPhone Safari 的效能／相容性驗收**。
- [原生、資料轉換及打包防錯 CI #138](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44221054085)：**completed/success**；前一個舊版 CI #136 曾因測試的 Unicode escape 斷言多寫一個反斜線而失敗，修正後再驗證成功。不要隱藏過去的失敗，但最新的成功結果已涵蓋修正。

**提醒**：原本第 1 項「尚未完成真正公平 v3 WASM」現在已完成*指定虛構案例的實測*；第 2～5 項對跨月新鮮度、艱苦哨／值星業參完整公平、iPhone Safari 與正式軍務整合的缺口**依然存在**，不能因 8/8 browser 過關而宣告可正式排哨。

## 實務結論

本次不是「發現系統已全面正常」，而是已找到並修補幾個可能造成**錯誤公平額度或不實驗收宣稱**的具體缺口。部署前的主瓶頸是**v3 真正 C++/WASM 的兩階段求解驗證、完整艱苦公平，以及真實 iPhone Safari／v7 資料一致性**。

本文件中的 CI 結果必須以相應 GitHub workflow 終態為準。若新修改尚未結束 CI，不可寫成「所有測試已通過」。
