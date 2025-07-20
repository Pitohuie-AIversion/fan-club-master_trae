# Fan Club MkIV Mbed 库升级说明

## 升级后的目录结构

本次升级创建了以下新目录和文件：

```
fan-club-master_trae/
├── slave_upgraded/                    # 升级后的从机代码
│   ├── mbed_app.json                 # 更新的配置文件
│   ├── Communicator_Updated_Example.cpp  # 示例更新代码
│   └── [其他原始文件...]              # 从原始 slave/ 复制的文件
├── slave_bootloader_upgraded/         # 升级后的引导程序
│   ├── mbed_app.json                 # 更新的配置文件
│   └── [其他原始文件...]              # 从原始 slave_bootloader/ 复制的文件
├── Mbed_Library_Upgrade_Guide.md     # 详细升级指南
├── Fan_Club_MkIV_Wiki.md             # 项目 Wiki 文档
└── UPGRADE_README.md                 # 本文件
```

## 主要变更内容

### 1. 配置文件更新

#### slave_upgraded/mbed_app.json
- 添加了网络接口配置
- 增加了 LWIP 网络协议栈设置
- 优化了内存和线程配置
- 添加了串口波特率设置

#### slave_bootloader_upgraded/mbed_app.json
- 更新了固件更新文件路径
- 添加了网络协议栈宏定义
- 优化了 NUCLEO_F429ZI 目标板配置

### 2. 代码示例更新

#### Communicator_Updated_Example.cpp
这个文件展示了如何更新 Communicator.cpp 以适配新版本的 Mbed OS：

- **网络接口初始化**：使用 `EthernetInterface::get_default_instance()`
- **套接字 API**：更新为新的 API 调用方式
- **线程管理**：使用新的线程创建和管理方法
- **错误处理**：采用新的错误类型和处理机制

## 使用方法

### 1. 编译升级后的从机程序

```bash
cd slave_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

### 2. 编译升级后的引导程序

```bash
cd slave_bootloader_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

### 3. 应用代码更新

如果需要应用示例代码中的更新：

1. 备份原始的 `Communicator.cpp`：
   ```bash
   cp Communicator.cpp Communicator_backup.cpp
   ```

2. 参考 `Communicator_Updated_Example.cpp` 中的更新模式

3. 逐步更新您的代码以适配新的 API

### 4. 测试和验证

升级后请进行以下测试：

- [ ] 网络连接功能
- [ ] UDP 通信
- [ ] 风扇控制
- [ ] LED 指示
- [ ] 固件更新功能

## 重要注意事项

### 1. API 变更

**网络接口**：
```cpp
// 旧版本
EthernetInterface eth;
eth.connect();

// 新版本
EthernetInterface *eth = EthernetInterface::get_default_instance();
eth->connect();
```

**套接字**：
```cpp
// 旧版本
socket.open(&eth);

// 新版本
socket.open(eth);
```

### 2. 配置变更

新的配置文件包含了更多的网络和系统设置，确保这些设置与您的硬件和网络环境兼容。

### 3. 内存使用

新配置优化了内存使用，但请根据实际需求调整堆栈大小和缓冲区设置。

## 回滚方案

如果升级遇到问题，可以使用原始的 `slave/` 和 `slave_bootloader/` 目录中的文件：

```bash
# 恢复原始配置
cp slave/mbed_app.json slave_upgraded/mbed_app.json
cp slave_bootloader/mbed_app.json slave_bootloader_upgraded/mbed_app.json

# 重新编译
cd slave_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

## 进一步升级

### 1. 更新 Mbed OS 版本

```bash
cd slave_upgraded
mbed update mbed-os-6.17.0  # 或其他目标版本
```

### 2. 检查依赖库

```bash
mbed ls
```

### 3. 更新编译工具链

确保使用兼容的 ARM GCC 工具链版本。

## 技术支持

如需更详细的升级指导，请参考：

1. **详细升级指南**：`Mbed_Library_Upgrade_Guide.md`
2. **项目 Wiki**：`Fan_Club_MkIV_Wiki.md`
3. **Mbed OS 官方文档**：https://os.mbed.com/docs/

## 版本信息

- **原始版本**：基于 Mbed OS 5.x
- **升级目标**：Mbed OS 6.x
- **编译工具**：ARM GCC 7.3.1+ 
- **目标板**：NUCLEO_F429ZI

---

*升级完成后，建议进行全面的功能测试以确保系统稳定性。*