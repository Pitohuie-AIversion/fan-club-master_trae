# Mbed CLI 安装指南

## 🎯 概述

Mbed CLI 是 ARM Mbed 平台的命令行工具，用于编译、构建和管理 Mbed 项目。本指南提供多种安装方法。

## 📋 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.8 或更高版本
- **内存**: 至少 2GB RAM
- **磁盘空间**: 至少 1GB 可用空间

## 🚀 方法一：安装 Mbed CLI 2（推荐）

### 步骤 1：检查 Python 环境

```powershell
# 检查 Python 版本
python --version
# 或者
python3 --version

# 如果没有 Python，请下载安装：
# https://www.python.org/downloads/
```

### 步骤 2：升级 pip

```powershell
# 升级 pip 到最新版本
python -m pip install --upgrade pip
```

### 步骤 3：安装 Mbed CLI 2

```powershell
# 安装 Mbed Tools (Mbed CLI 2)
pip install mbed-tools

# 验证安装
mbed --version
```

### 步骤 4：配置环境

```powershell
# 配置 Mbed 工具
mbed config --list

# 设置默认编译器（可选）
mbed config GCC_ARM_PATH "C:\Program Files (x86)\GNU Arm Embedded Toolchain\bin"
```

## 🔧 方法二：使用 Conda 安装

如果您使用 Anaconda 或 Miniconda：

```powershell
# 创建新环境
conda create -n mbed python=3.9
conda activate mbed

# 安装 Mbed CLI 2
pip install mbed-tools

# 验证安装
mbed --version
```

## 🎨 方法三：安装 Mbed Studio（图形界面）

### 优势
- 包含完整的编译环境
- 图形界面操作
- 集成调试功能
- 自动管理依赖

### 安装步骤

1. **下载 Mbed Studio**：
   - 访问：https://os.mbed.com/studio/
   - 选择 Windows 版本下载

2. **安装**：
   - 运行下载的安装程序
   - 按照向导完成安装
   - 默认安装路径：`C:\Program Files\Mbed Studio`

3. **验证**：
   - 启动 Mbed Studio
   - 检查是否能正常打开项目

## ⚡ 快速安装脚本

创建自动化安装脚本：

```powershell
# install_mbed_cli.ps1

Write-Host "🚀 开始安装 Mbed CLI 2..." -ForegroundColor Green

# 检查 Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 未安装" -ForegroundColor Red
    Write-Host "请先安装 Python 3.8+: https://www.python.org/downloads/"
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# 显示 Python 版本
$pythonVersion = python --version
Write-Host "✅ 检测到 Python: $pythonVersion" -ForegroundColor Green

# 升级 pip
Write-Host "📦 升级 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 安装 Mbed CLI 2
Write-Host "📦 安装 Mbed CLI 2..." -ForegroundColor Yellow
pip install mbed-tools

# 验证安装
if (Get-Command mbed -ErrorAction SilentlyContinue) {
    $mbedVersion = mbed --version
    Write-Host "🎉 Mbed CLI 安装成功: $mbedVersion" -ForegroundColor Green
    
    # 显示配置信息
    Write-Host "\n📋 当前配置:" -ForegroundColor Cyan
    mbed config --list
    
    Write-Host "\n✅ 安装完成！现在可以使用以下命令:" -ForegroundColor Green
    Write-Host "  mbed --help" -ForegroundColor White
    Write-Host "  mbed compile -t ARMC6 -m NUCLEO_F446RE" -ForegroundColor White
    Write-Host "  python build_firmware.py" -ForegroundColor White
} else {
    Write-Host "❌ Mbed CLI 安装失败" -ForegroundColor Red
    Write-Host "请检查网络连接和 Python 环境" -ForegroundColor Yellow
    exit 1
}

Write-Host "\n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
```

## 🔍 验证安装

### 基本验证

```powershell
# 检查 Mbed CLI 版本
mbed --version

# 显示帮助信息
mbed --help

# 列出支持的目标板
mbed target -S

# 列出支持的编译器
mbed toolchain -S
```

### 高级验证

