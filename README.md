# LocalFlow

一个基于 Python 的可视化工作流管理工具，支持拖拽式节点编辑、UV 虚拟环境管理和多标签页工作流。

## 快速开始

### 构建打包

### 生成可执行文件
```bash
# 使用 Python 构建脚本
python build.py

# 或使用批处理脚本 (Windows)
build.bat

# 或使用 Shell 脚本 (Linux/Mac)
./build.sh
```

生成的可执行文件将在 `dist/` 目录中。

## 环境要求要求
- Python 3.8+
- PySide6
- UV (推荐用于包管理)

### 安装和运行

1. **克隆项目**
```bash
git clone <repository-url>
cd localflow
```

2. **安装依赖**
```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv (推荐)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. **运行应用**
```bash
python main.py
```

## 文档

- [用户指南](docs/user-guide/) - 使用说明和教程
- [开发文档](docs/development/) - 开发和构建指南
- [架构文档](docs/architecture/) - 系统架构和设计
- [测试文档](test/README.md) - 测试说明和运行指南

## 主要功能

- 🎨 **可视化工作流编辑器** - 拖拽式节点编辑
- 🔄 **多标签页管理** - 同时管理多个工作流
- 🐍 **UV 虚拟环境** - 智能的 Python 环境管理
- 🎯 **自定义配置** - 支持自定义 UV 路径和镜像源
- 🌙 **主题支持** - 明暗主题切换
- 💾 **数据持久化** - 自动保存和加载工作流

## 项目结构

```
LocalFlow/
├── src/                    # 源代码
│   ├── core/              # 核心逻辑
│   ├── dialogs/           # 对话框
│   ├── views/             # 视图组件
│   └── widgets/           # 自定义组件
├── test/                  # 测试文件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── ui/                # UI 测试
├── docs/                  # 文档
│   ├── user-guide/        # 用户指南
│   ├── development/       # 开发文档
│   └── architecture/      # 架构文档
├── assets/                # 资源文件
├── workflows/             # 工作流数据
└── main.py               # 主入口
```

## 测试

运行测试套件：

```bash
# 运行所有测试
python test/run_tests.py

# 运行特定类型测试
python test/run_tests.py unit        # 单元测试
python test/run_tests.py integration  # 集成测试
python test/run_tests.py ui          # UI 测试

# 或使用批处理脚本 (Windows)
run_tests.bat
```

## 配置

### UV 配置

LocalFlow 支持：
- 自动检测多个 UV 安装
- 自定义 UV 可执行文件路径
- 配置 PyPI 镜像源

配置方法：
1. 打开设置对话框
2. 在"UV 包管理工具"部分进行配置
3. 配置会自动保存到 `~/.uv/uv.toml`

### 工作流配置

工作流数据存储在 `workflows/` 目录下，每个工作流都有独立的虚拟环境。

## 贡献

欢迎贡献代码！请查看 [开发文档](docs/development/) 了解开发指南。

## 许可证

见 [LICENSE](LICENSE) 文件。

## 问题反馈

如有问题，请提交 Issue 或查看 [故障排除文档](docs/user-guide/)。