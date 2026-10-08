<!-- translation-of: docs/adr/0005-postgresql-and-redis.md | synced: 2026-10-08 -->

# ADR-0005：PostgreSQL 作為正式資料來源，Redis 存放可遺失的狀態

- 狀態：已採納
- 日期：2026-10-08

## 背景

資料量很小，即使是數十年的家庭紀錄也只有幾十 MB。但這個系統會長期使用、之後可能有多個服務，而且本來就以 container 運行。

## 決策

- 從第一天就使用 PostgreSQL，每個模組一個 schema。
- Redis 用於 rate limit 計數、Casbin 策略變更通知，之後也用於快取與工作佇列。Redis 絕不存放不能遺失的資料。

## 影響

- 將來不需要從 SQLite 遷移到 PostgreSQL。
- 多出幾個 container（PostgreSQL 約 100 MB 記憶體，Redis 只有幾 MB），NAS 有 4 GB 以上記憶體，足以負擔。
- 備份要用 `pg_dump`，不能直接複製檔案。

## 考慮過的替代方案

- **SQLite：** 以資料量來說足夠，但同時只能有一個寫入者，若第二個服務需要這些資料會很麻煩。
