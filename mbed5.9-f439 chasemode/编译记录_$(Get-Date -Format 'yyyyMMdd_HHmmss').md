# Fan Club MkIV mbed5.9 编译记录

## 编译时间
生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

## 编译环境
- **Python 版本**：Python 3.7.1
- **Python 环境路径**：C:\Users\Pitoyoung\miniconda3\envs\mbed-py37
- **Mbed CLI 版本**：1.10.5
- **目标板**：NUCLEO_F429ZI
- **工具链**：GCC_ARM

## 编译结果

### 1. Slave 项目编译成功
- **项目路径**：`D:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\mbed5.9\slave`
- **输出文件**：`BUILD\NUCLEO_F429ZI\GCC_ARM\slave.bin`
- **文件大小**：159,940 字节
- **内存使用**：
  - Total Static RAM memory (data + bss): 59,836 bytes
  - Total Flash memory (text + data): 159,306 bytes

#### 模块内存分布
```
+---------------------------------+--------+-------+-------+
| Module                          |  .text | .data |  .bss |
+---------------------------------+--------+-------+-------+
| Communicator.o                  |  10144 |     0 |     0 |
| Fan.o                           |    904 |   106 |     0 |
| FastPWM\Device                  |    148 |     0 |     0 |
| FastPWM\FastPWM_common.o        |    504 |     0 |     0 |
| Processor.o                     |   3560 |     0 |     0 |
| [fill]                          |    306 |    10 |    36 |
| [lib]\c.a                       |  42010 |  2472 |    89 |
| [lib]\gcc.a                     |   3464 |     0 |     0 |
| [lib]\misc                      |    252 |    16 |    28 |
| [lib]\stdc++.a                  |      1 |     0 |     0 |
| backups\PeripheralPins_backup.o |   1140 |     0 |     0 |
| main.o                          |   1598 |     0 |     0 |
| mbed-os\drivers                 |   2539 |     4 |   100 |
| mbed-os\events                  |   1543 |     0 |  1576 |
| mbed-os\features                |  50161 |    99 | 46708 |
| mbed-os\hal                     |   1971 |     4 |    68 |
| mbed-os\platform                |   4774 |   264 |   305 |
| mbed-os\rtos                    |  15416 |   168 |  6081 |
| mbed-os\targets                 |  14030 |     5 |  1337 |
| print.o                         |   1685 |     8 |   352 |
| Subtotals                       | 156150 |  3156 | 56680 |
+---------------------------------+--------+-------+-------+
```

### 2. Slave Bootloader 项目编译成功
- **项目路径**：`D:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\mbed5.9\slave_bootloader`
- **输出文件**：`BUILD\NUCLEO_F429ZI\GCC_ARM\slave_bootloader.bin`
- **文件大小**：262,144 字节
- **应用程序文件**：`slave_bootloader_application.bin` (181,072 字节)
- **内存使用**：
  - Total Static RAM memory (data + bss): 60,220 bytes
  - Total Flash memory (text + data): 179,645 bytes

#### 内存区域配置
- **应用程序区域**：大小 0x40000，偏移 0x8000000
- **后应用程序区域**：大小 0x1c0000，偏移 0x8040000
- **使用空间**：0x40000

#### 模块内存分布
```
+---------------------------+--------+-------+-------+
| Module                    |  .text | .data |  .bss |
+---------------------------+--------+-------+-------+
| PeripheralPins_original.o |    384 |     0 |     0 |
| [fill]                    |    364 |    11 |    52 |
| [lib]\c.a                 |  48725 |  2472 |    89 |
| [lib]\gcc.a               |   7224 |     0 |     0 |
| [lib]\misc                |    252 |    16 |    28 |
| [lib]\nosys.a             |     32 |     0 |     0 |
| [lib]\stdc++.a            |   7673 |    40 |   204 |
| main.o                    |  11238 |     9 |  1086 |
| mbed-http\http_parser     |  11120 |     0 |     0 |
| mbed-os\drivers           |   2216 |     4 |   140 |
| mbed-os\events            |   1611 |     0 |  1576 |
| mbed-os\features          |  51147 |    99 | 46706 |
| mbed-os\hal               |   1839 |     4 |    68 |
| mbed-os\platform          |   5008 |   264 |   305 |
| mbed-os\rtos              |  15560 |   168 |  6081 |
| mbed-os\targets           |  12160 |     5 |   793 |
| Subtotals                 | 176553 |  3092 | 57128 |
+---------------------------+--------+-------+-------+
```

## 编译命令

### Slave 项目
```bash
cd D:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\mbed5.9\slave
C:\Users\Pitoyoung\miniconda3\envs\mbed-py37\Scripts\mbed.exe compile -t GCC_ARM -m NUCLEO_F429ZI
```

### Slave Bootloader 项目
```bash
cd D:\2025\chendashuai_wind_turnnal\fan-club-master\fan-club-master_trae\mbed5.9\slave_bootloader
C:\Users\Pitoyoung\miniconda3\envs\mbed-py37\Scripts\mbed.exe compile -t GCC_ARM -m NUCLEO_F429ZI
```

## 生成的文件

### Slave 项目输出
- `slave.bin` - 主应用程序二进制文件 (159,940 字节)

### Slave Bootloader 项目输出
- `slave_bootloader.bin` - 完整引导加载程序二进制文件 (262,144 字节)
- `slave_bootloader_application.bin` - 应用程序部分 (181,072 字节)

## 部署说明

1. **引导加载程序部署**：将 `slave_bootloader.bin` 烧录到 STM32 NUCLEO-F429ZI 开发板
2. **应用程序更新**：可通过网络或串口使用 `slave.bin` 进行固件更新
3. **调试连接**：使用 460800 波特率连接串口进行调试

## 注意事项

- 编译使用 Python 3.7.1 环境，确保与 Mbed OS 5.x 的兼容性
- 两个项目都成功编译，无错误或警告
- 内存使用在 STM32F429ZI 的限制范围内
- 引导加载程序支持固件更新功能