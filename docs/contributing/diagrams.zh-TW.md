<!-- translation-of: docs/contributing/diagrams.md | synced: 2026-10-08 -->

# 架構圖

[English](diagrams.md)

架構圖以 Mermaid 原始檔維護，與文件保持同步，並在 CI 中與程式碼比對。

## 位置

| 圖 | 呈現內容 | 出現在 |
|---|---|---|
| 系統情境 | 使用者、Family Hub、外部系統、正式環境與 Demo 的隔離 | [架構](../architecture.zh-TW.md) |
| 容器 | 正式環境中的程序與資料儲存 | [README](../../README.zh-TW.md)、[架構](../architecture.zh-TW.md) |
| API 元件 | API 程序內部的分層 | [架構](../architecture.zh-TW.md) |

虛線框代表規劃中、尚未實作。

## 運作方式

- 每張圖只有一個來源：`docs/diagrams/<名稱>.mmd`。
- Markdown 檔在 `<!-- diagram: <名稱> -->` 與 `<!-- /diagram -->` 之間嵌入圖，`make diagrams` 會改寫這些區塊。
- 標籤只用英文，讓中英文件共用同一份來源。

## 檢查

`scripts/diagrams.py --check`（pre-commit、`make docs-check`、CI）在以下情況會失敗：

- 嵌入的內容與來源不同。
- 來源沒有被任何文件嵌入，或文件嵌入了不存在的名稱。
- API router 的路徑前綴或 Docker Compose 服務沒有出現在圖中。

CI 也會用 mermaid-cli 實際渲染每個來源，語法錯誤會讓建置失敗。

## 更新

修改來源後執行 `make diagrams`。完整流程與慣例寫在
[`.claude/skills/architecture-diagrams/SKILL.md`](../../.claude/skills/architecture-diagrams/SKILL.md)，
AI 助手會依此操作，人也可以直接閱讀。
