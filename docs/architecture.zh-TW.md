<!-- translation-of: docs/architecture.md | synced: 2026-10-08 -->

# 架構

[English](architecture.md)

## 概覽

Family Hub 是一個**模組化單體**，搭配**分離的前端**（[ADR-0002](adr/0002-modular-monolith-with-separate-frontend.zh-TW.md)）。
一個 FastAPI 程序同時承載共用的「平台」與多個功能「模組」。
React PWA 透過從 OpenAPI 規格自動產生的型別化 client 呼叫 API。

```mermaid
flowchart LR
    subgraph Devices[裝置]
        iPhone[iPhone PWA]
        Browser[網頁瀏覽器]
    end
    subgraph Tailnet["Tailscale（私有網路）"]
        subgraph NAS["Synology NAS · Docker Compose"]
            Caddy[Caddy<br/>靜態檔案 + 反向代理]
            API[FastAPI<br/>平台 + 模組]
            PG[(PostgreSQL)]
            Redis[(Redis)]
        end
    end
    iPhone -- HTTPS --> Caddy
    Browser -- HTTPS --> Caddy
    Caddy -- "/" --> Static[React 建置檔]
    Caddy -- "/api/*" --> API
    API --> PG
    API --> Redis
```

前端與 API 位於同一個網域（`/` 與 `/api`），因此可以使用 `SameSite` 的 session cookie，
也不需要處理 CORS（[ADR-0007](adr/0007-cookie-session-auth.zh-TW.md)）。

## Repo 結構

```
family-hub/
├── apps/
│   ├── api/                    # FastAPI 服務（uv）
│   │   ├── src/family_hub/
│   │   │   ├── platform/       # 登入、使用者、家庭、RBAC、稽核
│   │   │   ├── modules/
│   │   │   │   └── finance/    # 每個模組一個套件
│   │   │   └── main.py         # app factory、模組註冊
│   │   ├── migrations/         # Alembic
│   │   └── tests/
│   └── web/                    # React + TS + Vite PWA（pnpm）
├── packages/
│   └── api-client/             # 由 OpenAPI 自動產生，禁止手動編輯
├── deploy/                     # compose 檔、Caddyfile、備份腳本
└── docs/
```

## 平台

平台負責所有模組都需要的功能：

| 面向 | 職責 |
|---|---|
| 身分 | 使用者、密碼雜湊（Argon2id）、session |
| 租戶 | 家庭與成員關係。每一筆領域資料都帶有 `household_id` |
| 授權 | Casbin RBAC，以家庭作為 domain（[ADR-0006](adr/0006-casbin-rbac-with-domains.zh-TW.md)） |
| 稽核 | 只能新增的紀錄：誰在何時改了什麼 |
| Rate limiting | 以 Redis 計數，登入相關端點更嚴格 |
| 模組註冊 | 探索模組、掛載 router、註冊權限 |

### 角色

角色的範圍限定在家庭內。初始角色：

| 角色 | 適用對象 |
|---|---|
| `owner` | 管理家庭、成員與角色 |
| `adult` | 完整使用各模組 |
| `child` | 受限。實際權限等需要時再定義 |

## 模組合約

模組是 `modules/` 底下的一個 Python 套件，對外只提供一個 `Module` 描述物件，平台不使用模組的其他任何東西。

| 部分 | 說明 |
|---|---|
| `name` | 唯一代稱，如 `finance`。用於 URL 前綴 `/api/v1/<name>` 與資料庫 schema |
| `router` | FastAPI 的 `APIRouter` |
| `permissions` | 模組定義的權限字串，如 `finance.transaction.create` |
| `default_grants` | 內建角色預設擁有哪些權限 |
| models | 放在模組專屬 PostgreSQL schema 中的 SQLAlchemy models |

讓模組保持獨立、未來可拆分的規則：

1. **不跨模組存取資料表。** 模組不 join、不寫入其他模組的資料表，而是呼叫對方的 service 介面。
2. **每個模組一個 PostgreSQL schema**（`platform`、`finance`⋯⋯）。
3. **API 有版本號。** 所有路由都在 `/api/v1/` 底下。
4. **授權用宣告的，不手寫判斷。** 端點透過 `require_permission("<模組>.<資源>.<動作>")` 檢查權限。
5. **擁有者檢查在 service 層。** RBAC 回答「這個角色能不能做這個動作」；
   像「個人帳只有本人看得到」這類規則，在模組的 service 程式碼中檢查。

前端採用相同的結構：每個模組是一個路由資料夾加上一個導覽項目。

## API 合約

FastAPI 產生 `openapi.json`，再由它產生 TypeScript client 與型別，放進 `packages/api-client`。
Pydantic schema 是請求與回應格式的唯一來源。CI 會重新產生 client，若與已 commit 的內容不同就失敗。

## 資料

- **PostgreSQL** 是正式的資料來源（[ADR-0005](adr/0005-postgresql-and-redis.zh-TW.md)）。
- **Redis** 存放 rate limit 計數、Casbin 策略變更的通知頻道，之後也會用於快取與背景工作。
  Redis 裡不放任何不能遺失的資料。
- 金額以整數的最小貨幣單位儲存，並附上 ISO 4217 幣別代碼。
- 上傳的檔案（未來功能）存放在檔案系統，不放進資料庫。

## 環境

| 環境 | 位置 | 資料 | 可存取範圍 |
|---|---|---|---|
| 本機開發 | MacBook | 虛構示範資料 | localhost |
| 正式環境 | Synology DS923+ | 真實家庭資料 | 僅限 Tailscale（[ADR-0009](adr/0009-private-access-via-tailscale.zh-TW.md)） |
| 公開 Demo（之後） | 雲端免費方案，完全獨立 | 虛構資料，沙盒會自動銷毀 | 公開（[ADR-0010](adr/0010-isolated-public-demo.zh-TW.md)） |
