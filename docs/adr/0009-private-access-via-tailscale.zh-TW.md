<!-- translation-of: docs/adr/0009-private-access-via-tailscale.md | synced: 2026-10-08 -->

# ADR-0009：正式環境僅能透過 Tailscale 存取

- 狀態：已採納
- 日期：2026-10-08

## 背景

家人需要在外面使用（例如在店裡記一筆支出）。NAS 上還存放其他私密的家庭資料。
在路由器開 port 會讓 NAS 暴露在網際網路上。部分 ISP 讓用戶位於 CGNAT 之後，外部連線本來就連不進來。

## 決策

- 正式環境**只能**透過 Tailscale（Synology 官方套件）存取，路由器不轉發任何 port。
- HTTPS 使用 Tailscale 為 `*.ts.net` 主機名稱簽發的憑證。
- 以 Tailscale ACL 限制成員裝置只能連到本系統的 port。

## 影響

- 正式環境沒有公開的攻擊面；在 CGNAT 之後也能使用。
- 每台家庭裝置都要安裝 Tailscale App。免費方案足以涵蓋我們的使用者數量。
- 依賴 Tailscale 的協調服務。退路：自架 Headscale。

## 考慮過的替代方案

- **Synology VPN Server（OpenVPN 或 L2TP）：** 需要開 port、公網 IP 與 DDNS；協定較舊。
- **Cloudflare Tunnel：** 不用開 port，但正式環境會變成公開可連。
