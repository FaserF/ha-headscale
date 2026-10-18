# ha-headscale

<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-headscale/main/brand/logo.png" alt="Headscale Logo" width="180">
</p>

<p align="center">
  <strong>Home Assistant integration for self-hosted Headscale and official Tailscale mesh VPN control planes.</strong>
</p>

<p align="center">
  <a href="https://github.com/FaserF/ha-headscale/releases"><img src="https://img.shields.io/github/v/release/FaserF/ha-headscale?include_prereleases" alt="Latest Release"></a>
  <a href="https://github.com/hacs/default"><img src="https://img.shields.io/badge/HACS-Custom-orange.svg" alt="HACS Custom"></a>
  <a href="https://github.com/FaserF/ha-headscale/actions/workflows/ci-orchestrator.yml"><img src="https://github.com/FaserF/ha-headscale/actions/workflows/ci-orchestrator.yml/badge.svg" alt="CI Status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/FaserF/ha-headscale" alt="License"></a>
</p>

---

## 🌟 Features

- **Dual Provider Support**: Seamlessly connect to self-hosted **Headscale** (REST API v1) or official **Tailscale SaaS** (OAuth).
- **100% Tailscale Core Feature Parity**: Full support for all official Home Assistant Tailscale entities (connectivity, node IP, last seen, key expiration, client update state).
- **Server Metrics & Status**: Track total nodes, online nodes, registered users, and control plane availability.
- **Route Approval Switches**: Directly approve or revoke advertised subnet and exit routes per node from Home Assistant.
- **Pre-Auth Key Automation**: Generate reusable or ephemeral pre-authentication keys via HA services.
- **Node Lifecycle Management**: Services and buttons to expire keys, rename nodes, tag nodes, or delete retired machines.
- **User Namespace Control**: Create and rename user namespaces directly from Home Assistant.

---

## 🚀 Installation

### Via HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click on the 3 dots in the top right corner and choose **Custom repositories**.
3. Add `https://github.com/FaserF/ha-headscale` with category **Integration**.
4. Search for **Headscale** and click **Download**.
5. Restart Home Assistant.

### Manual Installation

1. Download the `headscale.zip` release from the [Releases page](https://github.com/FaserF/ha-headscale/releases).
2. Extract the `headscale` folder into your Home Assistant `<config>/custom_components/` directory.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **Headscale**.
3. Choose your provider:
   - **Headscale (Self-Hosted)**: Enter your server URL (e.g. `https://vpn.example.com:8443`) and your Headscale API Key.
   - **Tailscale (Official SaaS)**: Enter your Tailnet name, OAuth Client ID, and OAuth Client Secret.

---

## 🛠️ Provided Services

| Service | Description | Parameters |
| :--- | :--- | :--- |
| `headscale.expire_node` | Force node registration expiration | `node_id` |
| `headscale.rename_node` | Rename a node in the mesh | `node_id`, `new_name` |
| `headscale.delete_node` | Permanently delete a node | `node_id` |
| `headscale.set_node_tags` | Update node ACL tags | `node_id`, `tags` |
| `headscale.set_approved_routes` | Approve or revoke advertised subnet routes | `node_id`, `routes` |
| `headscale.create_preauthkey` | Generate a new machine auth key | `user`, `reusable`, `ephemeral`, `expiration`, `tags` |
| `headscale.expire_preauthkey` | Revoke an active auth key | `user`, `key` |
| `headscale.create_user` | Create a user namespace | `user` |
| `headscale.rename_user` | Rename a user namespace | `old_user`, `new_user` |

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
