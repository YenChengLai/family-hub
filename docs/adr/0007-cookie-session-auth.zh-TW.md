<!-- translation-of: docs/adr/0007-cookie-session-auth.md | synced: 2026-10-08 -->

# ADR-0007：以 HttpOnly cookie 承載伺服器端 session

- 狀態：已採納
- 日期：2026-10-08

## 背景

前端與 API 位於同一個網域。存放在 `localStorage` 的 token 會被任何 XSS 竊取。
我們希望 session 能立即撤銷（例如手機遺失時）。

## 決策

- 伺服器端 session，以隨機 ID 存放在 cookie 中，屬性為 `HttpOnly; Secure; SameSite=Lax`（若不影響使用體驗則用 `Strict`）。
- 登入時更換 session ID；設定閒置逾時與絕對逾時。
- 所有會改變狀態的請求都有 CSRF 防護（token 或必要的自訂標頭）。
- 密碼以 Argon2id 雜湊。
- 登入流程放在一個介面後面，日後若非 Python 的服務需要單一登入，可以改用 OIDC 提供者替換。

## 影響

- 可以立即撤銷，也沒有 token 更新的複雜度。
- 每個請求都要查詢 session 儲存，以我們的規模可忽略。

## 考慮過的替代方案

- **JWT access + refresh token：** 無狀態，但難以撤銷，且常見的 `localStorage` 存法容易被 XSS 竊取。
- **專用的身分提供者（Authentik、Keycloak）：** 對 NAS 來說太重（1–2 GB 記憶體）。等第二個獨立服務需要 SSO 時再評估。
