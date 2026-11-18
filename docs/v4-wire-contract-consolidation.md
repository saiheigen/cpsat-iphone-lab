# v4 求解器資料交接整併驗收（虛構資料，2026-11-18）

**目的：** 不修改現有 C++ CP-SAT v4 勤務限制或 v7 備份格式，把 Python Phase 22 產生的匿名虛構整月資料在 JS 端作位元組不變的協議解析與預檢。

## 已實作

- 新增 integration/v4_frame_contract.cjs，嚴格解析 v4 8 行匿名輸入：協議、年月、池、尺寸、候選矩陣、固定班、起始 hint 與公平目標。拒絕非 ASCII、無終止換行、非標準尺寸、未知月份、格式缺漏與非典型整數；再透過現有 normalize 要求序列化逐字完全相同。
- 強化 integration/phase5_synthetic_adapter.cjs 的 C++ v4 等價輸入前置條件：固定人員／hint 必須可排，固定缺班不可有 hint，hint 不得與固定人員衝突。此修改不放寬任何硬規則。
- 原 JS 測試新增四類拒絕案例；tests/test_v4_wire_contract.py 使用真正 Python Phase 22 產出的虛構大門 372 班／56 人、安官 217 班／50 人跨月 handoff，透過 Node 子程序做同位元組 roundtrip、固定缺班及非法資料測試。
- ci-fast 工作流程增加 Parser 語法與 Python 到 JS 的跨語言測試。未跑雲端 CI。

## 本機驗證

- 階段 20–24 虛構 Python 回歸 121/121 通過。
- CI 策略 Python 測試 4/4 通過。
- 新增跨語言 Python 測試 4/4 通過。
- 既有 JS 整合測試（含新負面案例）通過。
- Python 合計 129 項通過，但不是新 WASM 編譯或手機 Safari 驗收。

## 邊界與禁止誤認

此 Parser 只驗證 wire 結構與原有 C++ v4 輸入前置條件，synthetic_only=true **不代表來源真實或已授權**。它不是 v7 inputSig、新鮮度、封存授權、正式軍務合法性或獨立執行 WASM 的證明。要檢查源頭休假、夜查、車勤和跨月完整規則，仍必須用 Phase 22 原始虛構 source/anchors 重新建構並反向稽核。正式 v7 源 HTML 不在本 GitHub 儲存庫，正式核定發版仍受阻。

沒有修改 main、GitHub 帳戶付費設定或真實軍務資料。
