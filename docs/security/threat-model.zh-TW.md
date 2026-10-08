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
| **偽冒：** 撞庫、暴力破解 | Argon2id 雜湊；每個 IP 每分鐘最多嘗試登入 10 次；同一帳號失敗 5 次即鎖定 15 分鐘；email 不存在與密碼錯誤的回應完全相同；不開放自行註冊（AUTH-1 至 AUTH-4）。之後加入 TOTP 或 Passkey |
| **偽冒：** session 被竊 | `__Host-` cookie 搭配 `HttpOnly`、`Secure`、`SameSite=Lax`；只儲存 token 雜湊；登出時於伺服器端撤銷；14 天閒置與 60 天絕對逾時；每次登入都產生新 token（AUTH-5、AUTH-6） |
| **竄改：** CSRF | 同源部署、不開放 CORS、`SameSite` cookie，所有會改變狀態的請求都必須在 `X-CSRF-Token` 帶上與 session 綁定的 HMAC token（AUTH-7） |
| **竄改：** 注入攻擊 | 所有輸入經 Pydantic 驗證；只使用 SQLAlchemy 參數化查詢；不以字串拼接 SQL |
| **否認** | 每次寫入都在同一個交易中寫入稽核事件；由資料庫 trigger 強制只能新增（AUDIT-1、AUDIT-2） |
| **資訊洩漏：** 跨家庭存取 | 每筆資料與每個限定家庭的路徑都帶 `household_id`；每個請求都檢查成員關係；非成員得到 404，無法探測 ID；以測試嘗試跨家庭存取（AUTHZ-5） |
| **資訊洩漏：** 配偶讀到個人帳 | service 層的擁有者檢查（FIN-5），並有測試 |
| **資訊洩漏：** 機密進入公開 repo | `.env` 列入 git ignore；pre-commit 與 CI 執行 gitleaks；只使用虛構的示範資料 |
| **資訊洩漏：** XSS | React 預設跳脫輸出；嚴格的 Content-Security-Policy；不使用 `dangerouslySetInnerHTML` |
| **阻斷服務** | 邊緣層與 App 層的 rate limit；請求大小上限；分頁上限 |
| **權限提升** | 預設拒絕；若有路由沒有恰好一個存取規則，API 拒絕啟動；公開路由清單由測試固定；每個請求都重新讀取角色，降級立即生效（AUTHZ-1、AUTHZ-2、ADR-0012） |
| **供應鏈** | Lockfile（uv、pnpm）；Dependabot；pip-audit、pnpm audit；Trivy 掃描 image；GitHub Actions 固定到 commit SHA |
| **從 container 逃逸到 NAS** | 非 root 的 container；盡量使用唯讀的根檔案系統；不掛載 Docker socket；只掛載必要的 volume |
| **資料遺失** | 每晚加密的 `pg_dump`；異地備份；演練過並寫成文件的還原流程 |

## 安全標頭

`Strict-Transport-Security`、`Content-Security-Policy`、`X-Content-Type-Options: nosniff`、
`Referrer-Policy: same-origin`、`Permissions-Policy`（停用不需要的功能）、`frame-ancestors 'none'`。

## 剩餘風險（目前接受）

- Tailscale 的協調伺服器屬於第三方。緩解方式：改為自架 Headscale。
- 單一 NAS 是可用性的單點故障。備份只保護資料，不保證服務不中斷。
- 依 IP 的登入限制取決於真實的用戶端 IP。代理設定錯誤會讓所有使用者共用同一個限制（見 [identity.zh-TW.md](../platform/identity.zh-TW.md#部署注意事項)）。
- 過期的 session 資料尚未刪除。它們無法被使用，但在清理排程完成前資料表會持續增長。
