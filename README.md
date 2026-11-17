# iPhone CP-SAT 單執行緒 WebAssembly 移植實驗

這個私人儲存庫只包含 **Google OR-Tools 的公開程式碼建置腳本與虛構數學題**。請勿上傳真實哨務、軍中人員或其他敏感資料。

## 目前驗收標準

- GitHub Actions 以 Emscripten 編譯真正 OR-Tools CP-SAT C++ 模型
- 產物為 `cp_sat_probe.js` 與 `cp_sat_probe.wasm`
- 在 Node.js **實際載入該 WASM** 並呼叫 `run_cp_sat_probe`
- 必須回報 `OPTIMAL`、`desks=0`、`tables=3`、`profit=90`
- 結果由獨立枚舉器複核
- **只有所有步驟通過**，GitHub Actions 才上傳求解器成品

## 編譯紀錄

[前往 Actions](https://github.com/saiheigen/cpsat-iphone-lab/actions/workflows/cp-sat-wasm-experimental.yml)

注意：工作流程顯示綠燈只代表上述 **虛構小題在 GitHub 執行成功**，還不代表 iPhone HTML Viewer 能夠啟動，更不代表整月 589 班模型已經完成全域最優證明。

## 檔案

- `src/cp_sat_probe.cc`：真正 CP-SAT C++ 模型
- `src/CMakeLists.txt`：單執行緒 Emscripten 封裝
- `build/real_solver_smoke.cjs`：在 Node.js 載入真正 WASM 並驗證結果
- `.github/workflows/cp-sat-wasm-experimental.yml`：自動建置與測試

不含任何真實排班資料；尚未與 v7.0 主程式整合。

## 自動產生 iPhone 單檔驗收頁

最新已新增 `.github/workflows/iphone-html-after-cpsat.yml`：當前一個真正 CP-SAT 編譯工作**成功**，並上傳經驗證的 JS/WASM 後，會自動下載該產物，再次執行 CP-SAT 真實求解及獨立枚舉驗證，檢查 WASM 無共享記憶體，才輸出：

`iPhone_CP-SAT_真正求解驗收.html`

[查看自動封裝執行紀錄](https://github.com/saiheigen/cpsat-iphone-lab/actions/workflows/iphone-html-after-cpsat.yml)

> 編譯失敗時不會產生手機驗收頁。就算產生，也仍需 iPhone HTML Viewer 實際測試，且暫時只處理虛構的二變數小題，不是 589 班整月模型。
