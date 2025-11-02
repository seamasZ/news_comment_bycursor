# 快速开始指南

## 前置要求

- Python 3.8+ (推荐 Python 3.11 或 3.12)
- Node.js 16+ (需要安装 Node.js，包含 npm)

## 快速启动步骤

### 1. 配置后端

```bash
cd backend

# 步骤1: 创建虚拟环境（必须先执行这一步！）
python -m venv venv

# 步骤2: 验证虚拟环境已创建
# 在PowerShell中运行: Test-Path venv\Scripts\Activate.ps1
# 应该返回 True

# 步骤3: 激活虚拟环境
# Windows (PowerShell)
# 方法1: 使用PowerShell脚本（推荐）
# 首先允许执行脚本（只需执行一次）:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后激活:
.\venv\Scripts\Activate.ps1
# 注意：完整路径是 venv\Scripts\Activate.ps1

# 方法2: 在PowerShell中执行.bat文件
cmd /c "venv\Scripts\activate.bat && powershell"

# 方法3: 切换到CMD窗口
cmd
venv\Scripts\activate.bat

# Windows (CMD)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend` 目录下创建 `.env` 文件（可以直接复制 `.env.example` 然后修改）：

```env
# 国内免费大模型配置（推荐）
# 选项1: DeepSeek（推荐 - 免费额度充足）
# 注册地址: https://platform.deepseek.com/api_keys
OPENAI_API_KEY=sk-63ee2464746d45daab9fde972b7c22d7
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat


### 3. 启动后端

```bash
# Windows
python main.py
# 或
start.bat

# Linux/Mac
python main.py
# 或
chmod +x start.sh
./start.sh
```

后端将在 `http://localhost:8000` 运行。

### 4. 配置前端

打开新终端窗口：

```bash
cd frontend
npm install
```

### 5. 启动前端

**重要**：首次使用前，必须先安装依赖！

```bash
# 首先安装依赖（只需执行一次）
npm install

# 然后启动前端服务
# Windows
npm run dev
# 或
start.bat

# Linux/Mac
npm run dev
# 或
chmod +x start.sh
./start.sh
```

前端将在 `http://localhost:5173` 运行。

### 6. 使用系统

1. 在浏览器中打开 `http://localhost:5173`
2. 输入新闻URL链接
3. 配置评论生成参数（可选）
4. 点击"生成评论"
5. 查看结果并导出CSV

## 注意事项

1. 如果没有OpenAI API密钥，系统会使用备用方法生成评论（质量较低）
2. 某些网站可能有反爬虫机制，建议使用公开可访问的新闻网站
3. 首次运行可能需要下载NLTK数据（如果需要）

### Q: pip安装依赖时遇到UnicodeDecodeError或pandas安装失败
A: 这通常是因为：
1. Python 3.13版本太新，某些包还不完全支持
2. 解决方案：
   - 使用Python 3.11或3.12（推荐）
   - 或者先单独安装numpy: `pip install numpy`
   - 或者跳过pandas（代码中未使用，已从requirements.txt移除）

## 常见问题

### Q: Test-Path venv\Scripts\Activate.ps1 返回 False
A: 这说明虚拟环境还没有创建！请先执行：
   ```powershell
   python -m venv venv
   ```
   等待创建完成后，再次检查：`Test-Path venv\Scripts\Activate.ps1` 应该返回 `True`

### Q: PowerShell中激活虚拟环境失败
A: PowerShell无法直接执行.bat文件，有以下解决方案：
1. **使用PowerShell脚本**（推荐）：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\venv\Scripts\Activate.ps1
   ```
2. **使用CMD执行**：
   ```powershell
   cmd /c "venv\Scripts\activate.bat && powershell"
   ```
3. **切换到CMD窗口**：
   ```powershell
   cmd
   venv\Scripts\activate.bat
   ```
4. **确保在正确目录**：虚拟环境必须在 `backend` 目录下，先执行 `cd news-comment-system\backend`

### Q: 后端启动失败 - ModuleNotFoundError: No module named 'sgmllib'
A: 这是因为 Python 3.13 移除了 sgmllib 模块。解决方案：
   1. **推荐方案**：使用 Python 3.11 或 3.12（推荐）
   2. **或**：已更新代码，移除对 newspaper3k 的依赖，现在只使用 BeautifulSoup，重新运行即可
   
### Q: 后端启动失败
A: 检查是否安装了所有依赖，确保Python版本 >= 3.8（推荐使用 Python 3.11 或 3.12）

### Q: npm 命令找不到 / 前端启动失败
A: 这说明 Node.js 没有安装或没有添加到 PATH。解决方案：
   1. **安装 Node.js**：
      - 访问 https://nodejs.org/
      - 下载并安装 LTS 版本（推荐）
      - 安装时确保勾选"Add to PATH"选项
   2. **验证安装**：
      ```powershell
      node -v    # 应该显示版本号，如 v18.17.0
      npm -v     # 应该显示版本号，如 9.6.7
      ```
   3. **如果已安装但仍找不到**：
      - 重启 PowerShell 或重启电脑
      - 检查环境变量 PATH 是否包含 Node.js 安装路径
      - 通常路径是：`C:\Program Files\nodejs\`

### Q: 前端启动失败
A: 检查Node.js版本，确保 >= 16，运行 `npm install` 安装依赖

### Q: 生成失败，请检查URL是否正确或稍后重试
A: 这个错误可能有以下原因：
   1. **后端服务没有运行**：
      - 检查后端是否在运行：访问 http://localhost:8000/docs
      - 如果没有运行，在新的终端窗口运行：`cd news-comment-system\backend` 然后 `python main.py`
   
   2. **无法连接到服务器**：
      - 确认后端服务在 http://localhost:8000 运行
      - 检查防火墙是否阻止了连接
   
   3. **新闻URL提取失败**：
      - 检查URL是否正确（需要完整的 http:// 或 https:// 开头）
      - **HTTP 403错误**：某些网站（如搜狐、新浪）有严格的反爬虫机制
      - **推荐使用**：新华网、人民网、光明网等对爬虫友好的新闻网站
      - 避免使用：搜狐、新浪、网易等可能有反爬虫的网站
      - 确保URL是公开可访问的（不需要登录）
   
   4. **API配置问题**：
      - 检查 `.env` 文件中的 API 密钥是否正确
      - 确认 DeepSeek API 密钥有效
   
   5. **查看详细错误**：
      - 打开浏览器开发者工具（F12）
      - 查看 Console 标签页的错误信息
      - 查看后端终端的错误日志

### Q: 无法连接API
A: 检查 `.env` 文件中的API密钥是否正确，检查网络连接

### Q: HTTP 403 错误或网页内容提取失败
A: 
   1. **403错误**：网站有反爬虫机制，已自动添加浏览器请求头，但某些网站仍可能阻止访问
   2. **推荐网站**：使用对爬虫友好的新闻网站：
      - 新华网 (www.xinhuanet.com)
      - 人民网 (www.people.com.cn)  
      - 光明网 (www.gmw.cn)
   3. **避免使用**：搜狐、新浪、网易等可能有严格反爬虫的网站
   4. 确保URL是具体的新闻文章链接（不是首页或列表页）

