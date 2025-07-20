# Mbed 库升级指南

## 概述

本指南详细说明如何升级 Fan Club MkIV 项目中的 Mbed OS 库，包括从机端和引导加载程序的升级步骤。

## 当前状态

### 现有版本信息
- **编译工具**: ARM GCC Tools 7.3.1 / 7.2.1
- **Mbed CLI**: 1.7.5
- **目标板**: NUCLEO_F429ZI
- **当前 Mbed OS**: 通过 `mbed-os.lib` 文件引用

### 项目结构
```
├── slave_upgraded/          # 升级后的从机代码
├── slave_bootloader_upgraded/  # 升级后的引导程序
├── slave/                   # 原始从机代码
└── slave_bootloader/        # 原始引导程序
```

## 升级步骤

### 1. 准备工作

#### 1.1 检查当前 Mbed OS 版本
```bash
cd slave_upgraded
mbed ls
```

#### 1.2 备份重要配置
- `mbed_app.json` - 应用配置
- `mbed_config.h` - 编译配置
- `.mbed` - 项目设置

### 2. 升级 Mbed OS

#### 2.1 更新到最新稳定版本
```bash
cd slave_upgraded
mbed update
```

#### 2.2 或指定特定版本
```bash
cd slave_upgraded
mbed update mbed-os-6.17.0  # 例如升级到 6.17.0
```

#### 2.3 检查升级结果
```bash
mbed ls
```

### 3. 配置文件更新

#### 3.1 更新 mbed_app.json

**原始配置** (`slave/mbed_app.json`):
```json
{
    "target_overrides": {
        "NUCLEO_F429ZI": {
            "target.bootloader_img": "bootloader/NUCLEO_F429ZI.bin"
        }
    }
}
```

**升级后可能需要的配置** (`slave_upgraded/mbed_app.json`):
```json
{
    "target_overrides": {
        "NUCLEO_F429ZI": {
            "target.bootloader_img": "bootloader/NUCLEO_F429ZI.bin",
            "platform.stdio-baud-rate": 115200,
            "platform.default-serial-baud-rate": 115200,
            "target.network-default-interface-type": "ETHERNET"
        }
    },
    "macros": [
        "MBED_CONF_LWIP_IPV4_ENABLED=1",
        "MBED_CONF_LWIP_ETHERNET_ENABLED=1"
    ]
}
```

#### 3.2 更新引导程序配置

**原始配置** (`slave_bootloader/mbed_app.json`):
```json
{
    "config": {
        "network-interface": {
            "help": "options are ETHERNET, WIFI_ESP8266, WIFI_IDW0XX1",
            "value": "ETHERNET"
        },
        "wifi-ssid": {
            "value": "\"SSID\""
        },
        "wifi-password": {
            "value": "\"Password\""
        },
        "firmware-update-file": {
            "value": "\"/sd/Slave_application.bin\""
        }
    },
    "target_overrides": {
        "NUCLEO_F429ZI": {
            "target.restrict_size": "0x80000"
        }
    }
}
```

### 4. 代码兼容性检查

#### 4.1 网络 API 变更

**Mbed OS 5.x 到 6.x 的主要变更**:

1. **网络接口初始化**:
```cpp
// 旧版本 (Mbed OS 5.x)
EthernetInterface eth;
eth.connect();

// 新版本 (Mbed OS 6.x)
EthernetInterface *eth = EthernetInterface::get_default_instance();
eth->connect();
```

2. **套接字 API**:
```cpp
// 旧版本
UDPSocket socket;
socket.open(&eth);

// 新版本
UDPSocket socket;
socket.open(eth);
```

#### 4.2 线程 API 变更

```cpp
// 旧版本
Thread thread;
thread.start(callback(function));

// 新版本 (如果需要)
Thread thread(osPriorityNormal, OS_STACK_SIZE);
thread.start(callback(function));
```

### 5. 编译和测试

#### 5.1 编译从机程序
```bash
cd slave_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

#### 5.2 编译引导程序
```bash
cd slave_bootloader_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

#### 5.3 处理编译错误

**常见问题和解决方案**:

1. **头文件路径变更**:
```cpp
// 可能需要更新的包含路径
#include "mbed.h"
#include "EthernetInterface.h"
#include "UDPSocket.h"
```

2. **API 弃用警告**:
```cpp
// 检查并更新弃用的 API 调用
// 参考 Mbed OS 迁移指南
```

### 6. 功能验证

#### 6.1 基本功能测试
- [ ] 网络连接
- [ ] UDP 通信
- [ ] PWM 输出
- [ ] 风扇控制
- [ ] LED 指示

#### 6.2 通信协议测试
- [ ] 广播接收
- [ ] 命令处理
- [ ] 状态反馈
- [ ] 固件更新

### 7. 性能优化

