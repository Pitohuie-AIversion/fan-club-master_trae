#!/usr/bin/python3
################################################################################
## 系统稳定性验证测试脚本
## 用于验证底层架构的稳定性和可靠性
################################################################################

import time
import threading
import psutil
import gc
import sys
import os
import queue
from typing import Dict, List, Any
from dataclasses import dataclass

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fc.backend.signal_acquisition import (
    SignalAcquisitionEngine, 
    SimulatedHardware, 
    AcquisitionConfig,
    ChannelConfig,
    SampleData
)
from fc.signal_processing_system import SignalProcessingSystem
from fc import printer as pt

@dataclass
class StabilityTestResult:
    """稳定性测试结果"""
    test_name: str
    duration: float
    success: bool
    error_count: int
    performance_metrics: Dict[str, Any]
    memory_usage: Dict[str, float]
    cpu_usage: float
    details: str = ""

class SystemStabilityTester:
    """系统稳定性测试器"""
    
    def __init__(self):
        self.results: List[StabilityTestResult] = []
        self.pqueue = queue.Queue()  # 使用Queue而不是list
        self.test_duration = 30  # 每个测试持续30秒
        
    def run_all_tests(self) -> List[StabilityTestResult]:
        """运行所有稳定性测试"""
        print("\n" + "="*60)
        print("系统稳定性验证测试开始")
        print("="*60)
        
        # 1. 信号采集系统基础功能测试
        self.test_signal_acquisition_basic()
        
        # 2. 数据处理和传输可靠性测试
        self.test_data_processing_reliability()
        
        # 3. 多线程架构稳定性测试
        self.test_multithreading_stability()
        
        # 4. 系统资源使用测试
        self.test_system_resource_usage()
        
        # 5. 异常处理和错误恢复测试
        self.test_exception_handling()
        
        # 6. 长时间运行稳定性测试
        self.test_long_running_stability()
        
        return self.results
    
    def test_signal_acquisition_basic(self):
        """测试信号采集系统基础功能"""
        print("\n1. 信号采集系统基础功能测试...")
        start_time = time.time()
        error_count = 0
        
        try:
            # 创建信号采集引擎
            hardware = SimulatedHardware()
            engine = SignalAcquisitionEngine(self.pqueue, hardware)
            
            # 配置采集参数
            config = AcquisitionConfig(
                sampling_rate=1000.0,
                channels=[0, 1, 2],
                buffer_size=1024
            )
            
            # 测试配置
            config_success = engine.configure(config)
            if not config_success:
                error_count += 1
                
            # 测试启动和停止
            start_success = engine.start_acquisition()
            if not start_success:
                error_count += 1
                
            # 运行一段时间收集数据
            time.sleep(5)
            
            # 检查数据采集
            data = engine.get_data(timeout=1.0)
            if not data:
                error_count += 1
                
            # 检查统计信息
            stats = engine.get_statistics()
            if stats['samples_acquired'] == 0:
                error_count += 1
                
            # 停止采集
            stop_success = engine.stop_acquisition()
            if not stop_success:
                error_count += 1
                
            duration = time.time() - start_time
            
            # 记录结果
            result = StabilityTestResult(
                test_name="信号采集基础功能",
                duration=duration,
                success=error_count == 0,
                error_count=error_count,
                performance_metrics={
                    "samples_acquired": stats['samples_acquired'],
                    "acquisition_rate": stats['samples_acquired'] / duration,
                    "error_rate": stats['errors'] / max(1, stats['samples_acquired'])
                },
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"采集了 {stats['samples_acquired']} 个样本，错误 {stats['errors']} 次"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 错误数: {error_count}, 采集样本: {stats['samples_acquired']}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="信号采集基础功能",
                duration=duration,
                success=False,
                error_count=error_count + 1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def test_data_processing_reliability(self):
        """测试数据处理和传输可靠性"""
        print("\n2. 数据处理和传输可靠性测试...")
        start_time = time.time()
        error_count = 0
        processed_samples = 0
        
        try:
            # 跳过信号处理系统创建，直接测试数据处理
            # processing_system = SignalProcessingSystem(self.pqueue)
            
            # 创建数据回调函数
            def data_callback(samples: List[SampleData]):
                nonlocal processed_samples, error_count
                try:
                    # 模拟数据处理
                    for sample in samples:
                        if sample.value is None or sample.timestamp <= 0:
                            error_count += 1
                        processed_samples += 1
                except Exception:
                    error_count += 1
            
            # 创建采集引擎并添加回调
            hardware = SimulatedHardware()
            engine = SignalAcquisitionEngine(self.pqueue, hardware)
            engine.add_data_callback(data_callback)
            
            config = AcquisitionConfig(sampling_rate=500.0, channels=[0, 1])
            engine.configure(config)
            engine.start_acquisition()
            
            # 运行测试
            time.sleep(10)
            
            engine.stop_acquisition()
            
            duration = time.time() - start_time
            
            result = StabilityTestResult(
                test_name="数据处理和传输可靠性",
                duration=duration,
                success=error_count < processed_samples * 0.01,  # 错误率小于1%
                error_count=error_count,
                performance_metrics={
                    "processed_samples": processed_samples,
                    "processing_rate": processed_samples / duration,
                    "error_rate": error_count / max(1, processed_samples)
                },
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"处理了 {processed_samples} 个样本，错误 {error_count} 次"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 处理样本: {processed_samples}, 错误率: {error_count/max(1,processed_samples)*100:.2f}%")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="数据处理和传输可靠性",
                duration=duration,
                success=False,
                error_count=error_count + 1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def test_multithreading_stability(self):
        """测试多线程架构稳定性"""
        print("\n3. 多线程架构稳定性测试...")
        start_time = time.time()
        error_count = 0
        
        try:
            # 创建多个采集引擎模拟多线程环境
            engines = []
            for i in range(3):
                hardware = SimulatedHardware()
                engine = SignalAcquisitionEngine(self.pqueue, hardware)
                config = AcquisitionConfig(
                    sampling_rate=200.0 + i * 100,
                    channels=[i],
                    buffer_size=512
                )
                engine.configure(config)
                engines.append(engine)
            
            # 启动所有引擎
            for engine in engines:
                if not engine.start_acquisition():
                    error_count += 1
            
            # 运行一段时间
            time.sleep(8)
            
            # 检查所有引擎状态
            total_samples = 0
            for engine in engines:
                stats = engine.get_statistics()
                total_samples += stats['samples_acquired']
                if stats['errors'] > 0:
                    error_count += stats['errors']
            
            # 停止所有引擎
            for engine in engines:
                if not engine.stop_acquisition():
                    error_count += 1
            
            duration = time.time() - start_time
            
            result = StabilityTestResult(
                test_name="多线程架构稳定性",
                duration=duration,
                success=error_count == 0,
                error_count=error_count,
                performance_metrics={
                    "total_samples": total_samples,
                    "engines_count": len(engines),
                    "avg_samples_per_engine": total_samples / len(engines)
                },
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"运行了 {len(engines)} 个采集引擎，总采集 {total_samples} 个样本"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 引擎数: {len(engines)}, 总样本: {total_samples}, 错误: {error_count}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="多线程架构稳定性",
                duration=duration,
                success=False,
                error_count=error_count + 1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def test_system_resource_usage(self):
        """测试系统资源使用情况"""
        print("\n4. 系统资源使用测试...")
        start_time = time.time()
        
        # 记录初始资源使用
        initial_memory = self._get_memory_usage()
        cpu_samples = []
        memory_samples = []
        
        try:
            # 创建高负载测试
            hardware = SimulatedHardware()
            engine = SignalAcquisitionEngine(self.pqueue, hardware)
            config = AcquisitionConfig(
                sampling_rate=2000.0,  # 高采样率
                channels=[0, 1, 2, 3],  # 多通道
                buffer_size=2048
            )
            
            engine.configure(config)
            engine.start_acquisition()
            
            # 监控资源使用
            for _ in range(20):  # 监控20秒
                time.sleep(1)
                cpu_samples.append(psutil.cpu_percent())
                memory_samples.append(self._get_memory_usage())
            
            engine.stop_acquisition()
            
            # 分析资源使用
            avg_cpu = sum(cpu_samples) / len(cpu_samples)
            max_cpu = max(cpu_samples)
            final_memory = self._get_memory_usage()
            memory_increase = final_memory['rss'] - initial_memory['rss']
            
            duration = time.time() - start_time
            
            # 判断是否通过测试（CPU < 80%, 内存增长 < 100MB）
            success = max_cpu < 80.0 and memory_increase < 100 * 1024 * 1024
            
            result = StabilityTestResult(
                test_name="系统资源使用",
                duration=duration,
                success=success,
                error_count=0 if success else 1,
                performance_metrics={
                    "avg_cpu_usage": avg_cpu,
                    "max_cpu_usage": max_cpu,
                    "memory_increase_mb": memory_increase / (1024 * 1024),
                    "final_memory_mb": final_memory['rss'] / (1024 * 1024)
                },
                memory_usage=final_memory,
                cpu_usage=avg_cpu,
                details=f"平均CPU: {avg_cpu:.1f}%, 最大CPU: {max_cpu:.1f}%, 内存增长: {memory_increase/(1024*1024):.1f}MB"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 平均CPU: {avg_cpu:.1f}%, 内存增长: {memory_increase/(1024*1024):.1f}MB")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="系统资源使用",
                duration=duration,
                success=False,
                error_count=1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def test_exception_handling(self):
        """测试异常处理和错误恢复"""
        print("\n5. 异常处理和错误恢复测试...")
        start_time = time.time()
        recovery_count = 0
        
        try:
            # 创建会产生异常的回调函数
            def faulty_callback(samples):
                if len(samples) > 5:  # 模拟偶发异常
                    raise ValueError("模拟异常")
            
            hardware = SimulatedHardware()
            engine = SignalAcquisitionEngine(self.pqueue, hardware)
            engine.add_data_callback(faulty_callback)
            
            config = AcquisitionConfig(sampling_rate=100.0, channels=[0])
            engine.configure(config)
            engine.start_acquisition()
            
            # 运行并观察系统是否能继续工作
            time.sleep(10)
            
            stats = engine.get_statistics()
            engine.stop_acquisition()
            
            # 检查系统是否仍在正常采集数据（说明异常被正确处理）
            success = stats['samples_acquired'] > 0
            if success:
                recovery_count = 1
            
            duration = time.time() - start_time
            
            result = StabilityTestResult(
                test_name="异常处理和错误恢复",
                duration=duration,
                success=success,
                error_count=0 if success else 1,
                performance_metrics={
                    "samples_after_exceptions": stats['samples_acquired'],
                    "recovery_success": recovery_count
                },
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"异常处理后仍采集了 {stats['samples_acquired']} 个样本"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 异常后采集样本: {stats['samples_acquired']}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="异常处理和错误恢复",
                duration=duration,
                success=False,
                error_count=1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def test_long_running_stability(self):
        """测试长时间运行稳定性"""
        print("\n6. 长时间运行稳定性测试...")
        start_time = time.time()
        
        try:
            hardware = SimulatedHardware()
            engine = SignalAcquisitionEngine(self.pqueue, hardware)
            config = AcquisitionConfig(sampling_rate=500.0, channels=[0, 1])
            
            engine.configure(config)
            engine.start_acquisition()
            
            # 运行较长时间（60秒）
            test_duration = 60
            for i in range(test_duration):
                time.sleep(1)
                if i % 10 == 0:  # 每10秒检查一次
                    stats = engine.get_statistics()
                    print(f"     {i}s: 采集 {stats['samples_acquired']} 样本, 错误 {stats['errors']} 次")
            
            final_stats = engine.get_statistics()
            engine.stop_acquisition()
            
            duration = time.time() - start_time
            
            # 计算稳定性指标
            expected_samples = config.sampling_rate * len(config.channels) * test_duration * 0.9  # 允许10%误差
            success = final_stats['samples_acquired'] >= expected_samples and final_stats['errors'] < 100
            
            result = StabilityTestResult(
                test_name="长时间运行稳定性",
                duration=duration,
                success=success,
                error_count=final_stats['errors'],
                performance_metrics={
                    "total_samples": final_stats['samples_acquired'],
                    "expected_samples": expected_samples,
                    "sample_rate_accuracy": final_stats['samples_acquired'] / expected_samples,
                    "total_errors": final_stats['errors']
                },
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"运行 {test_duration}s，采集 {final_stats['samples_acquired']} 样本，错误 {final_stats['errors']} 次"
            )
            
            self.results.append(result)
            print(f"   ✓ 完成 - 总样本: {final_stats['samples_acquired']}, 总错误: {final_stats['errors']}")
            
        except Exception as e:
            duration = time.time() - start_time
            result = StabilityTestResult(
                test_name="长时间运行稳定性",
                duration=duration,
                success=False,
                error_count=1,
                performance_metrics={},
                memory_usage=self._get_memory_usage(),
                cpu_usage=psutil.cpu_percent(),
                details=f"测试异常: {str(e)}"
            )
            self.results.append(result)
            print(f"   ✗ 失败 - 异常: {str(e)}")
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        process = psutil.Process()
        memory_info = process.memory_info()
        return {
            'rss': memory_info.rss,  # 物理内存
            'vms': memory_info.vms,  # 虚拟内存
            'percent': process.memory_percent()  # 内存使用百分比
        }
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("\n" + "="*60)
        report.append("系统稳定性验证测试报告")
        report.append("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        
        report.append(f"\n总测试数: {total_tests}")
        report.append(f"通过测试: {passed_tests}")
        report.append(f"失败测试: {total_tests - passed_tests}")
        report.append(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        report.append("\n详细结果:")
        report.append("-" * 60)
        
        for result in self.results:
            status = "✓ 通过" if result.success else "✗ 失败"
            report.append(f"\n{result.test_name}: {status}")
            report.append(f"  持续时间: {result.duration:.2f}s")
            report.append(f"  错误数: {result.error_count}")
            report.append(f"  CPU使用: {result.cpu_usage:.1f}%")
            report.append(f"  内存使用: {result.memory_usage['percent']:.1f}%")
            report.append(f"  详情: {result.details}")
            
            if result.performance_metrics:
                report.append("  性能指标:")
                for key, value in result.performance_metrics.items():
                    if isinstance(value, float):
                        report.append(f"    {key}: {value:.2f}")
                    else:
                        report.append(f"    {key}: {value}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)

def main():
    """主函数"""
    tester = SystemStabilityTester()
    
    # 运行所有测试
    results = tester.run_all_tests()
    
    # 生成并显示报告
    report = tester.generate_report()
    print(report)
    
    # 保存报告到文件
    with open('system_stability_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存到: system_stability_report.txt")
    
    # 返回总体测试结果
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.success)
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！系统架构稳定可靠。")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要进一步检查。")
        return 1

if __name__ == "__main__":
    exit(main())