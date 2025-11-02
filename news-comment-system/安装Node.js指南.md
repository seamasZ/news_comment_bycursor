# 安装 Node.js 指南

## 问题
如果运行 `npm -v` 时出现"无法将'npm'项识别为 cmdlet"错误，说明 Node.js 没有安装或没有添加到系统 PATH。

## 安装步骤

### Windows 系统

1. **下载 Node.js**
   - 访问官方网站：https://nodejs.org/
   - 点击下载 **LTS 版本**（长期支持版本，更稳定）
   - 例如：Windows Installer (.msi) 64-bit

2. **安装 Node.js**
   - 双击下载的 `.msi` 文件
   - 按照安装向导完成安装
   - **重要**：在安装选项中，确保勾选以下选项：
     - ✅ "Automatically install the necessary tools"
     - ✅ 确保 Node.js 被添加到 PATH 环境变量

3. **验证安装**
   打开新的 PowerShell 窗口（重要：需要新窗口），运行：
   ```powershell
   node -v
   npm -v
   ```
   应该分别显示 Node.js 和 npm 的版本号。

4. **如果仍然找不到命令**
   - 重启 PowerShell 窗口
   - 重启电脑（有时需要重启才能刷新环境变量）
   - 手动检查环境变量：
     - 右键"此电脑" -> 属性 -> 高级系统设置 -> 环境变量
     - 在"系统变量"的 PATH 中添加：`C:\Program Files\nodejs\`

## 验证安装成功

安装成功后，应该能够运行：
```powershell
node -v    # 例如：v18.17.0
npm -v    # 例如：9.6.7
```

## 安装前端依赖

安装 Node.js 后，进入前端目录安装依赖：
```powershell
cd news-comment-system\frontend
npm install
```

## 启动前端

```powershell
npm run dev
```

前端将在 http://localhost:5173 运行。

## 常见问题

### Q: 安装了 Node.js 但还是找不到 npm
A: 
1. 关闭并重新打开 PowerShell
2. 检查 Node.js 安装路径是否在 PATH 中
3. 尝试重启电脑

### Q: 应该安装哪个版本的 Node.js？
A: 推荐安装 LTS（长期支持）版本，通常是较新的稳定版本，兼容性最好。

### Q: 是否需要全局安装其他工具？
A: 不需要。npm 会随 Node.js 一起安装。



