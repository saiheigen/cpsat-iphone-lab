# Python／JavaScript／真正 C++ WASM 勤務規則交叉驗證（2026-11-18）

## 目的與安全範圍

這次只比對**現有共通的虛構同月勤務硬限制**，不重寫已通過的排班引擎，不將外部資料的 `synthetic_only` 標記當成真實性授權。禁止上傳任何真實人員、休假、勤務或機敏資料。

### 實際比對的三個獨立位置

- Python：`solver/phase21_synthetic_cross_month_gate.py` 的 `_conflict`（獨立且不依賴 OR-Tools）。
- JavaScript：`integration/month_audit.cjs` 的 `independentlyAudit`。
- C++：原有 `src/cp_sat_month_hardship_bridge.cc` 編成的**既有 genuine OR-Tools CP-SAT WASM**；此階段未重新編譯 C++，使用本機保存的前期已執行 WASM 二進位，SHA-256 `8929b0d8d98391b557a5d37f681459edf1099d2da7c7a2e6be05f6979b0b993d`。

## 驗證結果

1. `tests/test_cross_language_rule_parity.py`：**2,104 個虛構雙班組合**。同一份案例以 Python `_conflict` 算預期，JavaScript 對完整 2026 年 12 月合成班表進行獨立反向驗證；兩邊**0 項不一致**。涵蓋同日、隔日、兩日、三日、連續與非連續週日邊界；大門與安官分別檢查。
2. `tests/contract_real_wasm_smoke.cjs`：本機載入前期 genuine WASM，針對合成完整月的 14 個核心邊界案例進行**真實 C++ 求解**；合法案例要求 `FEASIBLE/OPTIMAL` 與填兩班，非法固定組合要求 `INFEASIBLE`。14/14 通過，合法解再由獨立 JS 稽核檢查。
3. 先前階段 20～24 的 Python 虛構回歸測試**121/121 通過**；這次沒有修改工作中真正的 C++ 求解器或原有 Python 勤務規則。

### 納入開發流程

- `.github/workflows/ci-fast.yml`：增加 Python↔JS 的真值表測試與 C++ 手動測試腳本語法檢查；一般提交依舊**不需要編譯 WASM**。
- `.github/workflows/phase19-fictional-v7-hard-rule-gate.yml`：在**手動** genuine WASM 發版驗收中追加 14 個真實 WASM 邊界案例；必須從明確指定的 `source_run_id` 下載 WASM，驗證 `js_sha256` 和 `wasm_sha256` 與現有 proof 相同，再獨立檢查；保留成功與失敗元資料，不採用 `UNKNOWN` 當合法結果。

## 工程結論（經測試支持）

**現有的同月休息／同時段／週日留守規則，在這批測試中沒有發現三種實作的語義差異。因此不建議為了「統一」而移除獨立稽核或重新編寫 C++ 模型。** 一般開發以 2,104 筆跨語言真值表作回歸；昂貴的 14 筆 C++ 真實 WASM 案例只在手動驗收時執行。

## 尚未驗證的重點

- **非同月事件與歷史**：JavaScript 同月稽核不會自行還原上月封存與休假、夜查、車勤等事件；C++ 主要相信由來源端編譯的候選遮罩。Python 的虛構跨月審核有另一套測試，但這份比對**不是**原始 v7 全規則逐項認證。
- **真實 v7.0 HTML、`inputSig`、封存核定與權限**：真正來源不在目前 GitHub，無法驗證授權或簽章。
- **高密度效能及 iPhone Safari**：本次故意使用稀疏固定班作規則邊界測試，不能證明 589 班密集求解在 10 秒內完成，也不能宣稱實體 Safari.app 驗收。
- **最優性**：Python/JS 的雙班真值表只驗證可行性；14 組 C++ 回傳的求解器狀態不能外推到完整月的公平或艱苦哨全域最優。

**現況**：release gate 仍為 BLOCKED，且此開發分支尚未合併 main；沒有啟動新的 GitHub Actions。
