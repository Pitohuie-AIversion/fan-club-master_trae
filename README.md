# Fan Club MkIV - 分布式风扇阵列控制系统

<div align="center">

![Fan Club MkIV](https://img.shields.io/badge/Fan%20Club-MkIV-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![C++](https://img.shields.io/badge/C++-Mbed%20OS-red?style=for-the-badge&logo=cplusplus)

**由 zhaoyangmu 和 chendashuai 开发**

*作者: zhaoyangmu, chendashuai*

</div>

---

## 📋 项目概述

Fan Club MkIV 是一个先进的分布式风扇阵列控制系统，采用主从架构设计，通过以太网实现对多个风扇模块的精确控制和实时监控。该系统专为航空航天研究和风洞实验设计，提供高精度的气流控制能力。

### 🎯 核心特性

- **分布式控制**: 主从架构，支持多达数百个风扇模块
- **实时监控**: 毫秒级响应的状态监控和反馈
- **精确控制**: 高精度占空比控制和转速调节
- **网络通信**: 基于以太网的可靠通信协议
- **图形界面**: 现代化的GUI界面，支持实时数据可视化
- **配置管理**: 灵活的配置文件系统，支持多种实验场景
- **信号处理**: 内置数字滤波和信号质量监控
- **数据存储**: 多格式数据记录和导出功能

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        主控端 (Python)                          │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   GUI Frontend  │  FCCommunicator │    External Control         │
│   - 控制界面     │  - 网络管理      │    - 外部监听器              │
│   - 实时监控     │  - 从机通信      │    - 命令处理器              │
│   - 数据可视化   │  - 状态同步      │    - 协议解析                │
└─────────────────┴─────────────────┴─────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │   以太网通信   │
                    └───────┬───────┘
                            │
┌─────────────────────────────────────────────────────────────────┐
│                      从机端 (C++/Mbed OS)                       │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Communicator  │    Processor    │       Fan Control          │
│   - 网络接收     │   - 命令解析     │       - PWM控制             │
│   - 协议处理     │   - 状态管理     │       - 转速监控            │
│   - 数据发送     │   - 错误处理     │       - 硬件接口            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### 📊 数据流管道

```
控制向量 [占空比分配] ──────────────────────────────────────────────>
命令向量 [ADD, REBOOT, FIRMWARE...] ─────────────────────────────>
                                                              ┌──────────┐
前端 ◄─── 反馈向量 F [占空比和转速] ◄─────────────────────────── │   后端   │
     ◄─── 从机向量 S [从机状态] ◄──────────────────────────── │          │
     ◄─── 网络向量 N [全局IP和端口] ◄─────────────────────────── │  通信器   │
     ◄─── 打印消息 [日志和调试信息] ◄─────────────────────────── └──────────┘
```

---

## 🚀 快速开始

### 📋 系统要求

- **主控端**: Windows/Linux/macOS，Python 3.8+
- **从机端**: NUCLEO-F446RE 开发板，Mbed OS 5.9+
- **网络**: 以太网连接，支持DHCP

### 🔧 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd fan-club-master
```

#### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

主要依赖包括：
- `tkinter` - GUI界面
- `numpy` - 数值计算
- `matplotlib` - 数据可视化
- `scipy` - 信号处理
- `pandas` - 数据分析
- `h5py` - 数据存储
- `psutil` - 系统监控
- `pillow` - 图像处理

#### 3. 配置启动参数

编辑 `master/main.py`，选择合适的配置文件：

```python
# 可选启动配置（只保留其中一行，注释其它行）
# INIT_PROFILE = "MODULE"    # 单模块测试
INIT_PROFILE = "TENX10"      # 10x10阵列 (推荐)
# INIT_PROFILE = "DEV1"      # 开发配置1
# INIT_PROFILE = "BOX"       # 盒式配置
# INIT_PROFILE = "CAST"      # CAST实验配置
```

#### 4. 烧录从机固件

```bash
# 方法1: 使用现有固件 (快速测试)
# 将 master/FC_MkIV_binaries/Slave.bin 复制到 NUCLEO-F446RE 根目录

# 方法2: 编译最新固件 (推荐)
cd slave
mbed compile -t GCC_ARM -m NUCLEO_F446RE
cp BUILD/NUCLEO_F446RE/GCC_ARM/slave.bin /path/to/nucleo/
```

#### 5. 网络配置

确保主控端和从机在同一网络中：
- 从机会自动通过DHCP获取IP地址
- 主控端会自动发现网络中的从机
- 默认通信端口: 25000

#### 6. 启动系统

```bash
cd master
python main.py
```

---

## 📁 项目结构

```
fan-club-master/
├── master/                          # 主控端代码
│   ├── main.py                      # 程序入口点
│   ├── fc/                          # 核心功能模块
│   │   ├── frontend/                # 前端GUI模块
│   │   │   ├── gui/                 # Tkinter界面
│   │   │   │   ├── widgets/         # UI组件
│   │   │   │   │   ├── control.py   # 控制面板
│   │   │   │   │   ├── network.py   # 网络管理
│   │   │   │   │   ├── monitoring.py # 监控界面
│   │   │   │   │   └── external.py  # 外部控制
│   │   │   │   ├── theme/           # 主题系统
│   │   │   │   └── embedded/        # 嵌入式资源
│   │   │   └── filter_config_gui.py # 滤波器配置
│   │   ├── backend/                 # 后端通信模块
│   │   │   ├── mkiii/               # MkIII通信协议
│   │   │   │   ├── FCCommunicator.py # 主通信器
│   │   │   │   ├── FCSlave.py       # 从机管理
│   │   │   │   └── exceptions.py    # 异常处理
│   │   │   ├── external.py          # 外部控制接口
│   │   │   ├── mapper.py            # 地址映射
│   │   │   ├── signal_acquisition.py # 信号采集
│   │   │   ├── digital_filtering.py # 数字滤波
│   │   │   └── data_storage.py      # 数据存储
│   │   ├── archive.py               # 配置管理
│   │   ├── standards.py             # 通信标准
│   │   ├── printer.py               # 日志系统
│   │   └── utils.py                 # 工具函数
│   ├── profiles/                    # 配置文件目录
│   ├── FC_MkIV_binaries/           # 预编译固件
│   └── tests/                       # 测试文件
├── slave/                           # 从机端代码 (C++/Mbed OS)
│   ├── main.cpp                     # 从机主程序
│   ├── Communicator.h/cpp           # 通信模块
│   ├── Fan.h/cpp                    # 风扇控制
│   ├── Processor.h/cpp              # 命令处理器
│   └── mbed-os.lib                  # Mbed OS库
├── slave_bootloader/                # 引导加载程序
├── mbed5.9/                        # Mbed OS 5.9
├── docs/                           # 文档目录
│   ├── Fan_Club_MkIV_Wiki.md       # 详细技术文档
│   └── ENVIRONMENT_SETUP.md        # 环境配置指南
└── README.md                       # 本文件
```

---

## 🎮 使用指南

### 🖥️ GUI界面操作

#### 控制面板
- **网格显示**: 实时显示风扇阵列状态
- **占空比控制**: 拖拽滑块调节风扇转速
- **模式选择**: 支持统一控制、配置文件加载等
- **实时反馈**: 显示当前转速和状态信息

#### 网络管理
- **从机发现**: 自动扫描和连接网络中的从机
- **状态监控**: 实时显示从机连接状态
- **固件更新**: 支持远程固件升级
- **网络诊断**: 连接质量和延迟监控

#### 监控系统
- **信号质量**: 实时监控通信信号质量
- **性能指标**: 系统资源使用情况
- **数据记录**: 自动记录实验数据
- **报警系统**: 异常状态自动报警

### 🔧 配置文件系统

系统支持多种预定义配置：

- **TENX10**: 10x10风扇阵列配置
- **MODULE**: 单模块测试配置
- **DEV1/DEV2/DEV3**: 开发测试配置
- **BOX**: 盒式风扇配置
- **CAST**: CAST实验专用配置

### 📡 外部控制接口

系统提供外部控制API，支持：
- TCP/UDP命令接口
- RESTful API (计划中)
- MATLAB/Python客户端库
- 实时数据流接口

---

## 🔬 技术特性

### 🌐 网络通信
- **协议**: 自定义TCP协议，基于JSON消息格式
- **可靠性**: 自动重连、心跳检测、错误恢复
- **性能**: 低延迟通信，支持高频率控制更新
- **安全性**: 消息校验、连接认证

### 🎛️ 控制算法
- **PID控制**: 精确的转速闭环控制
- **前馈控制**: 快速响应的开环控制
- **自适应控制**: 根据负载自动调节参数
- **故障检测**: 自动检测和处理硬件故障

### 📊 数据处理
- **实时滤波**: 多种数字滤波器选择
- **信号分析**: FFT频谱分析、统计分析
- **数据压缩**: 高效的数据存储格式
- **导出功能**: 支持CSV、HDF5、MATLAB格式

### 🔒 安全特性
- **权限管理**: 多级用户权限控制
- **操作日志**: 完整的操作记录和审计
- **紧急停止**: 硬件和软件双重安全保护
- **数据备份**: 自动配置和数据备份

---

## 🧪 开发指南

### 🏗️ 架构设计

系统采用模块化设计，主要组件包括：

1. **前端模块** (`fc/frontend/`)
   - GUI界面和用户交互
   - 数据可视化和图表显示
   - 主题系统和响应式布局

2. **后端模块** (`fc/backend/`)
   - 网络通信和协议处理
   - 数据采集和信号处理
   - 设备管理和状态监控

3. **核心模块** (`fc/`)
   - 配置管理和存档系统
   - 通信标准和协议定义
   - 工具函数和公共组件

### 🔧 扩展开发

#### 添加新的控制算法

```python
# 在 fc/backend/control/ 中添加新的控制器
class CustomController:
    def __init__(self, parameters):
        self.parameters = parameters
    
    def compute_output(self, setpoint, feedback):
        # 实现控制算法
        return control_output
```

#### 添加新的GUI组件

```python
# 在 fc/frontend/gui/widgets/ 中添加新组件
class CustomWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.setup_ui()
    
    def setup_ui(self):
        # 实现UI布局
        pass
```

#### 添加新的通信协议

```python
# 在 fc/backend/protocols/ 中添加新协议
class CustomProtocol:
    def encode_message(self, data):
        # 实现消息编码
        return encoded_data
    
    def decode_message(self, raw_data):
        # 实现消息解码
        return decoded_data
```

### 🧪 测试框架

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python fc/tests.py

# 运行性能测试
python system_stability_test.py
```

---

## 📚 API参考

### 主要类和方法

#### FCCommunicator
```python
class FCCommunicator:
    def connect_to_slaves(self, ip_list):
        """连接到指定IP的从机列表"""
        
    def send_control_vector(self, duty_cycles):
        """发送控制向量到所有从机"""
        
    def get_feedback_data(self):
        """获取从机反馈数据"""
```

#### ControlWidget
```python
class ControlWidget:
    def update_display(self, data):
        """更新控制面板显示"""
        
    def set_duty_cycle(self, slave_id, duty_cycle):
        """设置指定从机的占空比"""
```

#### ExternalController
```python
class ExternalController:
    def start_listener(self, port=25001):
        """启动外部控制监听器"""
        
    def process_command(self, command):
        """处理外部控制命令"""
```

---

## 🐛 故障排除

### 常见问题

#### 1. 从机连接失败
```
问题: 无法发现或连接从机
解决: 
- 检查网络连接和IP配置
- 确认从机固件已正确烧录
- 检查防火墙设置
- 验证端口25000是否被占用
```

#### 2. 控制响应延迟
```
问题: 控制命令响应缓慢
解决:
- 检查网络延迟和带宽
- 减少控制更新频率
- 优化数据包大小
- 检查系统资源使用情况
```

#### 3. GUI界面卡顿
```
问题: 界面响应缓慢或卡顿
解决:
- 降低数据更新频率
- 关闭不必要的监控功能
- 检查内存使用情况
- 更新显卡驱动
```

#### 4. 数据记录异常
```
问题: 数据记录不完整或格式错误
解决:
- 检查磁盘空间
- 验证文件权限
- 检查数据格式配置
- 重启数据记录服务
```

### 🔍 调试工具

```bash
# 启用详细日志
python main.py --debug --verbose

# 网络诊断
python fc/auxiliary/network_diagnostic.py

# 性能监控
python monitoring_demo.py

# 信号质量测试
python signal_demo.py
```

---

## 📈 性能优化

### 系统性能指标

- **控制延迟**: < 10ms (典型值 2-5ms)
- **数据更新率**: 100Hz (可配置)
- **网络带宽**: < 1Mbps (100个从机)
- **内存使用**: < 500MB (主控端)
- **CPU使用**: < 30% (正常负载)

### 优化建议

1. **网络优化**
   - 使用千兆以太网
   - 配置专用网络段
   - 启用网络QoS

2. **系统优化**
   - 使用SSD存储
   - 增加系统内存
   - 关闭不必要的后台程序

3. **软件优化**
   - 调整数据更新频率
   - 优化GUI渲染设置
   - 使用硬件加速

---

## 🤝 贡献指南

### 开发流程

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8 Python代码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 编写单元测试覆盖新功能

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式调整
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

---

## 📄 许可证

本项目由 zhaoyangmu 和 chendashuai 开发，仅供学术研究使用。

---

## 📞 联系方式

- **项目主页**: [GitHub仓库](https://github.com/mzymuzhaoyang/fan-club)
- **技术支持**: 请通过GitHub Issues提交问题
- **学术合作**: 请联系 zhaoyangmu 和 chendashuai
- **联系邮箱**: mzymuzhaoyang@gmail.com

---

## 🙏 致谢

感谢所有贡献者，以及Mbed OS和Python开源社区的支持。

---

<div align="center">

**Fan Club MkIV** - *精确控制，无限可能*

![Powered by](https://img.shields.io/badge/Powered%20by-zhaoyangmu%20%26%20chendashuai-orange?style=for-the-badge)

</div>













































