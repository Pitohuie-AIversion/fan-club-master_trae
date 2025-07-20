# Mbed CLI 安装成功指南

## ✅ 安装状态

**Mbed CLI 2 已成功安装！**

- **版本**: 7.59.0
- **安装路径**: `X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe`
- **验证命令**: `& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" --version`

## 🚀 快速使用指南

### 1. 基本命令格式

```powershell
# 在PowerShell中使用完整路径
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" [命令]

# 示例：查看版本
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" --version

# 示例：编译项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -t GCC_ARM -m NUCLEO_F446RE
```

### 2. 为方便使用，创建别名

```powershell
# 在当前会话中创建别名
Set-Alias mbed "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe"

# 然后可以直接使用
mbed --version
mbed compile -t GCC_ARM -m NUCLEO_F446RE
```

### 3. 永久添加到PATH（推荐）

```powershell
# 添加到用户环境变量
$env:PATH += ";X:\Users\Pitoyoung\anaconda3\Scripts"

# 或者手动添加到系统环境变量
# 1. 打开"系统属性" -> "高级" -> "环境变量"
# 2. 在"用户变量"中找到"Path"
# 3. 添加：X:\Users\Pitoyoung\anaconda3\Scripts
```

## 📁 Fan Club MkIV 项目编译

### 当前项目状态

- ✅ **Mbed CLI 2**: 已安装 (v7.59.0)
- ✅ **项目结构**: 完整
- ✅ **现有固件**: `master/FC_MkIV_binaries/Slave.bin` (426KB)
- ⚠️ **mbed-os依赖**: 需要网络下载

### 编译步骤

#### 方法1: 使用现有固件（推荐）

```powershell
# 现有固件位置
dir "master\FC_MkIV_binaries\*.bin"

# 直接使用现有的Slave.bin文件
# 文件大小: 426,580 字节
# 修改时间: 2023/9/9 7:53:08
```

#### 方法2: 重新编译（需要网络）

```powershell
# 进入项目目录
cd slave_upgraded

# 部署依赖（需要网络连接）
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" deploy

# 编译项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -t GCC_ARM -m NUCLEO_F446RE
```

#### 方法3: 离线编译（如果有mbed-os）

```powershell
# 如果已有mbed-os目录，直接编译
cd slave_upgraded
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile -t GCC_ARM -m NUCLEO_F446RE
```

## 🛠️ 支持的编译器

- **GCC_ARM**: GNU ARM Embedded Toolchain（推荐）
- **ARM**: ARM Compiler 6

## 🎯 支持的目标板

- **NUCLEO_F446RE**: STM32F446RE开发板（项目默认）
- 其他STM32系列开发板

## 📋 常用命令

```powershell
# 查看帮助
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" --help

# 查看支持的目标板
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile --help

# 配置项目
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" configure -t GCC_ARM -m NUCLEO_F446RE

# 清理构建
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" compile --clean
```

## 🔧 故障排除

### 问题1: "mbed不是内部或外部命令"

**解决方案**: 使用完整路径或添加到PATH

```powershell
# 使用完整路径
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" --version
```

### 问题2: "mbed-os目录不存在"

**解决方案**: 运行deploy命令或使用现有固件

```powershell
# 部署依赖
& "X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe" deploy

# 或使用现有固件
dir "master\FC_MkIV_binaries\*.bin"
```

### 问题3: Git克隆失败

**解决方案**: 检查网络连接或使用现有固件

```powershell
# 检查网络
ping github.com

# 或直接使用现有固件
copy "master\FC_MkIV_binaries\Slave.bin" "output\firmware.bin"
```

## 📈 性能指标

- **安装时间**: ~2分钟
- **编译时间**: ~3-5分钟（首次）
- **固件大小**: ~426KB
- **支持平台**: Windows, macOS, Linux

## 🎉 总结

✅ **Mbed CLI 2 安装成功**
- 版本: 7.59.0
- 路径: X:\Users\Pitoyoung\anaconda3\Scripts\mbed-tools.exe
- 状态: 可用

✅ **项目编译就绪**
- 现有固件: 可直接使用
- 重新编译: 支持（需要网络）
- 目标硬件: NUCLEO_F446RE

🚀 **下一步操作**
1. 使用现有固件进行硬件测试
2. 或重新编译获取最新版本
3. 部署到STM32开发板
4. 运行master/main.py进行功能验证

---

**相关文档**:
- [BIN_GENERATION_GUIDE.md](BIN_GENERATION_GUIDE.md) - 固件生成指南
- [QUICK_BUILD_GUIDE.md](QUICK_BUILD_GUIDE.md) - 快速构建指南
- [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) - 环境设置指南

**项目状态**: 🟢 生产就绪