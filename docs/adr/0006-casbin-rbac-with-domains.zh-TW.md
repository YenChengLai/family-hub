<!-- translation-of: docs/adr/0006-casbin-rbac-with-domains.md | synced: 2026-10-08 -->

# ADR-0006：以 Casbin RBAC with domains 實作授權

- 狀態：已採納；策略儲存與 watcher 部分已被 [ADR-0012](0012-code-defined-policies-roles-from-memberships.zh-TW.md) 取代
- 日期：2026-10-08

## 背景

使用者屬於某個家庭，並在家庭中擁有一個角色。各模組定義自己的權限。作者在工作上已經使用 Casbin。

## 決策

使用 pycasbin 的 **RBAC with domains** 模型，domain 即為家庭：

```ini
[request_definition]
r = sub, dom, obj, act
[policy_definition]
p = sub, dom, obj, act
[role_definition]
g = _, _, _
[policy_effect]
e = some(where (p.eft == allow))
[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && keyMatch(r.obj, p.obj) && r.act == p.act
```

- 策略透過 SQLAlchemy adapter 存放在 PostgreSQL。
- 每個模組宣告自己的權限與預設授權，平台在啟動時註冊。
- 端點宣告 `require_permission(...)`，預設拒絕。
- 策略變更時，透過 Redis watcher 通知每個 worker 重新載入。
- 資源擁有權（例如個人帳本）**不**放進 Casbin，由 service 層檢查。

## 影響

- 業界標準、易於理解的模型；與作者的工作經驗一致。
- 多 worker 部署必須搭配 watcher，否則權限會不同步。

## 考慮過的替代方案

- **自己寫角色與權限資料表：** 簡單，但是在重造已經解決過的問題。
- **外部策略引擎（OPA、Oso Cloud）：** 以這個規模來說太重。
