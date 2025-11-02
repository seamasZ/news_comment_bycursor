# 新闻评论生成系统

一个全栈式新闻评论生成系统，用户输入新闻链接后，系统自动生成新闻摘要并创建多条多样化的评论，支持不同语言风格和观点倾向。

## 功能特性

- 🌐 **网页内容提取**：自动从新闻网页中提取内容，去除广告、导航等无关元素
- 📝 **智能摘要生成**：使用大模型生成简洁的新闻摘要，包含标题、主要事件和关键信息
- 💬 **多样化评论生成**：生成多条不同语言风格（正式、随意、幽默、分析、情感）和观点倾向（积极、中性、消极）的评论
- 📊 **CSV导出**：支持将生成的评论导出为CSV格式
- 📚 **历史记录**：保存并展示历史生成记录

## 技术栈

### 后端
- **框架**：FastAPI
- **数据库**：SQLite（使用SQLAlchemy ORM）
- **网页提取**：newspaper3k + BeautifulSoup
- **大模型**：OpenAI API（可配置其他大模型API）

### 前端
- **框架**：React + Vite
- **HTTP客户端**：Axios
- **UI图标**：Lucide React

## 项目结构

```
news-comment-system/
├── backend/                 # 后端服务
│   ├── main.py             # FastAPI主应用
│   ├── requirements.txt    # Python依赖
│   ├── services/           # 业务逻辑服务
│   │   ├── news_extractor.py      # 新闻内容提取
│   │   ├── summary_generator.py   # 摘要生成
│   │   ├── comment_generator.py    # 评论生成
│   │   └── csv_exporter.py         # CSV导出
│   └── database/           # 数据库相关
│       ├── models.py       # 数据模型
│       └── crud.py         # CRUD操作
└── frontend/               # 前端应用
    ├── src/
    │   ├── App.jsx         # 主组件
    │   ├── App.css         # 样式文件
    │   ├── main.jsx        # 入口文件
    │   └── index.css       # 全局样式
    ├── package.json        # Node依赖
    └── vite.config.js      # Vite配置
```

## 安装和运行

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境（推荐）：
```bash
python -m venv venv

# Windows (PowerShell)
# 方法1: 使用PowerShell脚本（推荐）
.\venv\Scripts\Activate.ps1
# 如果遇到执行策略错误，运行: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 方法2: 在PowerShell中执行.bat文件
cmd /c "venv\Scripts\activate.bat && powershell"
# 或者切换到CMD:
cmd
venv\Scripts\activate.bat

# Windows (CMD)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 下载NLTK数据（如果需要）：
```python
python -c "import nltk; nltk.download('punkt')"
```

5. 配置环境变量：
创建 `.env` 文件（可以复制 `backend/.env.example` 然后修改，选择一种国内免费大模型）：
```env
# 选项1: DeepSeek（推荐 - 免费额度充足）
# 注册地址: https://platform.deepseek.com/api_keys
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# 选项2: Moonshot（有免费额度）
# 注册地址: https://platform.moonshot.cn/console/api-keys
# OPENAI_API_KEY=your_moonshot_api_key
# OPENAI_BASE_URL=https://api.moonshot.cn/v1
# OPENAI_MODEL=moonshot-v1-8k

# 选项3: 智谱AI GLM（有免费额度）
# 注册地址: https://open.bigmodel.cn/usercenter/apikeys
# OPENAI_API_KEY=your_zhipu_api_key
# OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
# OPENAI_MODEL=glm-4

# 选项4: 通义千问（阿里云，有免费额度）
# 注册地址: https://dashscope.console.aliyun.com/apiKey
# OPENAI_API_KEY=your_qianwen_api_key
# OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# OPENAI_MODEL=qwen-turbo

# 选项5: OpenAI（需要付费）
# OPENAI_API_KEY=your_openai_api_key
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_MODEL=gpt-3.5-turbo
```

**快速开始：**
1. 选择其中一个平台注册账号并获取 API Key
2. 复制 `backend/.env.example` 为 `backend/.env`
3. 取消注释对应平台的配置，填入你的 API Key
4. 保存文件即可使用

6. 启动后端服务：
```bash
python main.py
# 或
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 运行。

### 前端设置

**注意**：首先需要安装 Node.js（包含 npm）。如果 `npm -v` 命令失败，请先安装 Node.js。

1. **安装 Node.js**（如果未安装）：
   - 访问 https://nodejs.org/
   - 下载并安装 LTS 版本
   - 安装时确保勾选"Add to PATH"

2. 进入前端目录：
```bash
cd frontend
```

3. **安装依赖**（重要：首次使用必须先执行）：
```bash
npm install
```
这会安装所有前端依赖（包括 Vite、React 等）。

4. 启动开发服务器：
```bash
npm run dev
```

前端应用将在 `http://localhost:5173` 运行。

## 使用说明

1. **输入新闻URL**：在输入框中粘贴新闻网页的URL链接

2. **配置生成参数**：
   - **评论数量**：设置要生成的评论数量（1-50）
   - **语言风格分布**：调整不同风格的比例（正式、随意、幽默、分析、情感）
   - **观点倾向分布**：调整不同观点倾向的比例（积极、中性、消极）

3. **生成评论**：点击"生成评论"按钮，系统将：
   - 提取新闻内容
   - 生成新闻摘要
   - 生成多样化评论

4. **查看结果**：
   - 查看生成的摘要和评论
   - 点击"导出CSV"按钮导出评论
   - 在历史记录中查看之前的生成结果

5. **历史记录**：点击右上角的"历史记录"按钮查看所有历史生成记录

## API接口

### POST /api/generate
生成新闻摘要和评论

**请求体**：
```json
{
  "url": "https://example.com/news",
  "comment_config": {
    "count": 10,
    "styles": {
      "formal": 0.3,
      "casual": 0.3,
      "humorous": 0.2,
      "analytical": 0.1,
      "emotional": 0.1
    },
    "perspectives": {
      "positive": 0.4,
      "neutral": 0.4,
      "negative": 0.2
    }
  }
}
```

### GET /api/history
获取所有历史记录

### GET /api/history/{record_id}
获取单条历史记录

### GET /api/export/{record_id}
导出评论为CSV文件

## 注意事项

1. **大模型API配置**：系统默认使用OpenAI API，需要配置有效的API密钥。如果没有OpenAI API，可以修改代码使用其他大模型API（如文心一言、通义千问等）。

2. **网页内容提取**：某些网站可能有反爬虫机制，可能导致内容提取失败。建议使用公开可访问的新闻网站。

3. **生成质量**：评论生成质量取决于大模型的性能。建议使用GPT-4或其他高质量模型以获得更好的效果。

4. **性能优化**：对于大量评论生成，可能需要较长时间。系统设置了超时和错误处理机制。

## 开发计划

- [ ] 支持更多大模型API（文心一言、通义千问等）
- [ ] 添加评论编辑功能
- [ ] 支持批量URL处理
- [ ] 添加评论质量评分
- [ ] 支持自定义提示词模板

## 许可证

MIT License

## 作者

新闻评论生成系统

