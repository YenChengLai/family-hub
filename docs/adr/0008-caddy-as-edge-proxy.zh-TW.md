<!-- translation-of: docs/adr/0008-caddy-as-edge-proxy.md | synced: 2026-10-08 -->

# ADR-0008：以 Caddy 作為邊緣代理

- 狀態：已採納
- 日期：2026-10-08

## 背景

需要一個元件負責提供前端建置檔、把 `/api` 轉發給 FastAPI、處理 TLS，並設定安全標頭。
作者工作上使用 Nginx。使用規模是一個家庭。

## 決策

使用 Caddy。

- 自動 HTTPS，包含從 Tailscale 取得 `*.ts.net` 名稱的憑證。
- Caddyfile 簡短易讀，TLS 預設設定安全。
- 主要的 rate limiting 放在應用程式層，因為它知道使用者與端點。邊緣層的 rate limiting 為選配，需要 `caddy-ratelimit` 外掛（自訂 build）。

## 影響

- 設定與憑證維護的工作較少。
- 邊緣層 rate limiting 不是內建的。
- 代理只是一層薄而可替換的設定，替換時只會動到 `deploy/`。

## 何時重新評估

若需要成熟的邊緣層 rate limiting、處理高流量，或部署到以 Nginx 為標準的環境，就改用 Nginx（或雲端負載平衡器、Ingress）。

## 考慮過的替代方案

- **Nginx：** 業界標準，內建 `limit_req`，但設定較冗長，憑證需手動處理。
- **Traefik：** 以 label 自動探索服務，在服務很多時很好用；只有一個服務時不需要。
