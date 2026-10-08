<!-- translation-of: docs/development.md | synced: 2026-10-08 -->

# 開發指南

[English](development.md)

## 事前準備

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | 3.13 以上 | API |
| [uv](https://docs.astral.sh/uv/) | 最新版 | Python 相依套件與 workspace |
| Node.js | 22 以上 | 網頁 App |
| [pnpm](https://pnpm.io/) | 10 | JavaScript 相依套件與 workspace |
| Docker | 近期版本皆可 | 本機開發用的 PostgreSQL 與 Redis |

主要的開發機器是 macOS，WSL 的操作方式相同。

## 第一次設定

```sh
make setup                       # uv sync + pnpm install
cp .env.example apps/api/.env    # 本機設定，已列入 git ignore
make deps-up                     # 在 127.0.0.1 啟動 PostgreSQL + Redis
make migrate                     # 套用資料庫遷移
make seed                        # 虛構帳號：alice@example.com / bob@example.com
uvx pre-commit install           # 每次 commit 時自動檢查
```

## 日常開發

開兩個終端機分別執行：

```sh
make api   # http://localhost:8000，互動式文件在 /api/v1/docs
make web   # http://localhost:5173，會把 /api 轉發給 API
```

打開 http://localhost:5173，以 `alice@example.com` 和 `make seed` 印出的密碼登入。

網頁開發伺服器會轉發 `/api`，讓瀏覽器看到的是同一個網域，與正式環境中 Caddy 的行為一致。

## 檢查

| 指令 | 執行內容 |
|---|---|
| `make lint` | ruff（檢查與格式）、ESLint |
| `make typecheck` | mypy（strict）、tsc |
| `make test` | pytest。標記為 `integration` 的測試需要先 `make deps-up` |
| `make docs-check` | 譯本配對、譯本標頭、內部連結、架構圖是否同步 |
| `make diagrams` | 把架構圖來源同步進文件並渲染檢查（[指引](contributing/diagrams.zh-TW.md)） |
| `make check` | 以上全部。開 PR 前請執行 |

整合測試使用獨立的資料庫（`<名稱>_test`，會自動建立）與 Redis 第 15 號資料庫，不會動到開發資料。

只跑不需要外部服務的測試：

```sh
cd apps/api && uv run pytest -m "not integration"
```

## 設定

API 讀取 `FH_` 開頭的環境變數，或 `apps/api/.env`。詳見 `apps/api/src/family_hub/config.py`。

| 變數 | 預設值 | 意義 |
|---|---|---|
| `FH_ENVIRONMENT` | `development` | `development`、`test` 或 `production`。正式環境會關閉互動式 API 文件 |
| `FH_DATABASE_URL` | 本機開發資料庫 | 使用 `asyncpg` driver 的 PostgreSQL URL |
| `FH_REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `FH_SECRET_KEY` | 不安全的開發用值 | CSRF 金鑰。正式環境必填 |
| `FH_COOKIE_SECURE` | `true` | `.env.example` 中設為 `false`，讓本機純 HTTP 也能登入 |

Session 相關設定列於 [identity.zh-TW.md](platform/identity.zh-TW.md#設定)。

第 1c 階段會以自動產生的設定參考文件取代這張表。

## 資料庫遷移

```sh
cd apps/api
uv run alembic revision --autogenerate -m "描述這次的變更"
uv run alembic upgrade head
```

每個自動產生的遷移檔都要先檢查過再 commit。

## 持續整合（CI）

每個 pull request 與 `main` 都會執行 GitHub Actions：

| Job | 檢查內容 |
|---|---|
| `api` | ruff、mypy、資料庫遷移、`alembic check`（models 與遷移檔一致）、對真實 PostgreSQL 與 Redis 執行 pytest |
| `web` | ESLint、型別檢查、正式版建置 |
| `docs` | `scripts/check_docs.py`；`scripts/diagrams.py --check --render` |
| `secrets` | 以 gitleaks 掃描完整歷史 |

Dependabot 每週為 Python 與 JavaScript 開一次合併的更新 PR，每月更新 GitHub Actions 與 Docker image。
Docker image 的大版本更新會被略過：請刻意安排升級，並讓開發、CI 與正式環境維持相同版本（PostgreSQL 大版本升級需要匯出再匯入資料）。

## 已知限制

- TypeScript 固定在 6.x，因為 typescript-eslint 尚未支援 TypeScript 7。
- PWA 圖示目前只有 SVG。iOS 主畫面圖示需要 PNG，會在做 UI 時補上。
