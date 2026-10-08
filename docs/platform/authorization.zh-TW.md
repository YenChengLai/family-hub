<!-- translation-of: docs/platform/authorization.md | synced: 2026-10-08 -->

# 授權：角色、權限與存取規則

[English](authorization.md)

說明誰可以做什麼。設計理由見 [ADR-0006](../adr/0006-casbin-rbac-with-domains.zh-TW.md)
與 [ADR-0012](../adr/0012-code-defined-policies-roles-from-memberships.zh-TW.md)。

## 規則

| 編號 | 規則 |
|---|---|
| AUTHZ-1 | **預設拒絕。** 沒有被宣告的權限永遠不會被授予。 |
| AUTHZ-2 | **每個路由都宣告恰好一個存取規則：** `public`、`authenticated` 或 `require_permission("<權限>")`。若有路由沒宣告、宣告超過一個，或引用了不存在的權限，API 會拒絕啟動。公開路由的清單由測試固定。 |
| AUTHZ-3 | **角色可繼承：** `owner` ⊇ `adult` ⊇ `child`。授予 `child` 的權限，`adult` 與 `owner` 也都擁有。 |
| AUTHZ-4 | **模組自行宣告權限**，格式為 `<模組>.<資源>.<動作>`，並授予角色。命名錯誤、重複、未宣告的權限，或功能模組的路由不在 `/<模組>` 底下，都會讓啟動失敗。 |
| AUTHZ-5 | **限定家庭的路由都包含 `{household_id}`。** 每個請求都從 `memberships` 讀取呼叫者的角色。非成員一律得到 **404**，與家庭不存在時相同，因此無法探測 ID。是成員但沒有權限則得到 403。 |

擁有者規則（例如個人帳本只有擁有者看得到，FIN-5）不是角色，而是在各模組的 service 層檢查。

## 存取規則

| 規則 | 誰可以通過 | 用於 |
|---|---|---|
| `public` | 任何人 | 健康檢查、登入、登出 |
| `authenticated` | 任何已登入的使用者 | `GET /auth/session` |
| `require_permission(p)` | `{household_id}` 的成員，且其角色擁有 `p` | 所有限定家庭的功能 |

## 平台權限

| 權限 | owner | adult | child |
|---|:-:|:-:|:-:|
| `platform.household.read` | ✓ | ✓ | ✓ |
| `platform.household.manage` | ✓ | — | — |
| `platform.audit.read` | ✓ | — | — |

功能模組的權限列在各模組文件中，例如 [finance.zh-TW.md](../modules/finance.zh-TW.md#權限初始)。

## 家庭 API

| 方法與路徑 | 權限 | 用途 |
|---|---|---|
| `GET /api/v1/households/{household_id}` | `platform.household.read` | 名稱、時區、成員與其角色 |
| `PATCH /api/v1/households/{household_id}` | `platform.household.manage` | 改名、更改時區（IANA 名稱）。會寫入稽核紀錄 |
| `GET /api/v1/households/{household_id}/audit-events` | `platform.audit.read` | 最新的稽核事件，由新到舊（`limit` 1–200，預設 50） |

## 為模組加入權限

```python
FINANCE = Module(
    name="finance",
    routers=(router,),  # 每個路由都以 /finance 開頭
    permissions=(Permission("finance.transaction.create", "Record a transaction"),),
    grants={Role.ADULT: frozenset({"finance.transaction.create"})},  # owner 會繼承
)
```

把描述物件加進 `apps/api/src/family_hub/modules/__init__.py` 的 `MODULES`，
再於每個路由加上 `Depends(require_permission("finance.transaction.create"))`。
