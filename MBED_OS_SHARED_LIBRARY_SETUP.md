# Mbed OS 共享库设置指南

## 🎯 问题描述

当使用Mbed CLI编译项目时，系统提示是否要将Mbed OS链接到共享位置。这个设置可以帮助节省磁盘空间，避免在每个项目中重复下载Mbed OS。

## 📋 设置步骤

### 1. 创建共享Mbed OS目录

```powershell
# 创建一个专门的目录存放共享的Mbed OS
mkdir "D:\mbed-os-shared"
cd "D:\mbed-os-shared"
```

### 2. 克隆Mbed OS到共享目录

```powershell
# 克隆官方Mbed OS仓库
git clone https://github.com/ARMmbed/mbed-os.git

# 或者如果网络问题，使用镜像
git clone https://gitee.com/mirrors/mbed-os.git
```

### 3. 设置共享库路径

在Mbed CLI提示时，输入共享Mbed OS的路径：

```
D:\mbed-os-shared\mbed-os
```

### 4. 验证设置

```powershell
# 检查共享库是否正确设置
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" config --list
```

## 🚀 Fan Club MkIV 项目的快速解决方案

### 方案1: 使用现有固件（推荐）

```powershell
# 直接使用已编译的固件
dir "master\FC_MkIV_binaries\*.bin"

# 复制到输出目录
copy "master\FC_MkIV_binaries\Slave.bin" "output\firmware.bin"
```

### 方案2: 本地Mbed OS设置

```powershell
# 在项目根目录创建本地mbed-os
cd "d:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae"
mkdir mbed-os-local
cd mbed-os-local

# 克隆轻量版本
git clone --depth 1 https://github.com/ARMmbed/mbed-os.git
```

### 方案3: 修复现有项目配置

```powershell
# 进入slave目录
cd slave

# 检查mbed-os.lib文件内容
Get-Content mbed-os.lib

# 如果需要，更新为本地路径
echo "../mbed-os-local/mbed-os" > mbed-os.lib
```

## 🔧 配置文件修复

### 修复重复配置问题

如果遇到"Setting already defined"错误，需要检查配置文件：

```powershell
# 检查mbed_app.json
Get-Content slave_upgraded\mbed_app.json

# 检查是否有重复的配置项
# 删除重复的nanostack-hal.event_loop_thread_stack_size设置
```

### 清理配置冲突

```json
{
    "target_overrides": {
        "*": {
            "platform.stdio-baud-rate": 115200,
            "platform.default-serial-baud-rate": 115200
        }
    }
}
```

## 📁 目录结构建议

```
D:\mbed-projects\
├── mbed-os-shared\          # 共享Mbed OS
│   └── mbed-os\            # 官方Mbed OS仓库
├── fan-club-mkiv\          # 项目目录
│   ├── slave\              # 从机代码
│   ├── slave_upgraded\     # 升级版从机代码
│   └── master\             # 主机代码
└── build-output\           # 编译输出
    ├── slave.bin
    └── bootloader.bin
```

## 🛠️ 环境变量设置

### 设置Mbed OS路径

```powershell
# 设置环境变量
$env:MBED_OS_PATH = "D:\mbed-os-shared\mbed-os"

# 永久设置（需要管理员权限）
[Environment]::SetEnvironmentVariable("MBED_OS_PATH", "D:\mbed-os-shared\mbed-os", "User")
```

### 设置编译器路径

```powershell
# 如果使用GCC ARM
$env:GCC_ARM_PATH = "C:\Program Files (x86)\GNU Arm Embedded Toolchain\10 2021.10\bin"
```

## 🎯 编译命令

### 使用共享Mbed OS编译

```powershell
# 进入项目目录
cd slave

# 配置项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" configure -t GCC_ARM -m NUCLEO_F446RE

# 编译项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile
```

### 指定Mbed OS路径编译

```powershell
# 使用--mbed-os-path参数
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -t GCC_ARM -m NUCLEO_F446RE --mbed-os-path "D:\mbed-os-shared\mbed-os"
```

## 🔍 故障排除

### 问题1: Git克隆失败

```powershell
# 使用浅克隆
git clone --depth 1 https://github.com/ARMmbed/mbed-os.git

# 或使用国内镜像
git clone https://gitee.com/mirrors/mbed-os.git
```

### 问题2: 路径不存在

```powershell
# 检查路径是否存在
Test-Path "D:\mbed-os-shared\mbed-os"

# 创建符号链接
New-Item -ItemType SymbolicLink -Path "mbed-os" -Target "D:\mbed-os-shared\mbed-os"
```

### 问题3: 权限问题

```powershell
# 以管理员身份运行PowerShell
Start-Process powershell -Verb runAs

# 或修改目录权限
icacls "D:\mbed-os-shared" /grant Users:F
```

## 📈 性能优化

### 编译缓存

```powershell
# 启用编译缓存
$env:MBED_CACHE = "D:\mbed-cache"
mkdir "D:\mbed-cache"
```

### 并行编译

```powershell
# 使用多线程编译
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -j 4
```

## 🎉 推荐配置

### 最佳实践设置

```powershell
# 1. 创建项目专用目录
mkdir "D:\mbed-projects\fan-club-mkiv"

# 2. 设置共享Mbed OS
mkdir "D:\mbed-projects\mbed-os-shared"
cd "D:\mbed-projects\mbed-os-shared"
git clone --depth 1 https://github.com/ARMmbed/mbed-os.git

# 3. 在项目中使用相对路径
echo "..\..\mbed-os-shared\mbed-os" > mbed-os.lib

# 4. 编译项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -t GCC_ARM -m NUCLEO_F446RE
```

## 📋 检查清单

- [ ] 创建共享Mbed OS目录
- [ ] 克隆Mbed OS仓库
- [ ] 设置正确的路径
- [ ] 验证mbed-os.lib文件
- [ ] 检查配置文件冲突
- [ ] 测试编译命令
- [ ] 验证生成的.bin文件

## 🔗 相关资源

- [Mbed OS官方文档](https://os.mbed.com/docs/mbed-os/)
- [Mbed CLI 2文档](https://github.com/ARMmbed/mbed-tools)
- [STM32 Nucleo开发板文档](https://www.st.com/en/evaluation-tools/nucleo-f446re.html)

---

**总结**: 设置共享Mbed OS可以节省磁盘空间和下载时间。对于Fan Club MkIV项目，推荐先使用现有的.bin文件进行测试，然后根据需要设置共享库进行重新编译。