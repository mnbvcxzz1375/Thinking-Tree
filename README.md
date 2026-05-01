# 🌳 Children's Thinking Tree System

> 🇨🇳 [中文版本](README_CN.md)

A web-based interactive thinking tree system designed to help children develop critical thinking and problem-solving skills through visual tree structures and AI-powered guidance.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Speech Recognition](#speech-recognition)
- [Development Setup](#development-setup)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

## ✨ Features

- 🎯 **Interactive Tree Visualization** - Beautiful D3.js-powered tree with animated branches and leaves
- 🎙️ **AI Speech Recognition** - Record children's thoughts and automatically categorize them into the tree
- 🤖 **Multi-AI Support** - Qwen Omni (DashScope) and MiMo (Xiaomi) integration
- 🧠 **Smart Node Placement** - AI analyzes speech content and suggests optimal tree placement
- 🔄 **Similar Node Detection** - AI detects semantically similar nodes and prompts for merge
- 📍 **Hierarchical Mounting** - New ideas can be attached to any level of the tree (not just root branches)
- 🎨 **Child-Friendly UI** - Warm, nature-themed design with smooth animations
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile devices
- 💾 **Local Persistence** - Tree state saved to localStorage automatically

## 🛠 Tech Stack

### Frontend
- **Framework**: Nuxt 4 (Vue 3 + TypeScript)
- **Visualization**: D3.js + GSAP animations
- **Styling**: Scoped CSS with nature theme
- **State**: Pinia stores with localStorage persistence

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI Integration**: 
  - Qwen Omni Realtime API (WebSocket)
  - MiMo API (REST)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **WebSocket**: Real-time audio streaming proxy

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: Vercel (Frontend) / Docker (Backend)

## 📦 Prerequisites

- **Node.js** 20+ (with pnpm)
- **Python** 3.11+
- **API Key** from [Alibaba Cloud Bailian](https://bailian.console.aliyun.com/) (for Qwen)

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/mnbvcxzz1375/Thinking-Tree.git
cd Thinking-Tree
```

### 2. Set up environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: DASHSCOPE_API_KEY
```

### 3. Start development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8765
```

**Frontend:**
```bash
cd frontend
pnpm install
pnpm dev
```

### 4. Access the application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8765
- **Health Check**: http://localhost:8765/health

## 🎙️ Speech Recognition

### How It Works

1. **Record** - Click the microphone button to record a child's thought
2. **Analyze** - AI transcribes audio and analyzes content
3. **Categorize** - AI suggests the best position in the tree
4. **Review** - If similar nodes exist, teacher can choose to merge or add new
5. **Confirm** - Node is added to the tree at the suggested position

### AI Features

| Feature | Description |
|---------|-------------|
| **Speech-to-Text** | Converts audio to text using Qwen Omni |
| **Smart Placement** | Analyzes content and finds the best parent node |
| **Similar Detection** | Identifies semantically similar existing nodes |
| **Hierarchical Mounting** | Can attach to any depth, not just root branches |
| **Follow-up Questions** | Generates natural follow-up questions for teachers |

### Supported Audio Format

- **Format**: PCM 16-bit
- **Sample Rate**: 16kHz
- **Channels**: Mono
- **Chunk Size**: 3200 bytes (100ms)

### Example Flow

```
Tree Structure:
├── 🌳 Trees (root)
│   ├── 🍃 Appearance
│   │   ├── small
│   │   └── green
│   ├── 🌱 Growth
│   │   └── fast
│   └── 🔧 Uses
│       └── furniture

Recording: "The leaves are very small"

AI Analysis:
- Transcript: "The leaves are very small"
- Leaf Text: "leaves are small"
- Recommended Parent: "small" (under Appearance)
- Similar Nodes: ["small"]
- Follow-up: "What else is small about the tree?"
```

## 🔧 Development Setup

### Environment Variables

```bash
# .env file
DASHSCOPE_API_KEY=sk-your-api-key
QWEN_MODEL=qwen3.5-omni-flash-realtime
QWEN_REGION=cn

# Optional: MiMo API
MIMO_API_KEY=tp-your-mimo-key

# Server
HOST=127.0.0.1
PORT=8765
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/status` | GET | API status and config |
| `/api/speech/analyze` | POST | Analyze speech audio |
| `/api/activities` | CRUD | Activity management |
| `/api/trees` | CRUD | Tree management |

### Project Structure

```
Thinking-Tree/
├── frontend/                    # Nuxt 4 frontend
│   ├── app/
│   │   ├── components/          # Vue components
│   │   │   ├── ThinkingTree.vue # Main tree visualization
│   │   │   ├── AudioRecorder.vue# Recording component
│   │   │   └── ...
│   │   ├── composables/         # Vue composables
│   │   ├── stores/              # Pinia stores
│   │   └── pages/               # Nuxt pages
│   └── nuxt.config.ts
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── routers/
│   │   │   └── audio_proxy.py   # Speech analysis endpoint
│   │   ├── services/
│   │   │   └── adapters/        # AI adapters (Qwen, MiMo)
│   │   ├── models/              # SQLAlchemy models
│   │   └── config.py            # Configuration
│   └── requirements.txt
├── src/                         # Legacy/standalone components
│   └── api/
│       └── proxy_server.py      # WebSocket proxy
├── docs/                        # Documentation
├── scripts/                     # Utility scripts
└── docker-compose.yml
```

## 🧪 Testing

### Run Tests

```bash
# Frontend
cd frontend
pnpm test:unit

# Backend
cd backend
pytest

# Verify API connectivity
python src/api/verify_qwen_api.py
```

### Test Audio Files

Test audio files are located in `src/test/`:
- `测试录音.mp3` - Sample recording for testing

## 🚢 Deployment

### Docker (Recommended)

```bash
docker-compose up --build
```

### Manual Deployment

**Frontend:**
```bash
cd frontend
pnpm build
# Deploy .output/ to Vercel or similar
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `style:` formatting
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Alibaba Cloud](https://www.alibabacloud.com/) for Qwen API
- [Nuxt](https://nuxt.com/) for the frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [D3.js](https://d3js.org/) for tree visualization
