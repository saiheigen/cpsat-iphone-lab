# 離線整月整合入口（只使用虛構資料）

## 完成了什麼

這次把既有的四個已測試元件串成單一可重跑路徑：
`Phase20/21` 原始跨月封存與事件 → `Phase22` 兩組匿名 v4 月份輸入 → genuine C++ CP-SAT WASM → `Phase22` 用原始虛構事件/封存再次獨立反向稽核 → 只輸出不含班表的人員統計與安全狀態。

原有 Python、JavaScript 和 C++ 勤務規則沒有改動，`main` 沒有改動，也沒有使用真實軍務資料。

### 路徑

- `tools/fictional_offline_pipeline.py`：固定內建的虛構 2026-11/12 來源；刻意添加虛構「全免」事件，讓十二月 372+217 共 589 行只有少數候選人可值勤；封存與當月事件會重新推算 SHA-256；呼叫本機 Node/WASM 並重建完整來源做獨立查核。
- `integration/fictional_genuine_wasm_runner.cjs`：本機讀取已編好的真實 `module.js/.wasm` 和既有 proof，核對 WASM 和 JS 哈希、匿名 wire 哈希與 v4 格式。真正執行 `solve_guard_month_harsh_v4` 並把求解結果交回 Python；不呼叫外部網路。
- `tests/test_fictional_offline_pipeline.py`：13 項純本機虛構案例，測試資料行數、原始封存重驗、`UNKNOWN`/偽造 assignments 擋下、來源遭竄改、偽造填班數、檔案缺失與哈希錯誤。
- `ci-fast.yml`：日常只跑上述 13 項輕量測試及 JS 語法檢查，不編譯／執行真正 WASM。
- `phase19-fictional-v7-hard-rule-gate.yml`：僅手動的發版驗收；在已有的 genuine WASM / proof 核對及 14 個邊界案例之後再完整執行上述整合路徑，附上不包含原始勤務的 JSON 摘要。

## 本機實際測試結果

使用先前通過合成測試的真正 C++ CP-SAT WASM 在本機重新求解：WASM SHA-256 是 `8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d`；在這次虛構稀疏情境中大門 `OPTIMAL`（3/372）、安官 `OPTIMAL`（1/217），合計 4/589。完整原始事件加上前月封存經 Python 反向檢查通過。沒有增加 GitHub Actions run。

本機 13/13 新單元測試及此前 121/121 階段 20–24 回歸測試通過；本機還刻意修改了既有 proof 或使用錯誤 WASM SHA，均遭拒絕。**這次沒有重新編譯 C++，也不是 iPhone Safari.app 的實機驗收。**

## 本機執行方式

在 repo root 且已安裝 Python 3.11+ 與 Node.js 22、準備**從可信來源個別核對哈希**的實際 v4 C++ WASM 三件檔案之後：

```bash
python -m tools.fictional_offline_pipeline \
  --wasm-js /LOCAL_PATH/cp_sat_month_hardship_bridge.js \
  --wasm-bin /LOCAL_PATH/cp_sat_month_hardship_bridge.wasm \
  --proof /LOCAL_PATH/full_month_hardship_wasm_proof.json \
  --trusted-wasm-sha256 YOUR_INDEPENDENTLY_VERIFIED_64_HEX_SHA256 \
  --output ./synthetic_e2e_summary.json
```

`--trusted-wasm-sha256` **不能盲目從同一個不可信檔案複製**；它只是由外部核對後傳入的 SHA-256，並非數位簽章，也不會自動證明製作者身分。此指令故意**沒有接受使用者實際軍務名冊或備份的參數**。

若任一工作池回傳 `UNKNOWN`、`INVALID_INPUT` 或 `INFEASIBLE`，報告只標記 `BLOCKED`，不接受或輸出班表；被竄改的來源、固定班／候選遮罩、求解結果或不一致的 wasm/proof 直接拒絕。

## 對目前整合的限制

這是**故意稀疏、滿足固定限制的工程測試**，4/589 不是高密度排班能力或績效。尚未證明正式 v7 原始 `inputSig`／封存合法來源，沒有對全部 v7 規則與軍務核定權限的正式驗收；不會允許將這份摘要轉成 `guard-offline-v5` 備份。密集月份仍可能在 10 秒第一階段回傳 `UNKNOWN`。

**下一個真正的工作**應是把這套只處理虛構資料的安全交接逐步接到 iPhone 離線 UI，而非再新增一個排班演算法或自動上傳實際資料。
