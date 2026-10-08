<!-- translation-of: docs/adr/0002-modular-monolith-with-separate-frontend.md | synced: 2026-10-08 -->

# ADR-0002：模組化單體搭配分離的前端

- 狀態：已採納
- 日期：2026-10-08

## 背景

我們從一個模組（記帳）開始，預期之後還會有更多（行事曆、採買清單，以及目前未知的系統）。
每個新模組都要能輕鬆接入，並沿用登入、家庭與權限。系統跑在一台 NAS 上，使用者是 2–3 人的家庭。
這也是作品集，清楚的 API 邊界很有價值。

## 決策

- 後端：一個可部署的 FastAPI 服務，內含共用的**平台**與獨立的**模組**，遵循 [architecture.zh-TW.md](../architecture.zh-TW.md) 中的模組合約。
- 前端：獨立的 React SPA/PWA，呼叫有版本號的 HTTP API。
- 程式碼放在同一個 monorepo。

## 影響

- 一個程序、一個資料庫、一次部署，維運成本低。
- 模組規則（獨立 schema、不跨模組存取資料表）保留了日後把模組拆成獨立服務的可能。
- 前後端分離代表要維護兩套工具鏈（uv 與 pnpm）以及 API 合約。以自動產生的 client 降低負擔
  （[ADR-0004](0004-react-typescript-pwa-with-generated-client.zh-TW.md)）。

## 考慮過的替代方案

- **一開始就做微服務：** 以這個規模來說，維運負擔太重。
- **伺服器端渲染的單體（Django + HTMX）：** 程式碼較少，但 API 邊界較弱，在 iPhone 上也比較不像 App。
  最後選擇 FastAPI 方案（[ADR-0003](0003-fastapi-backend.zh-TW.md)）。
