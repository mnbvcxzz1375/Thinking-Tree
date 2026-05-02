# 🌳 儿童思维树系统

> 🇬🇧 [English Version](README.md)

一个基于 Web 的交互式思维树系统，旨在通过可视化的树结构和 AI 辅助引导，帮助儿童培养批判性思维和问题解决能力。

## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [语音识别功能](#语音识别功能)
- [开发设置](#开发设置)
- [测试](#测试)
- [部署](#部署)
- [贡献指南](#贡献指南)

## ✨ 功能特性

- 🎯 **交互式树可视化** - 基于 D3.js 的精美树形图，带动画分支和叶子
- 🎙️ **AI 语音识别** - 录制孩子的想法，自动归类到思维树中
- 🤖 **多 AI 支持** - 集成通义千问（DashScope）和小米 MiMo
- 🧠 **智能节点放置** - AI 分析语音内容，推荐最佳放置位置
- 🔄 **相似节点检测** - AI 检测语义相似的节点，提示是否合并
- 📍 **层级挂载** - 新想法可以挂载到树的任意层级（不仅仅是根分支）
- ⚖️ **辩论模式** - 支持正方/反方两侧思维树，录音内容会结合当前树结构自动归类到对应阵营
- 📚 **活动管理** - 可创建、编辑、删除活动，并保存活动描述、活动指导、难度、年龄段和活动模式
- 🎨 **儿童友好界面** - 温暖的自然主题设计，流畅动画
- 📱 **响应式设计** - 支持桌面、平板和手机
- 💾 **本地持久化** - 树状态自动保存到 localStorage

## 🧭 活动与辩论模式

- **普通思维树**：适合围绕一个主题自由发散，例如“一棵树”“我的校园”“如果我是一只小鸟”。
- **辩论模式**：适合有正反观点的主题，例如“放走蚂蚁 / 踩扁蚂蚁”。系统会用左右两侧树干区分正方和反方，方向叶子可在两侧共用。
- **活动描述**：建议写清楚本次活动想讨论什么、孩子需要围绕哪些角度表达。
- **活动指导**：建议写给老师看的引导方式，例如是否先自由表达、是否追问“为什么”、相似想法是否合并。
- **删除活动**：活动管理页和活动详情页均提供删除入口，删除会移除该活动及其关联数据。

## 🛠 技术栈

### 前端
- **框架**: Nuxt 4 (Vue 3 + TypeScript)
- **可视化**: D3.js + GSAP 动画
- **样式**: 作用域 CSS，自然主题
- **状态管理**: Pinia + localStorage 持久化

### 后端
- **框架**: FastAPI (Python 3.11+)
- **AI 集成**: 
  - 通义千问 Omni Realtime API（WebSocket）
  - 小米 MiMo API（REST）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **WebSocket**: 实时音频流代理

### DevOps
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **部署**: Vercel（前端）/ Docker（后端）

## 📦 环境要求

- **Node.js** 20+（带 pnpm）
- **Python** 3.11+
- **API Key** - 从[阿里云百炼](https://bailian.console.aliyun.com/)获取

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/mnbvcxzz1375/Thinking-Tree.git
cd Thinking-Tree
```

### 2. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# 必需: DASHSCOPE_API_KEY
```

### 3. 启动开发环境

**后端:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765
```

**前端:**
```bash
cd frontend
pnpm install
pnpm dev
```

### 4. 访问应用

- **前端**: http://localhost:3000
- **后端 API**: http://localhost:8765
- **健康检查**: http://localhost:8765/health

## 🎙️ 语音识别功能

### 工作流程

1. **录音** - 点击麦克风按钮录制孩子的想法
2. **分析** - AI 转录音频并分析内容
3. **归类** - AI 推荐在树中的最佳位置
4. **审核** - 如果存在相似节点，老师可选择合并或新建
5. **确认** - 节点被添加到推荐位置

### AI 功能

| 功能 | 说明 |
|------|------|
| **语音转文字** | 使用通义千问 Omni 将音频转为文本 |
| **智能放置** | 分析内容，找到最匹配的父节点 |
| **相似检测** | 识别语义相似的现有节点 |
| **层级挂载** | 可挂载到任意深度，不仅仅是根分支 |
| **追问生成** | 为老师生成自然的追问问题 |

### 支持的音频格式

- **格式**: PCM 16-bit
- **采样率**: 16kHz
- **声道**: 单声道
- **块大小**: 3200 字节（100ms）

### 示例流程

```
树结构:
├── 🌳 树木（根节点）
│   ├── 🍃 外形
│   │   ├── 很小
│   │   └── 很绿
│   ├── 🌱 生长
│   │   └── 很快
│   └── 🔧 用途
│       └── 做家具

录音: "叶子很小"

AI 分析:
- 转写: "叶子很小"
- 叶子文本: "叶子很小"
- 推荐父节点: "很小"（在外形下面）
- 相似节点: ["很小"]
- 追问: "树还有什么地方很小？"
```

## 🔧 开发设置

### 环境变量

```bash
# .env 文件
DASHSCOPE_API_KEY=sk-your-api-key
QWEN_MODEL=qwen3.5-omni-flash-realtime
QWEN_REGION=cn

# 可选: MiMo API
MIMO_API_KEY=tp-your-mimo-key

# 服务器配置
HOST=127.0.0.1
PORT=8765
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/status` | GET | API 状态和配置 |
| `/api/speech/analyze` | POST | 分析语音音频 |
| `/api/activities` | CRUD | 活动管理 |
| `/api/trees` | CRUD | 树管理 |

### 项目结构

```
Thinking-Tree/
├── frontend/                    # Nuxt 4 前端
│   ├── app/
│   │   ├── components/          # Vue 组件
│   │   │   ├── ThinkingTree.vue # 主树可视化组件
│   │   │   ├── AudioRecorder.vue# 录音组件
│   │   │   └── ...
│   │   ├── composables/         # Vue composables
│   │   ├── stores/              # Pinia 状态管理
│   │   └── pages/               # Nuxt 页面
│   └── nuxt.config.ts
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── routers/
│   │   │   └── audio_proxy.py   # 语音分析端点
│   │   ├── services/
│   │   │   └── adapters/        # AI 适配器（千问、MiMo）
│   │   ├── models/              # SQLAlchemy 模型
│   │   └── config.py            # 配置文件
│   └── requirements.txt
├── src/                         # 遗留/独立组件
│   └── api/
│       └── proxy_server.py      # WebSocket 代理
├── docs/                        # 文档
├── scripts/                     # 工具脚本
└── docker-compose.yml
```

## 🧪 测试

### 运行测试

```bash
# 前端
cd frontend
pnpm test:unit

# 后端
cd backend
pytest

# 验证 API 连通性
python src/api/verify_qwen_api.py
```

### 测试音频文件

测试音频文件位于 `src/test/`:
- `测试录音.mp3` - 示例录音

## 🚢 部署

### Docker（推荐）

```bash
docker-compose up --build
```

### 手动部署

**前端:**
```bash
cd frontend
pnpm build
# 将 .output/ 部署到 Vercel 或类似平台
```

**后端:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 提交规范

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 维护

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [阿里云](https://www.alibabacloud.com/) 提供通义千问 API
- [Nuxt](https://nuxt.com/) 前端框架
- [FastAPI](https://fastapi.tiangolo.com/) 后端框架
- [D3.js](https://d3js.org/) 树形可视化
