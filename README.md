# USB Redirector Remote Control Bot

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

通过 HTTP API 远程控制 [USB Redirector](https://www.incentives-pro.com/usb-redirector.html) 的 USB 设备共享与连接，基于命令行工具 `usbrdrsh.exe`，无需桌面会话，适合无人值守的服务器/虚拟机环境。

> **English**: A lightweight HTTP API that wraps USB Redirector's CLI tool (`usbrdrsh.exe`) to manage USB device sharing remotely — no RDP or desktop session needed.

---

## 特性

- **命令行驱动** — 直接调用 `usbrdrsh.exe`，不依赖 GUI
- **无人值守** — 无需 RDP/VNC 连接，服务运行即可操作
- **模糊匹配** — 设备名称关键词匹配，无需输入完整名称
- **状态感知** — 操作前自动检测设备状态，避免无效操作
- **环境变量配置** — 支持通过环境变量自定义路径和端口

---

## 快速开始

### 前置条件

- Windows + [USB Redirector](https://www.incentives-pro.com/usb-redirector.html) 已安装
- Python 3.8+

### 安装

```bash
pip install -r requirements.txt
```

<details>
<summary>离线安装</summary>

```bash
# 外网机器下载
pip download -r requirements.txt -d offline_packages

# 内网机器安装
pip install --no-index --find-links=offline_packages -r requirements.txt
```
</details>

### 启动

```bash
python usb_bot.py
```

服务默认监听 `http://0.0.0.0:5000`。

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `USBRDRSH_PATH` | `C:\Program Files\USB Redirector\usbrdrsh.exe` | usbrdrsh.exe 路径 |
| `USBRDRSH_TIMEOUT` | `10` | 命令执行超时（秒） |
| `PORT` | `5000` | HTTP 监听端口 |

---

## API

所有设备操作通过 `POST /command`，JSON body 格式：

```json
{"command": "<command>", "device": "<keyword>"}
```

### 命令列表

| 命令 | 说明 | 需要 device |
|------|------|:-----------:|
| `list` | 列出所有 USB 设备及状态 | 否 |
| `share` | 共享设备，使远程客户端可连接 | 是 |
| `unshare` | 取消共享 | 是 |
| `connect` | 连接设备（未共享则自动共享） | 是 |
| `disconnect` | 断开设备与客户端的连接 | 是 |

### 示例

```bash
# 健康检查
curl http://localhost:5000/health

# 列出设备
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{"command": "list"}'

# 共享设备（模糊匹配名称）
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{"command": "share", "device": "Vector"}'

# 断开设备
curl -X POST http://localhost:5000/command \
  -H "Content-Type: application/json" \
  -d '{"command": "disconnect", "device": "Vector"}'
```

<details>
<summary>PowerShell 示例</summary>

```powershell
# 列出设备
Invoke-RestMethod -Uri http://localhost:5000/command -Method POST `
  -ContentType "application/json" `
  -Body '{"command":"list"}'

# 共享设备
Invoke-RestMethod -Uri http://localhost:5000/command -Method POST `
  -ContentType "application/json" `
  -Body '{"command":"share","device":"Vector"}'
```
</details>

### 响应格式

```json
{
  "status": "success | error | info",
  "message": "操作结果描述"
}
```

`list` 命令额外返回 `devices`（格式化列表）和 `raw`（结构化数据）。

---

## 远程访问

1. 获取服务器 IP（如 `192.168.0.188`）
2. 防火墙放行 TCP 5000 端口
3. 将请求中的 `localhost` 替换为服务器 IP

---

## 项目结构

```
├── usb_bot.py          # 主服务
├── requirements.txt    # Python 依赖
├── examples/           # 早期 GUI 自动化探索脚本（参考用）
│   ├── list_devices.py
│   ├── test_connect.py
│   └── test_right_click_menu.py
├── LICENSE
└── README.md
```

---

## License

[MIT](LICENSE)
