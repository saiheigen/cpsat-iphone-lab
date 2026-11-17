# 驗證狀態

以下為不同層級，必須分開報告：

| 檢驗 | 完成條件 | 目前 |
| --- | --- | --- |
| GitHub 存放庫授權 | 可讀、可建立檔案 | 已連動、可寫入 |
| WASM 工具鏈 | GitHub Action 構建並成功執行 17+25 | 未確認 CI 結果 |
| iPhone HTML Viewer 基礎 WASM | 實機開啟 artifact 單檔並顯示成功 | 待實測 |
| 原生 CP-SAT | Linux OR-Tools 回傳 OPTIMAL，且解為 x=0 y=3 | 未確認 CI 結果 |
| 真正 CP-SAT WASM | JS 實際載入真實 CP-SAT WASM 並回傳 OPTIMAL | 未完成 |
| iPhone CP-SAT | 指定 iPhone HTML Viewer 回傳真實 OPTIMAL | 未完成 |
| 589 班整月數學最優 | 372 大門 + 217 安官完成合法建模、解與證明 | 未完成 |

GitHub Action 及手機應分別留存實際執行結果；**不要因為驗證腳本存在就寫「測試成功」。**
