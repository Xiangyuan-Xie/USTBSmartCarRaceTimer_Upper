# 🏁 北京科技大学智能汽车竞赛计时器系统

<p align="center">
  <img src="icon.ico" alt="Logo" width="100" height="100">
</p>

<p align="center">
  <b>专业 • 精准 • 高效</b>
</p>

---

## 📖 项目简介

本项目专为北京科技大学智能汽车竞赛设计，提供了一套完整的比赛计时与管理解决方案。系统基于 **Python** 与 **PySide6** 开发，集成了串口通信、网络通信（TCP/UDP）、实时计时、成绩管理、多屏投屏及网页即时显示功能，确保比赛流程的顺畅与公正。

## ✨ 核心功能

- **⏱️ 精准计时**：支持毫秒级计时，实时显示比赛时间与剩余时间。
- **📊 成绩管理**：自动记录并修正成绩，支持罚时操作与 Excel/CSV 数据导入导出。
- **📡 多模通信**：内置串口、TCP Server、UDP Server 通信模块，适配多种硬件设备。
- **🖥️ 多屏互动**：
  - **本地投屏**：支持双屏显示，实时向观众展示比赛进度与成绩。
  - **网页投屏**：内置 Web 服务器，支持通过浏览器实时查看比赛状态。
- **🎵 语音播报**：集成 Pygame 音频引擎，自动播报比赛关键节点（如时间到、重置）。
- **🛠️ 灵活配置**：支持自定义比赛参数、罚时规则及通信端口。

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Windows / macOS / Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行项目

```bash
python main.py
```

## 📂 项目结构

```
g:\校内赛计时器
├── audio/                  # 音频资源文件
├── communication_threads/  # 通信线程 (串口, TCP, UDP)
├── core/                   # 核心逻辑模块 (Config, Data, Audio, Web Server)
├── web/                    # 网页投屏资源 (HTML, CSS, JS)
├── widget/                 # UI 组件与界面逻辑
│   ├── dialog/             # 各类设置对话框 (标准化 BaseDialog)
│   ├── console.py          # 主控制台逻辑
│   ├── screen.py           # 投屏窗口逻辑
│   └── ...
├── config.json             # 配置文件
├── main.py                 # 程序入口
└── requirements.txt        # 项目依赖
```

## 🛠️ 技术栈

- **GUI Framework**: PySide6 (Qt for Python)
- **Web Server**: Python standard library / Custom implementation
- **Audio Engine**: Pygame
- **Data Processing**: Pandas, OpenPyXL
- **Communication**: PySerial, Socket

## 📝 开发规范

本项目遵循模块化设计原则，将业务逻辑与界面显示分离：
- `core/`: 负责核心数据、配置、音频及 Web 服务管理。
- `widget/`: 负责界面交互与展示，采用统一的 Dialog 基类。
- `communication_threads/`: 处理硬件通信与数据解析。

---

<p align="center">
  Made with ❤️ by USTB Smart Car Competition Team
</p>
