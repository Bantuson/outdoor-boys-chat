# 🏕️ Outdoor Boys Chat

A fully offline-capable knowledge base chat for [Outdoor Boys](https://www.youtube.com/@OutdoorBoys) YouTube fans. Query survival tips, building techniques, fishing advice, recipes, and dad jokes - all running locally in your browser!

![License](https://img.shields.io/badge/license-MIT-green)
![PWA](https://img.shields.io/badge/PWA-ready-blue)
![Offline](https://img.shields.io/badge/offline-capable-orange)

## ✨ Features

- **🔒 100% Private** - Everything runs locally in your browser
- **📴 Offline Ready** - Works without internet after first load
- **🧠 AI-Powered** - Uses WebLLM for intelligent responses
- **🔍 Semantic Search** - Finds relevant content by meaning, not just keywords
- **📂 Organized by Category** - Winter survival, crafting, fishing, recipes, and more
- **😄 Dad Jokes Included** - Because what's Outdoor Boys without the humor?

## 🛠️ Tech Stack

| Component     | Technology                         |
| ------------- | ---------------------------------- |
| Frontend      | React + TypeScript + Vite          |
| Styling       | TailwindCSS                        |
| LLM Inference | WebLLM (Llama 3.2 3B)              |
| Embeddings    | Transformers.js (all-MiniLM-L6-v2) |
| Vector Search | Orama                              |
| Offline       | Service Workers + IndexedDB        |
| Data Pipeline | Python + YouTube API               |

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Modern browser with WebGPU support (Chrome 113+, Edge 113+, Firefox 121+)
- ~4GB disk space (for AI model cache)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/outdoor-boys-chat.git
cd outdoor-boys-chat

# Install dependencies
npm install

# Start development server
npm run dev
```

Open http://localhost:5173 in your browser.

### First Load

On first load, the app will:

1. Download the embedding model (~30MB)
2. Load the knowledge base (~5MB)
3. Download the LLM model (~2-4GB)

After the initial download, everything is cached and works offline!

## 📊 Building the Knowledge Base

To scrape new content from the Outdoor Boys channel:

### Setup

```bash
cd scraper
pip install -r requirements.txt
```

### Configure API Keys

1. Get a [YouTube Data API key](https://console.cloud.google.com/apis/api/youtube.googleapis.com)
2. (Optional) Get an [Anthropic API key](https://console.anthropic.com) for fact extraction

### Run the Scraper

```bash
# Basic scrape (YouTube API only)
python main.py --api-key YOUR_YOUTUBE_API_KEY --max-videos 50

# With LLM fact extraction
python main.py --api-key YOUR_YOUTUBE_API_KEY --anthropic-key YOUR_ANTHROPIC_KEY --max-videos 50
```

### Copy to Frontend

```bash
cp -r knowledge-base/* ../public/knowledge-base/
```

## 📁 Project Structure

```
outdoor-boys-chat/
├── src/
│   ├── components/
│   │   └── ChatInterface.tsx    # Main chat UI
│   ├── lib/
│   │   └── rag-pipeline.ts      # RAG implementation
│   ├── types/
│   │   └── knowledge-base.ts    # TypeScript types
│   ├── App.tsx
│   └── main.tsx
├── public/
│   └── knowledge-base/          # Static knowledge base files
├── scraper/
│   ├── main.py                  # YouTube scraper
│   └── requirements.txt
└── package.json
```

## 🎯 Knowledge Base Categories

| Category              | Content Type                                      |
| --------------------- | ------------------------------------------------- |
| 🥶 Winter Survival    | Cold weather tips, shelter building, staying warm |
| 🏠 Building           | Cabin construction, woodworking, DIY projects     |
| 🎣 Fishing            | Ice fishing, salmon fishing, techniques           |
| ⚙️ Gear               | Equipment reviews and recommendations             |
| 🍳 Recipes            | Campfire cooking, outdoor meals                   |
| 💡 Life Lessons       | Wisdom from the wilderness                        |
| 😂 Dad Jokes          | Classic Zach humor                                |
| 📍 Business Directory | Charters, lodges, stores mentioned in videos      |

## 🔧 Configuration

### Environment Variables

Create a `.env` file for API keys:

```env
VITE_YOUTUBE_API_KEY=your_key_here
```

### Model Selection

Edit `src/lib/rag-pipeline.ts` to use different models:

```typescript
// Smaller, faster model
const LLM_MODEL = "Phi-3-mini-4k-instruct-q4f16_1-MLC";

// Larger, more capable model
const LLM_MODEL = "Llama-3.2-3B-Instruct-q4f16_1-MLC";
```

## 📦 Deployment

### Build for Production

```bash
npm run build
```

### Deploy to Vercel

```bash
npx vercel
```

### Deploy to Netlify

```bash
npm run build
# Drag & drop 'dist' folder to Netlify
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - feel free to use this for your own fan projects!

## 🙏 Acknowledgments

- [Outdoor Boys](https://www.youtube.com/@OutdoorBoys) for the amazing content
- [WebLLM](https://webllm.mlc.ai/) for browser-based LLM inference
- [Transformers.js](https://huggingface.co/docs/transformers.js) for client-side embeddings
- [Orama](https://orama.com/) for the search engine

---

**Disclaimer**: This is a fan project and is not affiliated with or endorsed by Outdoor Boys. All content is sourced from publicly available YouTube videos.
