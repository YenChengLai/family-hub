<!-- translation-of: docs/adr/0012-code-defined-policies-roles-from-memberships.md | synced: 2026-10-08 -->

# ADR-0012：權限策略寫在程式碼中；角色在每個請求時從成員關係讀取

- 狀態：已採納
- 日期：2026-10-08
- 取代：[ADR-0006](0006-casbin-rbac-with-domains.zh-TW.md) 中策略儲存與 Redis watcher 的部分

## 背景

ADR-0006 原本計畫透過 SQLAlchemy adapter 把 Casbin 策略存在 PostgreSQL，並以 Redis watcher 讓各 worker 保持同步。
實作時發現兩個問題：

- **兩個資料來源。** 角色指派已經存在 `memberships` 資料表。若再複製到 Casbin 的 `g` 規則，每次成員關係變更都要同時更新兩邊，否則就會不一致。
- **跨程序的快取過時。** 管理 CLI 在另一個程序中新增成員。每個 API worker 各自持有記憶體中的 enforcer，因此 watcher 是為了正確性而必須存在，不只是為了效能。

另一方面，目前沒有任何需要在執行期編輯策略的需求：權限及其對內建角色的授予，本來就是各模組程式碼的一部分。

## 決策

- **權限策略（`p`）寫在程式碼中。** 每個模組在其 `Module` 描述物件中宣告權限與授予。平台在啟動時據此建立記憶體中的 Casbin enforcer。策略的變更會在 pull request 中審閱。
- **角色階層（`g`）寫在程式碼中：** `owner` ⊇ `adult` ⊇ `child`。
- **使用者在家庭中的角色，在每個請求時從 `memberships` 讀取**（一次有索引的查詢）。家庭邊界由這個查詢強制：非成員得到 404。
- Casbin 負責判斷「角色 → 權限」，包含繼承。

## 影響

- 成員關係只有一個資料來源；角色變更會在每個程序的下一個請求立即生效，不需要 watcher，也不需要讓快取失效。
- 沒有 `casbin_rule` 資料表，也不需要 adapter 相依套件。
- 每個限定家庭的請求多一次查詢。以我們的規模可忽略，之後需要時也能加上快取。
- 無法為個別家庭自訂角色或權限。若將來需要，會以新的 ADR 引入儲存式策略。

## 考慮過的替代方案

- **照 ADR-0006 原案（adapter + watcher）：** 基於「背景」所述的理由不採用。
- **不用 Casbin，只用一個字典：** 現在可行，但 Casbin 讓模型維持熟悉的形式、處理繼承，並為 ABAC matcher 保留空間。
