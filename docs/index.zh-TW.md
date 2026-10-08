<!-- translation-of: docs/index.md | synced: 2026-10-08 -->

# 文件

[English](index.md)

| 文件 | 回答的問題 |
|---|---|
| [願景與範圍](vision.zh-TW.md) | 為什麼做、給誰用、範圍內外、路線圖 |
| [架構](architecture.zh-TW.md) | 系統如何組成、模組如何接入 |
| [開發指南](development.zh-TW.md) | 本機設定、執行與檢查程式碼；CI |
| [身分](platform/identity.zh-TW.md) | 帳號、登入、session、CSRF 與頻率限制（規則 `AUTH-*`） |
| [記帳模組](modules/finance.zh-TW.md) | 共同帳本與個人帳本的領域模型與業務規則 |
| [威脅模型](security/threat-model.zh-TW.md) | 要保護什麼、防範誰、怎麼防 |
| [ADR](adr/README.zh-TW.md) | 每個重大決策的理由 |
| [文件撰寫指引](contributing/documentation.zh-TW.md) | 文件如何撰寫、翻譯並與程式碼保持同步 |

程式碼完成後，自動產生的參考文件（API、資料庫 ERD、權限表、環境設定）會放在 `docs/reference/`。
這些文件從程式碼產生並由 CI 驗證，請勿手動編輯。
