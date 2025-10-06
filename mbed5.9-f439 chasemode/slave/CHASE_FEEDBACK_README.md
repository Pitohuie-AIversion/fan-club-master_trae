# Chase Feedback 控制系统实现

## 概述

本项目为风扇控制系统实现了chase feedback（追踪反馈）控制功能，使用PI（比例-积分）控制器来精确控制风扇转速。

## 功能特性

### 1. PI控制器
- **比例控制 (P)**: 根据当前转速与目标转速的误差进行调节
- **积分控制 (I)**: 消除稳态误差，提高控制精度
- **可配置增益**: 支持动态调整kp和ki参数

### 2. 命令支持
- **CHASE命令**: `CHASE <fanID> <targetRPM>` - 设置风扇目标转速并启动追踪模式
- **PISET命令**: `PISET <fanID> <kp> <ki>` - 设置指定风扇的PI控制器参数

### 3. 实时反馈控制
- 在主处理循环中集成反馈控制
- 支持容差设置，避免过度调节
- 自动PI控制更新

## 代码结构

### Fan类扩展

#### 新增方法
```cpp
// 设置目标转速并启动/停止追踪模式
void setTarget(int targetRPM);

// 执行PI控制更新
void updateChase(int tolerance);

// 获取当前目标转速
int getTarget();

// 检查是否处于追踪模式
bool isChasing();

// 设置PI控制器增益
bool setPIGains(float kp, float ki);
```

#### 新增成员变量
```cpp
private:
    // PI控制器参数
    float kp;           // 比例增益
    float ki;           // 积分增益
    float integral;     // 积分累积值
    float lastError;    // 上次误差值
    bool chasing;       // 追踪模式标志
    Timer chaseTimer;   // PI控制定时器
```

### Processor类扩展

#### 新增命令处理
- **CHASE命令处理**: 解析fanID和targetRPM，调用对应风扇的setTarget方法
- **PISET命令处理**: 解析fanID、kp和ki参数，调用对应风扇的setPIGains方法

#### 反馈控制集成
在`_processorRoutine`的主循环中添加了反馈控制逻辑：
```cpp
// 如果风扇处于追踪模式，执行PI控制更新
if (fanPtr->isChasing()) {
    fanPtr->updateChase(chaserTolerance);
}
```

## 使用方法

### 1. 启动Chase模式
```
CHASE 0 1500    // 设置风扇0的目标转速为1500 RPM
```

### 2. 调整PI参数
```
PISET 0 0.8 0.2  // 设置风扇0的kp=0.8, ki=0.2
```

### 3. 停止Chase模式
```
CHASE 0 0       // 设置目标转速为0停止追踪
```

## PI控制器参数调节指南

### 比例增益 (kp)
- **作用**: 控制响应速度
- **建议范围**: 0.1 - 2.0
- **调节原则**: 
  - 增大kp可提高响应速度，但过大会导致振荡
  - 减小kp可提高稳定性，但响应变慢

### 积分增益 (ki)
- **作用**: 消除稳态误差
- **建议范围**: 0.01 - 0.5
- **调节原则**:
  - 增大ki可减少稳态误差，但过大会导致超调
  - 减小ki可提高稳定性，但可能存在稳态误差

### 推荐起始参数
- **一般风扇**: kp=0.5, ki=0.1
- **高速风扇**: kp=0.3, ki=0.05
- **低速风扇**: kp=0.8, ki=0.2

## 测试

### 编译测试程序
```bash
mbed compile -t GCC_ARM -m YOUR_TARGET --source . --source test_chase_feedback.cpp
```

### 测试内容
1. **Fan类PI控制器测试**
   - PI增益设置
   - 目标转速设置
   - PI控制更新模拟

2. **Processor命令处理测试**
   - CHASE命令解析和执行
   - PISET命令解析和执行
   - 无效命令处理

## 故障排除

### 常见问题

1. **风扇不响应CHASE命令**
   - 检查fanID是否在有效范围内
   - 确认风扇已正确配置
   - 检查目标转速是否合理

2. **PI控制振荡**
   - 减小kp值
   - 检查ki值是否过大
   - 确认容差设置合理

3. **稳态误差较大**
   - 适当增大ki值
   - 检查传感器读数准确性
   - 确认PI控制更新频率

### 调试信息
系统会输出详细的调试信息，包括：
- 命令接收确认
- 参数解析结果
- 错误信息和原因
- PI控制状态更新

## 技术规格

- **控制算法**: PI控制器
- **更新频率**: 与主处理循环同步
- **支持风扇数**: 取决于activeFans配置
- **转速范围**: 0-65535 RPM（理论值）
- **参数精度**: 浮点数（float）

## 版本信息

- **版本**: 1.0
- **开发日期**: 2025年1月
- **兼容性**: mbed OS 5.9+
- **硬件要求**: 支持PWM输出和转速检测的微控制器