<!-- translation-of: docs/adr/0003-fastapi-backend.md | synced: 2026-10-08 -->

# ADR-0003：後端採用 FastAPI

- 狀態：已採納
- 日期：2026-10-08

## 背景

作者日常使用 Python，工作上也使用 FastAPI。後端需要為分離的前端提供型別完整的 HTTP API。

## 決策

使用 FastAPI，搭配 SQLAlchemy 2.0（async）、Alembic 做資料庫遷移、Pydantic v2 處理 schema 與設定，並用 uv 管理相依套件與 workspace。

## 影響

- OpenAPI 從程式碼自動產生，因此前端 client 也能自動產生。
- 登入、管理功能與 RBAC 不是內建的，要由平台層提供，並使用成熟的套件，不自己實作密碼學相關邏輯。

## 考慮過的替代方案

- **Django（+ Django Ninja）：** 功能齊全（登入、後台、ORM），但彈性較低，也不是作者日常使用的工具。
