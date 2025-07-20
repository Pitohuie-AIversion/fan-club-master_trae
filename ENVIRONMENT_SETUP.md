# Fan Club MkIV - 编译环境快速设置指南

## 🚨 当前状态

**检测结果**：
- ❌ Mbed CLI 未安装
- ✅ 发现现有固件文件：`Slave.bin` (426KB, 2023年版本)
- ⚠️ 需要安装编译工具来生成最新固件

## 🎯 快速解决方案

### 选项 1：使用现有固件 ⭐ **立即可用**

如果您只是想快速测试系统，可以使用现有的固件：

```powershell
# 现有固件位置
master\FC_MkIV_binaries\Slave.bin  # 426KB, 从机固件
```

**部署步骤**：
1. 连接 NUCLEO-F446RE 开发板到电脑
2. 开发板会显示为 USB 存储设备
3. 将 `Slave.bin` 复制到开发板根目录
4. 开发板自动重启并加载固件
5. 运行 `master/main.py` 开始使用

### 选项 2：安装完整编译环境 ⭐ **推荐**

为了生成最新的固件和进行开发，建议安装完整环境：

#### 步骤 1：安装 Mbed Studio（推荐）

1. **下载 Mbed Studio**：
   - 访问：https://os.mbed.com/studio/
   - 下载适用于 Windows 的版本
   - 安装到默认位置

2. **验证安装**：
   ```powershell
   # 检查 Mbed Studio 是否安装
   Get-ChildItem "C:\Program Files\Mbed Studio*" -ErrorAction SilentlyContinue
   ```

#### 步骤 2：使用 Mbed Studio 编译

1. 启动 **Mbed Studio**
2. 选择 `File` → `Import Program`
3. 导入项目目录：
   ```
   d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae
   ```
4. 编译从机固件：
   - 选择 `slave_upgraded` 文件夹
   - 右键 → `Set as Active Program`
   - 点击 **Build** 按钮 🔨
5. 编译引导程序：
   - 选择 `slave_bootloader_upgraded` 文件夹
   - 右键 → `Set as Active Program`
   - 点击 **Build** 按钮 🔨

#### 步骤 3：安装 Mbed CLI 2（命令行选项）

如果您偏好命令行工具：

```powershell
# 安装 Python（如果未安装）
# 下载：https://www.python.org/downloads/

# 安装 Mbed CLI 2
pip install mbed-tools

# 验证安装
mbed --version
```

## 🔧 故障排除

### 问题 1：Mbed CLI 安装失败

**解决方案**：
```powershell
# 升级 pip
python -m pip install --upgrade pip

# 重新安装 Mbed CLI
pip install --upgrade mbed-tools

# 添加到 PATH（如果需要）
# 将 Python Scripts 目录添加到系统 PATH
```

### 问题 2：编译器未找到

**解决方案**：
1. 安装 **ARM Compiler 6**（包含在 Mbed Studio 中）
2. 或者安装 **GCC ARM Embedded**：
   - 下载：https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm
   - 添加到系统 PATH

### 问题 3：目标板不识别

**解决方案**：
1. 安装 **STM32 USB 驱动**：
   - 下载：https://www.st.com/en/development-tools/stsw-link009.html
2. 确认开发板连接正常
3. 检查设备管理器中是否显示 ST-Link

## 🚀 一键安装脚本

创建自动化安装脚本：

```powershell
# install_environment.ps1
Write-Host "安装 Fan Club MkIV 编译环境..."

# 检查 Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python 未安装，请先安装 Python 3.8+"
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# 安装 Mbed CLI
Write-Host "📦 安装 Mbed CLI 2..."
pip install mbed-tools

# 验证安装
if (Get-Command mbed -ErrorAction SilentlyContinue) {
    Write-Host "✅ Mbed CLI 安装成功"
    mbed --version
} else {
    Write-Host "❌ Mbed CLI 安装失败"
    exit 1
}

Write-Host "🎉 环境安装完成！"
Write-Host "现在可以运行: python build_firmware.py"
```

## 📋 环境检查清单

运行以下命令检查环境：

```powershell
# 检查 Python
python --version

# 检查 Mbed CLI
mbed --version

# 检查编译器
arm-none-eabi-gcc --version

# 检查项目结构
ls slave_upgraded, slave_bootloader_upgraded

# 检查现有固件
ls master\FC_MkIV_binaries\*.bin
```

## 🎯 推荐工作流

### 快速开始（使用现有固件）
```powershell
# 1. 部署现有固件到硬件
# 2. 测试系统功能
cd master
python main.py
```

### 完整开发（安装环境后）
```powershell
# 1. 安装 Mbed Studio 或 Mbed CLI
# 2. 编译最新固件
python build_firmware.py
# 3. 部署到硬件
# 4. 测试和开发
```

## 📚 相关资源

- **Mbed Studio 下载**：https://os.mbed.com/studio/
- **Mbed CLI 文档**：https://os.mbed.com/docs/mbed-os/latest/tools/index.html
- **STM32 驱动**：https://www.st.com/en/development-tools/stsw-link009.html
- **ARM 编译器**：https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm

## ✅ 总结

**立即可用**：使用现有的 `Slave.bin` 文件进行快速测试

**长期开发**：安装 Mbed Studio 获得完整的开发环境

**命令行用户**：安装 Mbed CLI 2 进行自动化编译

选择最适合您需求的方案开始使用 Fan Club MkIV 项目！

---

*最后更新: 2025年1月*  
*状态: 环境配置指南 ✅*