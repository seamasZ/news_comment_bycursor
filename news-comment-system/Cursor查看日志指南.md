# 在 Cursor 中查看后端日志指南

## 方法1：使用 Cursor 内置终端（推荐）

### 步骤：

1. **打开终端**
   - 快捷键：`` Ctrl + ` ``（反引号，Tab 键上方）
   - 或菜单：`Terminal` → `New Terminal`

2. **切换到后端目录**
   ```powershell
   cd news-comment-system\backend
   ```

3. **激活虚拟环境**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. **运行后端服务**
   ```powershell
   python main.py
   ```

5. **查看日志输出**
   - 所有日志会显示在终端面板中
   - 包括：
     - 服务器启动信息
     - 接收到的请求
     - 错误信息
     - API 调用日志

### 日志示例：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:52341 - "POST /api/generate HTTP/1.1" 200 OK
```

## 方法2：使用集成终端标签页

1. **打开多个终端**
   - 右键终端标签页 → `New Terminal`
   - 可以同时运行前端和后端

2. **分隔终端**
   - `Terminal` → `Split Terminal`
   - 一个用于后端，一个用于前端

## 方法3：查看日志文件（可选）

如果想将日志保存到文件，可以修改启动命令：

```powershell
python main.py > backend.log 2>&1
```

然后查看 `backend.log` 文件。

## 常见日志信息解读

### 正常启动：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```
✅ 后端服务已启动

### 请求成功：
```
INFO:     127.0.0.1:xxxxx - "POST /api/generate HTTP/1.1" 200 OK
```
✅ 请求处理成功

### 请求失败：
```
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  ...
```
❌ 查看详细错误信息定位问题

### 连接错误：
```
ERROR:    无法连接到服务器
```
❌ 检查网络或API配置

## 调试技巧

### 1. 实时查看日志
- 终端面板会实时显示所有日志
- 可以滚动查看历史记录

### 2. 搜索日志
- 在终端中使用 `` Ctrl + F `` 搜索关键词
- 例如搜索 "ERROR" 快速定位错误

### 3. 清理终端
- `` Ctrl + K `` 清除终端内容
- 或输入 `clear` 命令

### 4. 保存日志
- 右键终端内容 → `Copy`
- 或选中文本后复制

## 快速启动命令

创建一个快速启动脚本：

**backend/run.bat** (Windows):
```batch
@echo off
cd /d %~dp0
.\venv\Scripts\activate.bat
python main.py
```

然后在 Cursor 终端中运行：
```powershell
.\backend\run.bat
```

## 注意事项

1. **日志级别**：已设置为 `info`，会显示详细的请求和错误信息
2. **访问日志**：已启用，可以看到所有 HTTP 请求
3. **错误追踪**：所有异常都会显示完整的堆栈跟踪

## 常见问题

### Q: 看不到日志？
A: 确保终端在正确的目录下，并且虚拟环境已激活

### Q: 日志太多？
A: 可以修改 `log_level` 为 `warning` 或 `error` 只显示重要信息

### Q: 如何暂停/停止后端？
A: 在终端中按 `` Ctrl + C ``

