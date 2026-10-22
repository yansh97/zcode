# DeepSeek Search

DeepSeek 网页搜索与抓取，提供 `web_search` / `web_fetch` 两个 MCP 工具。

工具名、描述和参数 schema 定义在 `mcp/tools.json`，服务启动时读取；`mcp/server.py` 只负责协议与调用逻辑。

## 要求

macOS 12+，以及 `/usr/bin/python3`（由 Xcode Command Line Tools 提供，未装则运行 `xcode-select --install`）。除此之外只需系统 Python 标准库，不需要 pip 安装任何依赖。

## 安装

1. 在 <https://platform.deepseek.com> 创建 API Key。
2. **设置 → 插件市场 → + → 添加插件市场**：`https://github.com/yansh97/zcode`
3. **Personal → yansh97-zcode → DeepSeek Search → 安装**
4. **设置 → 插件管理 → DeepSeek Search → 高级设置**，填入 API Key。

## 自测

```bash
cd <仓库根>/plugins/deepseek-search
export DEEPSEEK_API_KEY=sk-...

# 列出工具
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  | /usr/bin/python3 mcp/server.py

# 实际搜索
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"web_search","arguments":{"query":"关键词","count":3}}}' \
  | /usr/bin/python3 mcp/server.py
```
