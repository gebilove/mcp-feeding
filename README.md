# MCP Feeding Tracker | MCP 喂养记录助手

> **Note**: This project is based on/forked from the [mcp-calculator](https://github.com/wong2/mcp-calculator) project.  
> **注意**: 本项目基于 [mcp-calculator](https://github.com/wong2/mcp-calculator) 修改而来。

A specialized MCP (Model Context Protocol) server for tracking baby feeding logs. It allows AI agents to record feeding events, track volumes, and analyze daily statistics using a local SQLite database.

一个专门用于追踪宝宝喂养记录的 MCP 服务器。它允许 AI 智能体记录喂养事件、追踪奶量，并使用本地 SQLite 数据库分析每日统计数据。

## Features | 特性

- 🍼 **Smart Recording**: Log feeding amount, type (formula/breast milk), and notes | 智能记录：记录喂奶量、类型（配方奶/母乳）及备注
- ⏰ **Natural Language Backfill**: Support recording past events (e.g., "fed 150ml last night at 10pm") | 自然语言补录：支持记录过去的时间点
- 📊 **Daily Analysis**: Get instant summary of today's total volume, count, and last feeding time (Beijing Time) | 每日分析：即时获取今日（北京时间）的总量、次数和上次喂奶时间
- � **Local Storage**: Data persists in `feeding_data.db` (SQLite), safe and private | 本地存储：数据保存在本地 SQLite 数据库中，安全隐私
- � **Standard MCP**: Compatible with any MCP client (Claude Desktop, Cursor, etc.) | 标准 MCP：兼容任何 MCP 客户端

## Quick Start | 快速开始

1. **Install dependencies | 安装依赖**:
```bash
pip install -r requirements.txt
```

2. **Run the server | 运行服务**:
```bash
python mcp_pipe.py
```

3. **Connect your AI | 连接 AI**:
   - Use the provided WebSocket endpoint or configure your MCP client to run the script directly.
   - 使用提供的 WebSocket 端点，或配置你的 MCP 客户端直接运行此脚本。

## Usage Examples | 使用示例

Once connected, you can ask your AI agent:

- "Record 150ml formula milk" (记录150ml配方奶)
- "I fed the baby 120ml at 10 PM last night" (昨晚10点喂了120ml)
- "How much has the baby eaten today?" (宝宝今天喝了多少？)
- "Show me the recent feeding logs" (给我看看最近的喂奶记录)

## Project Structure | 项目结构

- `mcp_pipe.py`: MCP Gateway/Host implementation | MCP 网关/宿主实现
- `feeding_server.py`: Core logic for feeding tracking and database management | 喂养追踪和数据库管理的核心逻辑
- `feeding_data.db`: SQLite database (auto-created) | SQLite 数据库（自动创建）
- `test_feeding_logic_mock.py`: Testing script | 测试脚本

## License | 许可证

This project is licensed under the MIT License.

本项目采用 MIT 许可证。
