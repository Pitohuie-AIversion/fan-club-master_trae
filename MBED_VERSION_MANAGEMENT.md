# Mbed OS 版本管理策略

## 概述

本项目采用双版本并行策略，同时维护 Mbed OS 5.9.0 和 6.16.0 两个版本，以满足不同的开发和部署需求。

## 版本分布

### Mbed OS 5.9.0 (Legacy)
- **位置**: `mbed5.9/` 目录
- **用途**: 兼容性支持，现有硬件的稳定运行
- **状态**: 维护模式，仅修复关键bug

### Mbed OS 6.16.0 (Current)
- **位置**: `mbed6.16/` 目录
- **用途**: 新功能开发，推荐用于新项目
- **状态**: 活跃开发

### 根目录项目
- **slave/**: 使用本地共享库 `D:\mbed-os-shared\mbed-os`
- **slave_bootloader/**: 使用特定commit版本

## mbed-os.lib 文件配置

```
项目结构:
├── slave/mbed-os.lib                    → D:\mbed-os-shared\mbed-os
├── slave_bootloader/mbed-os.lib         → https://github.com/ARMmbed/mbed-os/#866850acc15e86cd4ac11bf4404078a49f921ddd
├── mbed5.9/slave/mbed-os.lib           → https://github.com/ARMmbed/mbed-os/#mbed-os-5.15.8
├── mbed5.9/slave_bootloader/mbed-os.lib → https://github.com/ARMmbed/mbed-os/#mbed-os-5.15.8
├── mbed6.16/slave/mbed-os.lib          → https://github.com/ARMmbed/mbed-os/#mbed-os-6.16.0
└── mbed6.16/slave_bootloader/mbed-os.lib → https://github.com/ARMmbed/mbed-os/#mbed-os-6.16.0
```

## 使用指南

### 新项目开发
- **推荐**: 使用 `mbed6.16/` 目录下的项目
- **原因**: 最新功能、更好的性能、长期支持

### 现有项目维护
- **选择**: 根据当前部署的硬件版本选择对应目录
- **迁移**: 逐步从5.9.0迁移到6.16.0

### 编译选择

#### 编译 Mbed OS 5.9.0 项目
```bash
cd mbed5.9/slave
mbed compile -t GCC_ARM -m NUCLEO_F446RE
```

#### 编译 Mbed OS 6.16.0 项目
```bash
cd mbed6.16/slave
mbed compile -t GCC_ARM -m NUCLEO_F446RE
```

#### 编译根目录项目（开发版）
```bash
cd slave
mbed compile -t GCC_ARM -m NUCLEO_F446RE
```

## 版本兼容性

### API 差异
- **串口通信**: 6.16.0 使用新的 UnbufferedSerial API
- **线程管理**: 6.16.0 改进了 RTOS 接口
- **网络栈**: 6.16.0 提供更稳定的网络支持

### 迁移注意事项
1. **代码审查**: 检查已弃用的API调用
2. **配置文件**: 更新 mbed_app.json 配置
3. **依赖库**: 确认第三方库兼容性
4. **测试验证**: 全面测试硬件功能

## 维护策略

### 短期（3-6个月）
- 同时维护两个版本
- 新功能优先在6.16.0开发
- 关键bug修复同步到5.9.0

### 中期（6-12个月）
- 逐步迁移现有项目到6.16.0
- 减少5.9.0的新功能开发
- 建立迁移测试流程

### 长期（12个月后）
- 完全迁移到6.16.0或更新版本
- 5.9.0进入仅安全更新模式
- 清理旧版本代码

## Git 管理

### 分支策略
- `master`: 主分支，包含所有版本
- `mbed-5.9-stable`: 5.9.0稳定版本
- `mbed-6.16-dev`: 6.16.0开发版本

### 提交规范
```
[mbed5.9] 修复串口通信bug
[mbed6.16] 添加新的传感器支持
[common] 更新文档和配置
```

## 文件忽略

已在 `.gitignore` 中配置忽略以下文件：
- `mbed-os/` 目录（部署文件）
- `BUILD/` 和 `cmake_build/` 目录
- `venv_python311/` 虚拟环境
- `*.bin`, `*.hex`, `*.elf` 编译产物

## 故障排除

### 常见问题
1. **编译错误**: 检查mbed-os.lib路径是否正确
2. **版本冲突**: 确认使用正确的工具链版本
3. **依赖缺失**: 运行 `mbed deploy` 更新依赖

### 支持联系
- 技术问题: 查看项目Wiki
- Bug报告: 提交GitHub Issue
- 版本迁移: 参考迁移指南

---

**最后更新**: 2025年1月
**维护者**: Fan Club MkIV 开发团队