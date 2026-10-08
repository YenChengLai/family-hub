<!-- translation-of: docs/adr/0011-bilingual-docs-as-code.md | synced: 2026-10-08 -->

# ADR-0011：雙語 docs-as-code，與程式碼保持一致

- 狀態：已採納
- 日期：2026-10-08

## 背景

文件必須隨著程式碼變動保持正確。讀者包括家人（繁體中文）與國際的審閱者（英文）。

## 決策

- 文件以 Markdown 放在 `docs/`，與它描述的程式碼在同一個 PR 中審閱。
- **以英文為正本。** 每份手寫文件 `x.md` 都有譯本 `x.zh-TW.md`，譯本第一行為
  `<!-- translation-of: <路徑> | synced: YYYY-MM-DD -->`。
- **自動產生的參考文件只有英文**，且禁止手動編輯：OpenAPI 規格、資料庫 ERD、權限矩陣、環境設定參考。
  CI 會重新產生，若 `git diff` 有差異就失敗。
- CI 檢查每份英文文件都有譯本，且內部連結都有效。
- PR 範本的檢查清單與 repo 的 `CLAUDE.md` 要求程式變更時同步更新文件。
- 內容足夠時以 MkDocs Material 與其 i18n 外掛發布；在那之前直接在 GitHub 上閱讀。

詳見[文件撰寫指引](../contributing/documentation.zh-TW.md)。

## 影響

- 自動產生的文件不可能帶著不一致被合併。手寫文件的落差由審閱與檢查清單把關。
- 翻譯增加工作量。由 AI 助手起草譯文，再由人審閱。
