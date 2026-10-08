<!-- translation-of: docs/platform/audit.md | synced: 2026-10-08 -->

# 稽核紀錄

[English](audit.md)

永久記錄誰在何時改了什麼。它能回答家人之間「這筆支出是誰改的？」，也能在事件發生後協助調查。

## 規則

| 編號 | 規則 |
|---|---|
| AUDIT-1 | 透過 API 或管理 CLI 所做的每次寫入，都會在**同一個交易**中記錄稽核事件，讓變更與紀錄一起提交或一起回滾。沒有改變的值不會被記錄。 |
| AUDIT-2 | 紀錄**只能新增，由 PostgreSQL 強制執行**：trigger 會拒絕對 `platform.audit_events` 的所有 `UPDATE` 與 `DELETE`，不論應用程式怎麼做。 |
| AUDIT-3 | 事件絕不包含機密。名為 `password`、`password_hash`、`token`、`token_hash` 或 `secret` 的欄位會在寫入前移除。 |
| AUDIT-4 | 事件儲存使用者與家庭的 ID 時**不使用外鍵**，因此即使原資料被刪除，事件仍會保留。 |

## 事件欄位

| 欄位 | 意義 |
|---|---|
| `occurred_at` | 寫入時的資料庫時間 |
| `source` | `api` 或 `cli` |
| `actor_user_id` | 操作者。CLI 操作時為空 |
| `household_id` | 受影響的家庭。登入等帳號事件時為空 |
| `action` | `<區域>.<實體>.<動作>`，例如 `platform.household.update` |
| `entity_type`、`entity_id` | 被變更的對象 |
| `before`、`after` | 只包含有變更的欄位（JSON） |

## 會記錄的操作

| 操作 | 來源 | 家庭 |
|---|---|---|
| `auth.login`、`auth.logout` | api | — |
| `platform.household.create` | cli | ✓ |
| `platform.member.add` | cli | ✓ |
| `platform.household.update` | api | ✓ |

家庭的 owner 可透過 `GET /api/v1/households/{household_id}/audit-events` 讀取該家庭的事件
（見 [authorization.zh-TW.md](authorization.zh-TW.md#家庭-api)）。帳號事件（登入、登出）不屬於任何家庭，因此不會出現在那裡。

## 尚未涵蓋

- 登入失敗不寫入稽核紀錄，而是由頻率限制計數（[identity.zh-TW.md](identity.zh-TW.md)，AUTH-4）。
- 保存期限：目前永久保存。
