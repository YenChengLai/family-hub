<!-- translation-of: docs/contributing/documentation.md | synced: 2026-10-08 -->

# 文件撰寫指引

[English](documentation.md)

說明本 repo 的文件如何撰寫，以及如何與程式碼保持同步。
理由見 [ADR-0011](../adr/0011-bilingual-docs-as-code.zh-TW.md)。

## 文件種類

| 種類 | 位置 | 撰寫方式 | 語言 |
|---|---|---|---|
| 概覽、架構、模組設計 | `docs/*.md`、`docs/modules/` | 手寫 | 英文 + 繁中 |
| 決策 | `docs/adr/` | 手寫 | 英文 + 繁中 |
| 資安 | `docs/security/` | 手寫 | 英文 + 繁中 |
| 維運手冊 | `docs/operations/` | 手寫 | 英文 + 繁中 |
| 參考文件（API、ERD、權限、設定） | `docs/reference/` | **自動產生** | 僅英文 |

## 規則

1. **文件與程式碼在同一個 PR 修改。** PR 若改變行為、業務規則、端點、權限或部署方式，就要更新對應的文件。
2. **功能開發文件先行。** 在實作之前或同時更新模組文件，而不是事後補。
3. **以英文為正本。** 先寫或修改英文文件，再於同一個 PR 更新 `.zh-TW.md` 譯本，並更新其 `synced` 日期。
4. **禁止手動編輯自動產生的文件。** 修改程式碼後重新產生。
5. **業務規則都有編號**（例如 `FIN-2`）。測試在名稱或 docstring 中引用編號，讓規則和測試可以雙向追溯。
6. **重大決策要寫 ADR。** 「重大」指難以回頭，或新加入的人會問「為什麼？」的決策。

## 譯本標頭

每份譯本的開頭都是：

```
<!-- translation-of: docs/path/to/file.md | synced: YYYY-MM-DD -->
```

若英文檔案在 `synced` 日期之後有變更，代表譯本已過時。

## 預計加入的 CI 檢查

以下檢查會隨程式骨架一起加入：

- 重新產生參考文件，若 `git diff` 有差異就失敗。
- 每份英文文件都有對應的 `.zh-TW.md`，且標頭格式正確。
- Markdown 內部連結都有效。
