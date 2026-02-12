<div align="center">

<img src="icon.ico" alt="Logo" width="120" height="120">

# 北京科技大学智能汽车竞赛计时器系统

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) [![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE) [![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

这是一个专为**北京科技大学智能汽车竞赛**开发的计时与赛事管理系统。
支持多组别比赛管理、精确计时、成绩修正、多端投屏展示以及硬件设备通信。

[项目主页](https://github.com/Xiangyuan-Xie/USTBSmartCarRaceTimer_Upper.git)

[功能特性](#功能特性) • [安装使用](#安装使用) • [配置说明](#配置说明) • [项目结构](#项目结构) • [贡献指南](#贡献指南)

</div>

## 功能特性

- **多端投屏同步**：
  - **本地双屏**：控制台与观众展示屏分离，支持扩展屏幕显示。
  - **Web 实时投屏**：内置 WebSocket 服务器，观众可通过浏览器连接局域网查看实时赛况（支持移动端适配）。
- **赛事管理**：
  - 支持多组别（摄像头组、电磁组等）切换与配置。
  - 自动化成绩记录，支持 Excel/CSV 格式导入导出。
  - 灵活的罚时系统与成绩修正功能。
- **硬件集成**：
  - **串口通信**：对接计时触发器。
  - **网络通信**：支持 TCP/UDP 协议对接外部设备。
  - **语音播报**：基于 Pygame 的关键节点语音提示（开始、结束等）。
- **界面交互**：
  - 基于 PySide6 的现代化 UI 设计。
  - 队伍成员名单超长自动滚动（跑马灯效果）。

## 安装使用

### 环境要求

- Windows 10/11 (推荐) / macOS / Linux
- Python 3.8 或更高版本

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/Xiangyuan-Xie/USTBSmartCarRaceTimer_Upper.git
   cd USTBSmartCarRaceTimer_Upper
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

## 配置说明

项目根目录下的 `config.json` 用于管理比赛参数。程序启动时会自动读取，若文件不存在则生成默认配置。

```json
{
  "比赛名称": "北京科技大学智能汽车竞赛",
  "比赛组别": "摄像头组",
  "赛前准备时间": 90,
  "比赛时间": 600,
  "WebSocketURI": "ws://0.0.0.0:4001"
}
```

> **提示**: 部分高级设置（如端口号、罚时规则）建议直接在程序界面的“设置”菜单中修改。

## 项目结构

```text
.
├── core/                   # 核心业务逻辑 (数据管理, 配置, Web服务)
├── widget/                 # UI 界面组件 (基于 PySide6)
│   ├── console.py          # 主控制台窗口
│   ├── screen.py           # 投屏显示窗口
│   └── dialog/             # 设置弹窗
├── web/                    # Web 投屏前端资源 (HTML/JS/CSS)
├── communication_threads/  # 硬件通信线程 (Serial/TCP/UDP)
└── tests/                  # 单元测试
```

## 开发与测试

本项目使用 `pytest` 进行单元测试。运行测试确保核心逻辑正确：

```bash
pytest tests/
```

## 贡献指南

欢迎提交 Issue 或 Pull Request 来改进本项目。

### 1. 安装开发工具

请确保安装了 pre-commit 钩子，以便在提交时自动检查代码风格和运行测试。

```bash
pip install pre-commit
pre-commit install
```

### 2. 代码规范

- 代码风格遵循 `black` 和 `isort`。
- 新增功能请确保有对应的测试覆盖。
- 提交信息请遵循 Conventional Commits 规范。

## 许可证

本项目采用 [GNU GPL v3](LICENSE) 许可证。


<p align="center">
  Made with ❤️ by USTB Smart Car Competition Team
</p>
