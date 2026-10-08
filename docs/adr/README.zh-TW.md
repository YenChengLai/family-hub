<!-- translation-of: docs/adr/README.md | synced: 2026-10-08 -->

# 架構決策紀錄（ADR）

[English](README.md)

| ADR | 標題 | 狀態 |
|---|---|---|
| [0001](0001-record-architecture-decisions.zh-TW.md) | 記錄架構決策 | 已採納 |
| [0002](0002-modular-monolith-with-separate-frontend.zh-TW.md) | 模組化單體搭配分離的前端 | 已採納 |
| [0003](0003-fastapi-backend.zh-TW.md) | 後端採用 FastAPI | 已採納 |
| [0004](0004-react-typescript-pwa-with-generated-client.zh-TW.md) | React + TypeScript PWA，搭配自動產生的 API client | 已採納 |
| [0005](0005-postgresql-and-redis.zh-TW.md) | PostgreSQL 作為正式資料來源，Redis 存放可遺失的狀態 | 已採納 |
| [0006](0006-casbin-rbac-with-domains.zh-TW.md) | 以 Casbin RBAC with domains 實作授權 | 已採納，部分被 0012 取代 |
| [0007](0007-cookie-session-auth.zh-TW.md) | 以 HttpOnly cookie 承載伺服器端 session | 已採納 |
| [0008](0008-caddy-as-edge-proxy.zh-TW.md) | 以 Caddy 作為邊緣代理 | 已採納 |
| [0009](0009-private-access-via-tailscale.zh-TW.md) | 正式環境僅能透過 Tailscale 存取 | 已採納 |
| [0010](0010-isolated-public-demo.zh-TW.md) | 公開 Demo 與正式環境完全隔離 | 已採納 |
| [0011](0011-bilingual-docs-as-code.zh-TW.md) | 雙語 docs-as-code，與程式碼保持一致 | 已採納 |
| [0012](0012-code-defined-policies-roles-from-memberships.zh-TW.md) | 權限策略寫在程式碼中；角色在每個請求時從成員關係讀取 | 已採納 |

新增 ADR：參照既有 ADR 的結構，取下一個編號，並同時加入英文與中文索引。
