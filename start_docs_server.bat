@echo off
echo ========================================
echo Fan Club MkIV - GitHub Pages 本地预览
echo ========================================
echo.

cd /d "%~dp0"

echo 正在启动本地文档服务器...
echo.
echo 请选择启动方式:
echo 1. 使用 Python HTTP 服务器 (推荐)
echo 2. 使用 Node.js HTTP 服务器
echo 3. 使用 Jekyll (需要先安装)
echo.
set /p choice=请输入选择 (1-3): 

if "%choice%"=="1" goto python_server
if "%choice%"=="2" goto node_server
if "%choice%"=="3" goto jekyll_server
goto python_server

:python_server
echo.
echo 使用 Python HTTP 服务器启动...
echo 访问地址: http://localhost:8000
echo 按 Ctrl+C 停止服务器
echo.
cd docs
python -m http.server 8000
goto end

:node_server
echo.
echo 使用 Node.js HTTP 服务器启动...
echo 访问地址: http://localhost:8080
echo 按 Ctrl+C 停止服务器
echo.
cd docs
npx http-server -p 8080
goto end

:jekyll_server
echo.
echo 使用 Jekyll 启动...
echo 访问地址: http://localhost:4000
echo 按 Ctrl+C 停止服务器
echo.
cd docs
if not exist Gemfile (
    echo 创建 Gemfile...
    echo source "https://rubygems.org" > Gemfile
    echo gem "github-pages", group: :jekyll_plugins >> Gemfile
    echo gem "webrick", "~> 1.7" >> Gemfile
)
if not exist Gemfile.lock (
    echo 安装依赖...
    bundle install
)
bundle exec jekyll serve
goto end

:end
echo.
echo 服务器已停止
pause