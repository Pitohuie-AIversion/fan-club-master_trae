# Fan Club MkIV - GitHub Pages 文档站点

这是 Fan Club MkIV 项目的 GitHub Pages 文档站点，提供了完整的项目介绍、技术文档和使用指南。

## 🌐 在线访问

访问地址：`https://your-username.github.io/fan-club-master/`

## 📁 文件结构

```
docs/
├── index.html          # 主页面
├── styles.css          # 样式文件
├── script.js           # JavaScript 交互
├── architecture-diagram.svg  # 系统架构图
├── _config.yml         # GitHub Pages 配置
└── README.md           # 说明文档
```

## 🚀 启用 GitHub Pages

### 方法一：通过 GitHub 网页界面

1. 进入你的 GitHub 仓库
2. 点击 **Settings** 选项卡
3. 滚动到 **Pages** 部分
4. 在 **Source** 下选择 **Deploy from a branch**
5. 选择 **main** 分支和 **/ (root)** 或 **/docs** 文件夹
6. 点击 **Save**

### 方法二：使用 GitHub Actions（推荐）

创建 `.github/workflows/pages.yml` 文件：

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Pages
      uses: actions/configure-pages@v3
      
    - name: Upload artifact
      uses: actions/upload-pages-artifact@v2
      with:
        path: './docs'
        
    - name: Deploy to GitHub Pages
      id: deployment
      uses: actions/deploy-pages@v2
```

## 🎨 自定义配置

### 修改网站信息

编辑 `_config.yml` 文件中的以下内容：

```yaml
# 基本信息
title: 你的项目名称
description: 项目描述
baseurl: "/你的仓库名"
url: "https://你的用户名.github.io"

# 项目信息
project:
  name: 项目名称
  version: "版本号"
  description: 详细描述
```

### 修改样式

- 编辑 `styles.css` 来自定义网站外观
- 修改颜色主题、字体、布局等
- 支持响应式设计，适配移动设备

### 添加功能

- 编辑 `script.js` 来添加交互功能
- 支持平滑滚动、代码复制、移动菜单等
- 可以添加更多动画效果和用户体验优化

## 📊 功能特性

### 已实现功能

- ✅ 响应式设计
- ✅ 平滑滚动导航
- ✅ 代码高亮显示
- ✅ 代码一键复制
- ✅ 移动端适配
- ✅ 系统架构图
- ✅ API 文档展示
- ✅ 下载链接
- ✅ SEO 优化

### 可扩展功能

- 🔄 多语言支持
- 🔄 搜索功能
- 🔄 评论系统
- 🔄 Google Analytics
- 🔄 更多交互动画

## 🛠️ 本地开发

### 使用 Jekyll（推荐）

```bash
# 安装 Jekyll
gem install jekyll bundler

# 在 docs 目录下创建 Gemfile
echo 'source "https://rubygems.org"' > Gemfile
echo 'gem "github-pages", group: :jekyll_plugins' >> Gemfile

# 安装依赖
bundle install

# 启动本地服务器
bundle exec jekyll serve

# 访问 http://localhost:4000
```

### 使用简单 HTTP 服务器

```bash
# Python 3
python -m http.server 8000

# Node.js
npx http-server

# 访问 http://localhost:8000
```

## 📝 内容更新

### 更新项目信息

1. 修改 `index.html` 中的项目描述
2. 更新功能特性列表
3. 添加新的 API 文档
4. 更新下载链接

### 添加新页面

1. 在 `docs` 目录下创建新的 HTML 文件
2. 在导航菜单中添加链接
3. 更新 `_config.yml` 配置

### 更新架构图

1. 编辑 `architecture-diagram.svg` 文件
2. 使用 SVG 编辑器或代码直接修改
3. 确保图片在不同设备上正常显示

## 🔧 故障排除

### 常见问题

1. **页面无法访问**
   - 检查 GitHub Pages 是否已启用
   - 确认分支和文件夹设置正确
   - 等待几分钟让更改生效

2. **样式不显示**
   - 检查 CSS 文件路径
   - 确认 `baseurl` 配置正确
   - 清除浏览器缓存

3. **JavaScript 不工作**
   - 检查浏览器控制台错误
   - 确认文件路径正确
   - 检查语法错误

### 调试技巧

- 使用浏览器开发者工具
- 检查网络请求状态
- 查看 GitHub Actions 构建日志
- 使用 Jekyll 本地调试

## 📚 相关资源

- [GitHub Pages 官方文档](https://docs.github.com/en/pages)
- [Jekyll 官方文档](https://jekyllrb.com/docs/)
- [Markdown 语法指南](https://guides.github.com/features/mastering-markdown/)
- [SVG 教程](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial)

## 📄 许可证

本文档站点使用 MIT 许可证，详见项目根目录的 LICENSE 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进文档站点！

---

**注意**：记得将所有的 `your-username` 和 `fan-club-master` 替换为你的实际 GitHub 用户名和仓库名。