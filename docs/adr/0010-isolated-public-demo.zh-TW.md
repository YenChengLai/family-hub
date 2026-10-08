<!-- translation-of: docs/adr/0010-isolated-public-demo.md | synced: 2026-10-08 -->

# ADR-0010：公開 Demo 與正式環境完全隔離

- 狀態：已採納
- 日期：2026-10-08

## 背景

這個專案是作品集，面試官應該能實際操作。正式環境把真實的家庭資料存放在必須保持私密的 NAS 上
（[ADR-0009](0009-private-access-via-tailscale.zh-TW.md)）。

## 決策

公開 Demo **絕不在 NAS 上運行**，也絕不接觸真實資料。它是同一份程式碼，部署在獨立的基礎設施上。

第一階段（隨 MVP）：
- 本機 `docker compose up`，搭配虛構的示範資料。
- README 附上截圖與 GIF。

第二階段（穩定後）：
- 部署到雲端的免費方案（例如 Cloud Run、Neon、Upstash、Cloudflare Pages），上線前確認額度限制。
- 「試用 Demo」為每位訪客建立一個**臨時的沙盒家庭**，內含示範資料，不需要註冊或 email。
- 沙盒 24 小時後失效，每晚有排程清除所有資料。
- 依 IP 限制建立沙盒的次數，並搭配 Cloudflare Turnstile。
- 停用敏感功能（改密碼、邀請成員），並限制資料量。

## 影響

- 即使 Demo 被入侵，也無法觸及家中網路。
- 沙盒設計會公開展示多租戶、RBAC、rate limiting 與資料生命週期管理。
- 免費方案的限制與冷啟動可能讓 Demo 較慢，可以接受。

## 考慮過的替代方案

- **把 Demo 放在 NAS，透過 Cloudflare Tunnel 公開：** 一旦 container 逃逸，家庭資料就會暴露。不採用。
- **只有前端、搭配模擬 API 的 Demo：** 零風險，但完全無法展示後端成果。可作為補充。
