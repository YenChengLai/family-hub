<!-- translation-of: docs/adr/0004-react-typescript-pwa-with-generated-client.md | synced: 2026-10-08 -->

# ADR-0004：React + TypeScript PWA，搭配自動產生的 API client

- 狀態：已採納
- 日期：2026-10-08

## 背景

介面必須同時支援 iPhone 與網頁，運行成本要趨近於零。作者偏好 Python，希望手寫維護的 TypeScript 越少越好。

## 決策

- React + TypeScript + Vite，以可安裝的 PWA 形式提供。
- 從 FastAPI 的 OpenAPI 規格自動產生 TypeScript API client 與型別，放在 `packages/api-client`。自動產生的程式碼禁止手動修改。
- 伺服器狀態以 TanStack Query 管理。

## 影響

- 不需要 Apple 開發者計畫的年費，也不需要 App Store 審核。
- 後端 schema 改變時，前端會在建置階段出現型別錯誤。
- 受 iOS PWA 的限制：網頁推播需要先加入主畫面；離線支援有限。

## 考慮過的替代方案

- **原生 App（Flutter、React Native）：** 要在 iPhone 上長期安裝，需要付費的 Apple 開發者帳號。
- **Vue 或 Svelte：** 可行，但生態系較小，在求職市場上也較少見。
- **Python UI 框架（Reflex、NiceGUI）：** 不是真正的前後端分離；作品集價值較低。
