<!-- translation-of: docs/security/threat-model.md | synced: 2026-10-08 -->

# 威脅模型

[English](threat-model.md)

> 這是持續更新的文件。任何改動登入、授權、網路暴露範圍、資料儲存或相依套件的 PR，都要同步更新。

## 資產

| 資產 | 重要性 |
|---|---|
| 家庭財務資料 | 私密。外洩會造成困擾，也可能被用於詐騙或社交工程 |
| 使用者帳密與 session | 取得它們就能存取上述所有資料 |
| NAS 本身 | 還存放著與本系統無關的家庭照片和文件 |
| Repo 與建置流程 | 公開。一旦被入侵，惡意程式碼會被部署進家裡 |

## 環境與信任邊界

| 環境 | 暴露範圍 | 資料 |
|---|---|---|
| 正式環境（NAS） | 僅限 Tailscale，路由器不轉發任何 port | 真實 |
| 公開 Demo（之後） | 網際網路 | 只有虛構資料。基礎設施獨立，沒有任何通往 NAS 的路徑 |
| 本機開發 | localhost | 只有虛構資料 |

**硬性規則：** 真實資料絕不離開正式環境；公開 Demo 絕不在 NAS 上運行（[ADR-0010](../adr/0010-isolated-public-demo.zh-TW.md)）。

## 威脅來源

| 來源 | 適用環境 |
|---|---|
| 網路攻擊者或機器人 | Demo；正式環境只有在違反暴露規則時才適用 |
| Tailnet 中被入侵或遺失的裝置 | 正式環境 |
| 好奇的家庭成員（例如未來的小孩） | 正式環境 |
| 惡意的 Demo 訪客 | Demo |
| 供應鏈攻擊（相依套件、image、CI action） | 全部 |

## 威脅與防護措施

| 威脅（STRIDE） | 防護措施 |
|---|---|
| **偽冒：** 撞庫、暴力破解 | Argon2id 雜湊；登入相關端點依 IP 與帳號限流；失敗後逐步延長等待並暫時鎖定。之後加入 TOTP 或 Passkey |
| **偽冒：** session 被竊 | `HttpOnly`、`Secure`、`SameSite` cookie；可撤銷的伺服器端 session；閒置與絕對逾時；登入時更換 session ID |
| **竄改：** CSRF | 同源部署、`SameSite` cookie，所有會改變狀態的請求額外要求 CSRF token 或自訂標頭 |
| **竄改：** 注入攻擊 | 所有輸入經 Pydantic 驗證；只使用 SQLAlchemy 參數化查詢；不以字串拼接 SQL |
| **否認** | 只能新增的稽核紀錄，記錄每次寫入的操作者、時間、修改前後的值 |
| **資訊洩漏：** 跨家庭存取 | 每筆資料都帶 `household_id`；所有查詢都限定在呼叫者的家庭；以測試嘗試跨租戶存取 |
| **資訊洩漏：** 配偶讀到個人帳 | service 層的擁有者檢查（FIN-5），並有測試 |
| **資訊洩漏：** 機密進入公開 repo | `.env` 列入 git ignore；pre-commit 與 CI 執行 gitleaks；只使用虛構的示範資料 |
| **資訊洩漏：** XSS | React 預設跳脫輸出；嚴格的 Content-Security-Policy；不使用 `dangerouslySetInnerHTML` |
| **阻斷服務** | 邊緣層與 App 層的 rate limit；請求大小上限；分頁上限 |
| **權限提升** | Casbin 預設拒絕；每個端點都宣告權限檢查；若有路由沒宣告，測試就會失敗 |
| **供應鏈** | Lockfile（uv、pnpm）；Dependabot；pip-audit、pnpm audit；Trivy 掃描 image；GitHub Actions 固定到 commit SHA |
| **從 container 逃逸到 NAS** | 非 root 的 container；盡量使用唯讀的根檔案系統；不掛載 Docker socket；只掛載必要的 volume |
| **資料遺失** | 每晚加密的 `pg_dump`；異地備份；演練過並寫成文件的還原流程 |

## 安全標頭

`Strict-Transport-Security`、`Content-Security-Policy`、`X-Content-Type-Options: nosniff`、
`Referrer-Policy: same-origin`、`Permissions-Policy`（停用不需要的功能）、`frame-ancestors 'none'`。

## 剩餘風險（目前接受）

- Tailscale 的協調伺服器屬於第三方。緩解方式：改為自架 Headscale。
- 單一 NAS 是可用性的單點故障。備份只保護資料，不保證服務不中斷。
