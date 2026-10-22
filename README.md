# yansh97/zcode

为 ZCode 编写的个人插件集合，以 marketplace 形式分发。

## 添加市场

ZCode 中打开 **设置 → 插件市场 → `+` → 添加插件市场**，填入：

```
https://github.com/yansh97/zcode
```

然后在 **Personal → yansh97-zcode** 下安装需要的插件。

## 插件列表

| 插件 | 版本 | 说明 |
|---|---|---|
| [deepseek-search](plugins/deepseek-search/README.md) | 0.2.0 | DeepSeek 网页搜索与抓取（MCP 工具） |

## 仓库结构

```
.
├── marketplace.json                 # 市场清单，所有插件在此登记
├── pyproject.toml                   # ruff / ty 的 Python 版本限定
├── LICENSE                          # MIT
└── plugins/
    └── deepseek-search/
        ├── .zcode-plugin/plugin.json   # 插件清单
        ├── mcp/server.py               # stdio MCP 服务端（常驻进程）
        ├── mcp/tools.json              # 工具名、描述与参数 schema
        └── README.md
```

`mcp/` 下是运行时进程。工具描述和参数 schema 放在 `mcp/tools.json`，启动时读一次；改描述只动 JSON，不用碰代码。JSON 里的 `name` 必须与 `server.py` 中同名函数对应，分派靠 `globals()` 查找。

## 新增插件的步骤

1. 新建 `plugins/<plugin-name>/`，目录名必须与 `plugin.json` 的 `name` 完全一致。
2. 写 `.zcode-plugin/plugin.json`，只声明真实存在的组件字段（`skills` / `commands` / `hooks` / `mcpServers` / `agents`）。
3. 在根目录 `marketplace.json` 的 `plugins` 数组里加一条，`source` 用相对路径 `./plugins/<plugin-name>`。
4. 提交后用户侧刷新市场即可看到新版本。

## 约定

- **优先把用法写进工具描述。** 工具描述随 MCP 连接常驻，模型调用前就能看到；只有需要压缩常驻开销的大段内容才值得拆成按需加载的 skill。
- **密钥走 `userConfig` + `sensitive: true`，注入 `env` 或 `headers`。** 严禁写进仓库、`args` 或 `url`。
- **版本号在 `plugin.json` 与 `marketplace.json` 两处保持一致**，更新行为才一致。
- 运行时使用 macOS 自带的 `/usr/bin/python3`（Xcode Command Line Tools 提供）及其标准库。

## 开发与自测

每个插件的 README 里有独立的本地自测命令，可以不经过 ZCode 直接验证。改动后递增版本号，并在脚手架生成的文件上直接编辑。

`pyproject.toml` 只用于静态检查：`requires-python` 与 `[tool.ruff] target-version` 都锁定 3.9，因为插件跑在系统自带的 Python 上。

```bash
ruff check plugins && ruff format --check plugins && ty check plugins
```