```powershell
# 检查配置
mbed config --list

# 测试编译（在项目目录中）
cd slave_upgraded
mbed compile -t ARMC6 -m NUCLEO_F446RE --profile debug
```

## 🛠️ 安装编译器

### ARM Compiler 6（推荐）

1. **通过 Mbed Studio 安装**（最简单）：
   - 安装 Mbed Studio 会自动包含 ARM Compiler 6

2. **手动安装**：
   - 下载：https://developer.arm.com/tools-and-software/embedded/arm-compiler
   - 安装后添加到系统 PATH

### GCC ARM Embedded

```powershell
# 下载并安装 GCC ARM Embedded
# https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

# 验证安装
arm-none-eabi-gcc --version
```

## 🚨 故障排除

### 问题 1：`mbed: command not found`

**原因**：Mbed CLI 未正确安装或不在 PATH 中

**解决方案**：
```powershell
# 重新安装
pip uninstall mbed-tools
pip install mbed-tools

# 检查 Python Scripts 目录是否在 PATH 中
echo $env:PATH

# 手动添加到 PATH（临时）
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python39\Scripts"
```

### 问题 2：`pip install` 失败

**解决方案**：
```powershell
# 使用国内镜像源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple mbed-tools

# 或者使用阿里云镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ mbed-tools

# 跳过 SSL 验证（不推荐，仅在必要时使用）
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org mbed-tools
```

### 问题 3：权限错误

**解决方案**：
```powershell
# 使用用户安装（推荐）
pip install --user mbed-tools

# 或者以管理员身份运行 PowerShell
# 右键 PowerShell -> "以管理员身份运行"
pip install mbed-tools
```

### 问题 4：编译器未找到

**解决方案**：
```powershell
# 检查编译器路径
mbed config --list

# 设置编译器路径
mbed config GCC_ARM_PATH "C:\Program Files (x86)\GNU Arm Embedded Toolchain\bin"
mbed config ARMC6_PATH "C:\Program Files\ARMCompiler6.16\bin"

# 验证编译器
arm-none-eabi-gcc --version
armclang --version
```

## 📊 性能优化

### 加速编译

```powershell
# 使用并行编译
mbed compile -j 4

# 使用缓存
mbed config cache.enabled true

# 设置临时目录到 SSD
mbed config cache.dir "D:\mbed_cache"
```

### 减少下载时间

```powershell
# 使用本地镜像
mbed config protocol.default-protocol https
mbed config protocol.timeout 30
```

## 🎯 推荐配置

### 开发环境配置

```powershell
# 设置默认目标和编译器
mbed config target NUCLEO_F446RE
mbed config toolchain ARMC6

# 启用详细输出
mbed config build.verbose true

# 设置并行编译
mbed config build.parallel 4
```

### 项目配置

在项目根目录创建 `.mbedignore` 文件：
```
# 忽略备份文件
*.backup
*.bak

# 忽略临时文件
BUILD/
.mbed_cache/

# 忽略 IDE 文件
.vscode/
.idea/
```

## 📚 相关资源

- **官方文档**：https://os.mbed.com/docs/mbed-os/latest/tools/index.html
- **Mbed CLI 2 文档**：https://github.com/ARMmbed/mbed-tools
- **Mbed Studio 下载**：https://os.mbed.com/studio/
- **ARM 编译器**：https://developer.arm.com/tools-and-software/embedded/arm-compiler
- **GCC ARM 工具链**：https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

## ✅ 安装检查清单

- [ ] Python 3.8+ 已安装
- [ ] pip 已升级到最新版本
- [ ] Mbed CLI 2 安装成功
- [ ] `mbed --version` 命令正常工作
- [ ] 编译器已安装并配置
- [ ] 能够编译测试项目
- [ ] 环境变量配置正确

## 🎉 快速开始

安装完成后，立即测试：

```powershell
# 进入项目目录
cd d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae

# 运行自动化编译脚本
python build_firmware.py

# 或者手动编译
cd slave_upgraded
mbed compile -t ARMC6 -m NUCLEO_F446RE
```

---

*最后更新: 2025年1月*  
*适用版本: Mbed CLI 2.x*  
*状态: 安装指南 ✅*