#### 7.1 内存使用优化
```json
// 在 mbed_app.json 中调整内存设置
{
    "target_overrides": {
        "NUCLEO_F429ZI": {
            "target.restrict_size": "0x80000",
            "rtos.main-thread-stack-size": 4096,
            "rtos.timer-thread-stack-size": 768
        }
    }
}
```

#### 7.2 网络性能调优
```json
{
    "macros": [
        "MBED_CONF_LWIP_TCP_SOCKET_MAX=4",
        "MBED_CONF_LWIP_UDP_SOCKET_MAX=4",
        "MBED_CONF_LWIP_SOCKET_MAX=8"
    ]
}
```

## 升级后的文件修改

### 1. 主要修改文件

#### slave_upgraded/main.cpp
```cpp
// 可能需要的修改示例
#include "mbed.h"
#include "EthernetInterface.h"
#include "UDPSocket.h"
#include "Communicator.h"

// 更新网络初始化代码
EthernetInterface *eth = EthernetInterface::get_default_instance();
if (eth->connect() != 0) {
    printf("Network connection failed\n");
    return -1;
}
```

#### slave_upgraded/Communicator.cpp
```cpp
// 更新套接字初始化
int Communicator::initNetwork() {
    // 获取默认网络接口
    _eth = EthernetInterface::get_default_instance();
    
    // 连接网络
    if (_eth->connect() != 0) {
        return -1;
    }
    
    // 初始化套接字
    if (_socket.open(_eth) != 0) {
        return -1;
    }
    
    return 0;
}
```

### 2. 配置文件更新

#### slave_upgraded/mbed_app.json
```json
{
    "config": {
        "network-interface": {
            "help": "Network interface type",
            "value": "ETHERNET"
        }
    },
    "target_overrides": {
        "NUCLEO_F429ZI": {
            "target.bootloader_img": "bootloader/NUCLEO_F429ZI.bin",
            "target.restrict_size": "0x80000",
            "platform.stdio-baud-rate": 115200,
            "target.network-default-interface-type": "ETHERNET"
        }
    },
    "macros": [
        "MBED_CONF_LWIP_IPV4_ENABLED=1",
        "MBED_CONF_LWIP_ETHERNET_ENABLED=1",
        "MBED_CONF_NSAPI_DEFAULT_STACK=LWIP"
    ]
}
```

## 故障排除

### 1. 编译错误

**错误**: `'EthernetInterface' was not declared`
**解决**: 添加正确的头文件包含
```cpp
#include "EthernetInterface.h"
```

**错误**: `undefined reference to 'EthernetInterface::get_default_instance()'`
**解决**: 检查 mbed_app.json 中的网络配置

### 2. 运行时错误

**问题**: 网络连接失败
**检查**:
- 以太网线缆连接
- 网络配置正确性
- DHCP 服务可用性

**问题**: 内存不足
**解决**: 调整堆栈大小和内存分配

### 3. 性能问题

**问题**: 响应延迟增加
**优化**:
- 调整线程优先级
- 优化网络缓冲区大小
- 减少不必要的内存分配

## 版本兼容性矩阵

| Mbed OS 版本 | GCC 版本 | 支持状态 | 备注 |
|-------------|----------|----------|------|
| 5.15.x      | 7.3.1    | ✅ 当前  | 稳定版本 |
| 6.15.x      | 9.2.1    | ✅ 推荐  | 长期支持 |
| 6.17.x      | 10.3.1   | ✅ 最新  | 最新功能 |

## 回滚计划

如果升级失败，可以通过以下步骤回滚：

1. **恢复原始文件**:
```bash
cp -r slave/* slave_upgraded/
cp -r slave_bootloader/* slave_bootloader_upgraded/
```

2. **重新编译**:
```bash
cd slave_upgraded
mbed compile -t GCC_ARM -m NUCLEO_F429ZI
```

3. **验证功能**:
- 测试基本通信
- 验证风扇控制
- 检查网络连接

## 最佳实践

1. **渐进式升级**: 先升级到中间版本，再升级到目标版本
2. **充分测试**: 在每个升级步骤后进行完整的功能测试
3. **文档更新**: 及时更新项目文档和配置说明
4. **版本锁定**: 在生产环境中锁定特定的 Mbed OS 版本

## 参考资源

- [Mbed OS 官方文档](https://os.mbed.com/docs/)
- [Mbed OS 迁移指南](https://os.mbed.com/docs/mbed-os/latest/porting/)
- [NUCLEO-F429ZI 平台页面](https://os.mbed.com/platforms/ST-Nucleo-F429ZI/)
- [Mbed CLI 文档](https://os.mbed.com/docs/mbed-os/latest/tools/)

---

*本指南基于 Fan Club MkIV 项目的实际需求编写，建议在升级前仔细阅读并测试每个步骤。*