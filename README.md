<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-headscale/main/brand/logo.png" alt="Headscale Logo" width="220">
</p>

# Headscale & Tailscale Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![CI](https://github.com/FaserF/ha-headscale/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-headscale/actions)
[![Latest Release](https://img.shields.io/github/v/release/FaserF/ha-headscale?include_prereleases&color=blue)](https://github.com/FaserF/ha-headscale/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Comprehensive Home Assistant custom integration for self-hosted **Headscale** nodes and official **Tailscale SaaS** networks.

This integration delivers **100% feature-parity** with the official Home Assistant Core Tailscale integration, while introducing full **self-hosted Headscale support** via its native v1 REST API. Control nodes, advertise routes, monitor users, inspect mesh connectivity, and manage pre-authenticated keys directly from Home Assistant.

---

## 🌟 Key Features & Supported Platforms

### 1. 🔄 Dual Provider Architecture (Headscale & Tailscale)
- **Self-Hosted Headscale Mode**: Connects directly to Headscale v0.23+ / v0.24+ / v0.29+ control planes using your server URL and API bearer token.
- **Official Tailscale SaaS Mode**: 1:1 drop-in replacement with official Tailscale OAuth client credentials (`oauth_client_id`, `oauth_client_secret`, and `tailnet`).

### 2. 📡 Full Core Feature Parity (100% Compatibility)
- **Node Connectivity Binary Sensor** (`binary_sensor.*_connected_to_control`): Live connectivity status with the control server.
- **Client Update Available** (`binary_sensor.*_update_available`): Diagnostic sensor indicating pending client package updates.
- **Key Expiration State** (`binary_sensor.*_key_expiry_disabled`): Shows whether key expiration has been disabled.
- **Network Capabilities Sensors**:
  - `binary_sensor.*_ipv6_support`
  - `binary_sensor.*_pcp_support`
  - `binary_sensor.*_nat_pmp_support`
  - `binary_sensor.*_udp_support`
  - `binary_sensor.*_upnp_support`
- **Tailscale IP Sensor** (`sensor.*_tailscale_ip`): Primary Tailnet IPv4/IPv6 address with attributes containing machine keys, node keys, assigned users, routes, and tags.
- **Timestamp Sensors**:
  - `sensor.*_key_expiration`: Absolute timestamp of node expiration.
  - `sensor.*_last_seen`: Live timestamp when the node last communicated with the control plane.

### 3. 🛡️ Headscale Control Plane & Subnet Management
- **Subnet Route Approval Switches** (`switch.*_route_*`):
  - Automatically discovers advertised subnet routes and exit nodes (e.g. `0.0.0.0/0`, `192.168.1.0/24`, `::/0`).
  - Toggle route approvals on and off directly from Lovelace dashboards or automations.
- **Server Health Binary Sensor** (`binary_sensor.headscale_control_plane_online`):
  - Monitors uptime, REST API responsiveness, and control plane reachability.
- **Mesh Network Telemetry**:
  - `sensor.headscale_total_nodes`: Number of registered nodes in the mesh.
  - `sensor.headscale_online_nodes`: Count of currently online machines.
  - `sensor.headscale_total_users`: Active user namespaces on the server.

### 4. ⚡ Node Lifecycle Buttons & Automations
- **`button.*_expire_node_key`**: Instantly force key logout/expiration for a node from the UI.
- **`button.headscale_refresh_data`**: Manually trigger data synchronization and coordinator polling.

---

## 🛠️ Provided Action Services

The integration provides powerful Home Assistant services to automate your Tailnet:

| Service | Description | Parameters |
| :--- | :--- | :--- |
| `headscale.expire_node` | Force node registration expiration | `node_id` |
| `headscale.rename_node` | Rename a node in the DNS and mesh | `node_id`, `new_name` |
| `headscale.delete_node` | Permanently delete a node from the cluster | `node_id` |
| `headscale.set_node_tags` | Assign or replace ACL tags on a node | `node_id`, `tags` (list) |
| `headscale.set_approved_routes` | Approve or revoke advertised subnet and exit routes | `node_id`, `routes` (list) |
| `headscale.create_preauthkey` | Generate a reusable or ephemeral machine auth key | `user`, `reusable`, `ephemeral`, `expiration`, `tags` |
| `headscale.expire_preauthkey` | Invalidate an active pre-auth key | `user`, `key` |
| `headscale.create_user` | Create a new user namespace on the server | `user` |
| `headscale.rename_user` | Rename an existing user namespace | `old_user`, `new_user` |

### Example Automations

#### 1. Generate Pre-Auth Key for New Docker Deployment
```yaml
alias: "Generate Headscale Key for New Container"
sequence:
  - action: headscale.create_preauthkey
    data:
      user: "fabian"
      reusable: false
      ephemeral: true
      expiration: "2027-01-01T00:00:00Z"
      tags:
        - "tag:server"
    response_variable: auth_result
  - action: notify.persistent_notification
    data:
      title: "New Pre-Auth Key Generated"
      message: "Key: {{ auth_result.key }}"
```

#### 2. Automatic Notification on Offline Node
```yaml
alias: "Alert When Server Node Goes Offline"
trigger:
  - platform: state
    entity_id: binary_sensor.oracle_vm_connected_to_control
    to: "off"
    for:
      minutes: 5
action:
  - action: notify.notify
    data:
      title: "Headscale Node Disconnected"
      message: "Node {{ trigger.entity_id }} is currently offline!"
```

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Enter `https://github.com/FaserF/ha-headscale` and select **Integration** as category.
4. Click **Add**, find **Headscale**, and click **Download**.
5. Restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest `headscale.zip` release from [GitHub Releases](https://github.com/FaserF/ha-headscale/releases).
2. Unpack the zip and copy `custom_components/headscale` into your `<config_dir>/custom_components/` directory.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **Headscale**.
3. Choose your provider mode:
   - **Headscale (Self-Hosted)**: Enter your Headscale server URL (e.g. `https://vpn.example.com:8443` or `http://127.0.0.1:8443`), provide your API Bearer Key, and select your SSL verification preference.
   - **Tailscale (Official SaaS)**: Enter your Tailnet name, OAuth Client ID, and OAuth Client Secret.

---

## 📊 Diagnostics

The integration fully supports Home Assistant Diagnostics. Download redacted diagnostic logs from the device or integration page to inspect network payloads, route definitions, and API status without exposing sensitive credentials or private machine keys.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
