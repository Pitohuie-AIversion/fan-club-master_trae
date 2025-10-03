# Auto Flash mbed/DAPLink Tool

## 概述

这是一个用于自动检测和烧录mbed/DAPLink开发板的PowerShell脚本工具。当您插入兼容的开发板时，脚本会自动检测设备并将固件文件烧录到板卡中。

## 功能特性

- 🔍 **自动设备检测**: 持续监控USB设备，自动识别mbed/DAPLink板卡
- 📋 **多标签支持**: 支持多种设备标签模式（MBED*, DAPLINK*, NUCLEO*, NODE_*, NOD_*, MAINTENANCE*）
- 🚀 **一键烧录**: 检测到设备后自动复制固件文件并监控烧录过程
- 📊 **详细调试信息**: 提供完整的设备检测、文件操作和烧录监控日志
- 🔊 **声音反馈**: 烧录成功或失败时提供蜂鸣提示
- ⚡ **实时监控**: 监控DAPLink处理状态，检测FAIL.TXT和DETAILS.TXT文件

## 系统要求

- Windows操作系统
- PowerShell 5.0或更高版本
- 管理员权限（推荐）

## 使用方法

### 1. 准备固件文件

确保您的固件文件 `slave.bin` 位于脚本同一目录下。

### 2. 启动自动烧录

```powershell
# 在PowerShell中运行
powershell -ExecutionPolicy Bypass -File .\auto_flash_mbed.ps1
```

### 3. 插入设备

脚本启动后，只需插入您的mbed/DAPLink开发板，脚本会自动：
- 检测设备
- 复制固件文件
- 监控烧录过程
- 提供结果反馈

## 支持的设备标签

脚本支持以下设备标签模式：
- `MBED*` - 标准mbed设备
- `DAPLINK*` - DAPLink设备
- `NUCLEO*` - STM32 Nucleo板卡
- `NODE_*` - Node MCU等设备
- `NOD_*` - 简化的Node设备标签
- `MAINTENANCE*` - 维护模式设备

## 调试信息说明

脚本提供详细的调试输出：

```
[DEBUG] Monitoring label patterns: MBED*, DAPLINK*, NUCLEO*, NODE_*, NOD_*, MAINTENANCE*
[DEBUG] Poll interval: 2 seconds
[DEBUG] Starting USB device monitoring...
[DEBUG] Scanning USB devices...
[DEBUG] Found 5 volumes with drive letters
[DEBUG] Matched target devices: 1
```

### 设备检测阶段
```
==> [Device Detection] Found new target device G:\
    Label: NOD_F439ZI
    File System: FAT
    Size: 6.03 MB
```

### 文件操作阶段
```
[File Operation] Preparing to copy firmware file
Source file: D:\path\to\slave.bin
Target path: G:\slave.bin
File size: 408.82 KB
[File Operation] Starting copy...
✓ [File Operation] Copy successful to G:\slave.bin
```

### 烧录监控阶段
```
[Flash Monitor] Waiting for DAPLink processing (max 15 seconds)...
[Flash Monitor] Check 1 second...
[Flash Monitor] DETAILS.TXT file detected
[Flash Monitor] Check 2 second...
[Flash Monitor] Firmware file disappeared, DAPLink received
✓ [Flash Result] Flash successful! DAPLink received and processed firmware
```

## 烧录结果

### 成功情况
- ✅ 固件文件成功复制到设备
- ✅ DAPLink接收并处理固件
- ✅ 固件文件从设备消失（表示已被处理）
- ✅ 播放成功提示音

### 失败情况
- ❌ 检测到FAIL.TXT文件
- ❌ 设备处于MAINTENANCE模式
- ❌ 文件复制失败
- ❌ 烧录超时
- ❌ 播放错误提示音

## 故障排除

### 设备未被检测到
1. 确认设备已正确连接
2. 检查设备标签是否在支持列表中
3. 尝试重新插拔设备
4. 检查USB驱动是否正常

### 烧录失败
1. 检查FAIL.TXT文件内容获取错误信息
2. 确认固件文件完整性
3. 尝试手动烧录验证设备状态
4. 检查设备是否处于MAINTENANCE模式

### 脚本无响应
1. 检查PowerShell执行策略
2. 确认脚本路径正确
3. 以管理员权限运行
4. 检查系统资源使用情况

## 配置选项

脚本中的主要配置参数：

```powershell
$POLL_INTERVAL = 2                    # 设备扫描间隔（秒）
$WAIT_AFTER_COPY_SEC = 15             # 烧录监控超时时间（秒）
$FW_BIN = "slave.bin"                 # 固件文件名
```

## 技术细节

- **设备检测**: 使用PowerShell的Get-Volume命令扫描所有卷
- **标签匹配**: 使用WildcardPattern进行模式匹配
- **文件监控**: 通过Test-Path检查文件存在状态
- **状态反馈**: 监控DETAILS.TXT和FAIL.TXT文件变化

## 版本历史

- **v1.2**: 修复设备标签检测问题，添加英文调试信息
- **v1.1**: 增加详细调试输出和设备信息显示
- **v1.0**: 基础自动烧录功能

## 许可证

本项目遵循项目根目录下的LICENSE文件。

## 贡献

欢迎提交问题报告和功能请求。如需贡献代码，请先创建issue讨论您的想法。

---

**注意**: 使用前请确保您了解烧录操作的风险，建议先在测试设备上验证脚本功能。