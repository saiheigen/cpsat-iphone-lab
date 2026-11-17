# 第九階段工程紀錄｜規則一致性、動態 WASM 離線頁與多引擎驗證

更新日期：2026-11-18，台灣時間。所有測試使用虛構資料，尚不適用於正式軍務班表。

## 已查證並修正的規則差異

重新對照本專案提供的原始 `哨務工作台_v7.0_一鍵整月自動最佳化版.html` 的 `conflict(p,t,occupied)`：
- 相鄰日期站一歇一、同時段兩日內重複、同日勤務間隔與每日時數屬於強制限制。
- 「連續星期日留守」只有當兩班間隔 **7 天**且都屬週日留守才禁排。
- 同一個星期日若兩班相隔至少六小時、每日總時數合格，v7 的 `conflict` 並不因「同週日留守」而單獨禁止這兩班。

原 `solver/roster_cp_sat.py` 錯誤地在相鄰兩週日建立 `sum(本週留守+次週留守) <= 1`，意外禁止同週日合法的兩個大門班次。現已改為 **兩週日之間的每一對班次衝突限制**，保留同週日適當休息的多班可能性，並和 `solver/wasm_assignment_adapter.py` 使用的 `conflicts()` 配對邏輯對齊。

測試包括：
- 2026/12/6 06–08 與 14–16 同人合法；次週 12/13 06–08 不可再排同人。
- `tests/test_roster_cp_sat.py` 與 `tests/test_wasm_assignment_adapter.py` 新增明確回歸。
- `tests/test_synthetic_bruteforce.py` 的 **180 個不同虛構小型案例**，在独立枚舉、原生 CP-SAT、分池回退策略與匿名 WASM 協議枚舉之間最大填班數一致；[CI #8 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44201372982)。
- [原生及基礎 WASM CI #76 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44201373028)。

**測試界線：** 此審核對齊目前 v7 中已可直接見到的衝突判斷及局部模型，不等於所有軍方排班法規已獲第三方獨立認證。

## WebKit 真正求解成功，與 `file://` 不可混稱

- 最早真正 Chromium：可直接從本機 `file://` 開啟已打包的 9.3 MB 單檔 HTML、斷網求解、回傳真正 CP-SAT OPTIMAL；包含桌面與手機尺寸模擬。
- Linux Playwright WebKit 初次失敗原因：Playwright 容器內對 `file://` 直接導覽顯示 `WebKit encountered an internal error`。不是 CP-SAT 本身計算失敗。
- 後續測試 **明確改為 WebKit 內嵌文件載入**，不再聲稱已驗證本機檔案導覽；在 `offline=True`、零外部 HTTP 請求下，真正 WebKit 成功載入 JS+WASM、計算並回傳 OPTIMAL（虛構小題），約 288 ms。
- [GitHub browser CI #5 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44201573787) 清楚記錄 `loading_mode=inline-document`、`file_url_loading_proven=false`、`real_iphone_safari=false`。
- **尚未通過**：iPhone 真實 Safari 實機的 HTML 本機開啟、記憶體、長時間求解。

## 動態 CP-SAT WASM 與安全銜接工程

- [動態 C++/WASM 編譯 #1](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199192306) 本階段仍在進行，已編譯成敗與獨立數值檢查須以該 run 最終結果為準。
- `src/cp_sat_assignment_bridge.cc` 只能處理**最多 64 班、24 人**的匿名 eligibility + conflict pairs + fixed assignments，不含完整 589 班、不含跨月補償與公平。
- `solver/wasm_assignment_adapter.py` 的單位與人員轉換以索引表示，超過規格即拒絕；回傳結果必須由 Python `independently_check()` 重新核對。
- [原生銜接 CI #68 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44199657912)。

## 這次新完成的自動驗收鏈（待真實動態 WASM 產物）

**只有動態 C++/WASM CI 成功、Node 真正呼叫 CP-SAT 並由獨立枚舉驗證後，才繼續：**

1. `.github/workflows/package-dynamic-wasm.yml` 下載真實 WASM artifact，**再次 Node 實跑**四種虛構指派題。
2. `build/package_dynamic_assignment.py` 檢查完整求解結果、獨立最佳填班數、非法輸入拒絕測試、JS/WASM SHA-256，製作單檔 `dynamic_cp_sat_offline_demo.html`；未成功不產出。這是 *測試頁*，不是正式系統。
3. `tests/test_package_dynamic_assignment.py`：只使用刻意假造的最小二進位檔測試包裝防錯；**這些單元測試不能當成真正 WASM 驗收**。原生 [CI #75 success](https://github.com/saiheigen/cpsat-iphone-lab/actions/runs/44201120948)。
4. `.github/workflows/browser-dynamic-wasm.yml`：只有真正動態離線頁打包成功才自動下載，Playwright 真正 Chromium 離線執行四個虛構情境、對照頁面的獨立枚舉，留存 JSON 證據；失敗時保留錯誤與截圖。

**目前不應宣稱**真正動態 WASM 編譯、動態離線頁打包、四題瀏覽器測試及 iPhone Safari 已完成，除非相應 GitHub CI 實際 `success`。

## 下一個工程瓶頸

完成真實動態 WebAssembly 最低限度的 Node、HTML、Chromium 三道證明；再擴張模型到整月 589 班與 106 人並補齊所有軍務硬規則、跨月補償及分層公平；最後由真實 iPhone Safari 驗收。不可以透過隨意分割 64 班繞開上限，因為會遺失跨區間休息與跨月衝突。
