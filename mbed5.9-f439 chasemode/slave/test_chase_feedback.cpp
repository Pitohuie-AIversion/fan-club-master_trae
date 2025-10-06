/**
 * @file test_chase_feedback.cpp
 * @brief 测试chase feedback控制功能的实现
 * @author Assistant
 * @date 2025
 */

#include "mbed.h"
#include "Fan.h"
#include "Processor.h"

// 测试用的串口
Serial pc(USBTX, USBRX);

/**
 * @brief 测试Fan类的PI控制器功能
 */
void test_fan_pi_controller() {
    pc.printf("\n=== 测试Fan PI控制器 ===\n");
    
    // 创建一个Fan对象进行测试
    Fan testFan;
    
    // 配置风扇（使用默认引脚）
    testFan.configure(0, 0);
    
    // 测试设置PI增益
    bool result = testFan.setPIGains(0.5f, 0.1f);
    pc.printf("设置PI增益 (kp=0.5, ki=0.1): %s\n", result ? "成功" : "失败");
    
    // 测试设置目标转速
    testFan.setTarget(1500);
    pc.printf("设置目标转速 1500 RPM: %s\n", testFan.isChasing() ? "追踪模式开启" : "追踪模式关闭");
    pc.printf("当前目标转速: %d RPM\n", testFan.getTarget());
    
    // 模拟几次PI控制更新
    pc.printf("\n模拟PI控制更新:\n");
    for (int i = 0; i < 5; i++) {
        testFan.updateChase(50); // 使用50 RPM的容差
        wait_ms(100);
        pc.printf("第%d次更新 - 当前转速: %d RPM, 占空比: %.2f%%\n", 
                 i+1, testFan.read(), testFan.getDC() * 100.0f);
    }
    
    // 停止追踪
    testFan.setTarget(0);
    pc.printf("停止追踪: %s\n", testFan.isChasing() ? "仍在追踪" : "已停止追踪");
}

/**
 * @brief 测试Processor类的CHASE和PISET命令处理
 */
void test_processor_commands() {
    pc.printf("\n=== 测试Processor命令处理 ===\n");
    
    // 创建Processor对象
    Processor processor;
    
    // 配置处理器（使用默认参数）
    processor.configure(SINGLE, 2, 1000, 50);
    
    pc.printf("处理器配置完成\n");
    
    // 测试CHASE命令
    pc.printf("\n测试CHASE命令:\n");
    char chase_cmd[] = "CHASE 0 1200";
    bool chase_result = processor.process(chase_cmd);
    pc.printf("CHASE命令 '%s': %s\n", chase_cmd, chase_result ? "成功" : "失败");
    
    // 测试PISET命令
    pc.printf("\n测试PISET命令:\n");
    char piset_cmd[] = "PISET 0 0.8 0.2";
    bool piset_result = processor.process(piset_cmd);
    pc.printf("PISET命令 '%s': %s\n", piset_cmd, piset_result ? "成功" : "失败");
    
    // 测试无效命令
    pc.printf("\n测试无效命令:\n");
    char invalid_cmd[] = "CHASE 99 1000";
    bool invalid_result = processor.process(invalid_cmd);
    pc.printf("无效命令 '%s': %s\n", invalid_cmd, invalid_result ? "成功" : "失败");
}

/**
 * @brief 主测试函数
 */
int main() {
    pc.baud(115200);
    pc.printf("\n\n=== Chase Feedback 控制测试开始 ===\n");
    
    // 等待系统稳定
    wait_ms(1000);
    
    try {
        // 测试Fan类PI控制器
        test_fan_pi_controller();
        
        wait_ms(2000);
        
        // 测试Processor命令处理
        test_processor_commands();
        
        pc.printf("\n=== 所有测试完成 ===\n");
        
    } catch (...) {
        pc.printf("\n!!! 测试过程中发生异常 !!!\n");
    }
    
    // 保持程序运行
    while (true) {
        wait_ms(1000);
        pc.printf(".");
    }
    
    return 0;
}