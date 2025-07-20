# Fan Club MkIV 自动化调试和代码质量改进指南

## 概述

本指南提供了 Fan Club MkIV 项目的自动化调试、代码质量检查和持续改进的完整解决方案。

## 自动化调试策略

### 1. 静态代码分析

#### C++ 代码分析（从机和引导程序）

**工具推荐**：
- **Cppcheck**：开源 C++ 静态分析工具
- **Clang Static Analyzer**：LLVM 项目的静态分析器
- **PC-lint Plus**：商业级 C++ 代码检查工具

**自动化脚本示例**：
```bash
#!/bin/bash
# 静态分析脚本 - analyze_cpp.sh

echo "开始 C++ 代码静态分析..."

# 分析从机代码
echo "分析从机代码 (slave_upgraded)"
cppcheck --enable=all --xml --xml-version=2 slave_upgraded/ 2> slave_analysis.xml

# 分析引导程序代码
echo "分析引导程序代码 (slave_bootloader_upgraded)"
cppcheck --enable=all --xml --xml-version=2 slave_bootloader_upgraded/ 2> bootloader_analysis.xml

# 生成报告
echo "生成分析报告..."
cppcheck-htmlreport --file=slave_analysis.xml --report-dir=reports/slave_report
cppcheck-htmlreport --file=bootloader_analysis.xml --report-dir=reports/bootloader_report

echo "静态分析完成，报告保存在 reports/ 目录"
```

#### Python 代码分析（主控端）

**工具推荐**：
- **Pylint**：Python 代码质量检查
- **Flake8**：代码风格和错误检查
- **Bandit**：安全漏洞扫描
- **MyPy**：类型检查

**自动化脚本示例**：
```bash
#!/bin/bash
# Python 代码分析脚本 - analyze_python.sh

echo "开始 Python 代码分析..."

cd master/

# 代码质量检查
echo "运行 Pylint..."
pylint fc/ --output-format=json > ../reports/pylint_report.json

# 代码风格检查
echo "运行 Flake8..."
flake8 fc/ --output-file=../reports/flake8_report.txt

# 安全检查
echo "运行 Bandit..."
bandit -r fc/ -f json -o ../reports/bandit_report.json

# 类型检查
echo "运行 MyPy..."
mypy fc/ --json-report ../reports/mypy_report

echo "Python 代码分析完成"
```

### 2. 自动化单元测试

#### C++ 单元测试框架

**推荐框架**：Google Test (gtest)

**测试配置文件** (`test/CMakeLists.txt`)：
```cmake
cmake_minimum_required(VERSION 3.10)
project(FanClubTests)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 14)

# 查找 Google Test
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# 包含源代码目录
include_directories(../slave_upgraded)

# 创建测试可执行文件
add_executable(fan_tests
    test_fan.cpp
    test_communicator.cpp
    test_processor.cpp
    ../slave_upgraded/Fan.cpp
    ../slave_upgraded/Processor.cpp
)

# 链接测试库
target_link_libraries(fan_tests ${GTEST_LIBRARIES} pthread)

# 启用测试
enable_testing()
add_test(NAME FanClubUnitTests COMMAND fan_tests)
```

**示例测试文件** (`test/test_fan.cpp`)：
```cpp
#include <gtest/gtest.h>
#include "Fan.h"

class FanTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 测试前的设置
    }
    
    void TearDown() override {
        // 测试后的清理
    }
};

// 测试风扇初始化
TEST_F(FanTest, InitializationTest) {
    Fan fan;
    EXPECT_TRUE(fan.initialize());
    EXPECT_EQ(fan.getSpeed(), 0);
}

// 测试风扇速度设置
TEST_F(FanTest, SpeedControlTest) {
    Fan fan;
    fan.initialize();
    
    fan.setSpeed(50);
    EXPECT_EQ(fan.getSpeed(), 50);
    
    fan.setSpeed(100);
    EXPECT_EQ(fan.getSpeed(), 100);
    
    // 测试边界条件
    fan.setSpeed(-10);
    EXPECT_EQ(fan.getSpeed(), 0);
    
    fan.setSpeed(150);
    EXPECT_EQ(fan.getSpeed(), 100);
}

// 测试风扇停止功能
TEST_F(FanTest, StopTest) {
    Fan fan;
    fan.initialize();
    fan.setSpeed(75);
    
    fan.stop();
    EXPECT_EQ(fan.getSpeed(), 0);
}
```

#### Python 单元测试

**测试框架**：pytest + coverage

**测试配置文件** (`master/pytest.ini`)：
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=fc
    --cov-report=html:reports/coverage_html
    --cov-report=xml:reports/coverage.xml
    --cov-report=term-missing
```

**示例测试文件** (`master/tests/test_archive.py`)：
```python
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fc'))

from archive import FCArchive

class TestFCArchive:
    def setup_method(self):
        """每个测试方法前的设置"""
        self.archive = FCArchive()
    
    def test_initialization(self):
        """测试 FCArchive 初始化"""
        assert self.archive is not None
        assert hasattr(self.archive, 'profiles')
    
    def test_profile_validation(self):
        """测试配置文件验证"""
        # 测试有效配置
        valid_profile = {
            'version': '1.0',
            'platform': 'WINDOWS',
            'fan_mode': 'DOUBLE',
            'builtin_pinout': 'BASE'
        }
        assert self.archive.validate_profile(valid_profile)
        
        # 测试无效配置
        invalid_profile = {
            'version': '1.0',
            'platform': 'INVALID_PLATFORM',
            'fan_mode': 'DOUBLE'
        }
        assert not self.archive.validate_profile(invalid_profile)
    
    def test_profile_loading(self):
        """测试配置文件加载"""
        # 测试加载内置配置
        profile = self.archive.load_builtin_profile('BASE')
        assert profile is not None
        assert profile['builtin_pinout'] == 'BASE'
    
    @pytest.mark.parametrize("pinout,expected", [
        ('BASE', True),
        ('CAST', True),
        ('JPL', True),
        ('S117', True),
        ('INVALID', False)
    ])
    def test_pinout_validation(self, pinout, expected):
        """参数化测试引脚配置验证"""
        result = self.archive.is_valid_pinout(pinout)
        assert result == expected
```

### 3. 自动化集成测试

#### 硬件在环测试 (HIL)

**测试脚本示例** (`test/hil_test.py`)：
```python
#!/usr/bin/env python3
"""
硬件在环自动化测试脚本
"""

import time
import serial
import socket
import subprocess
import logging
from typing import List, Dict, Any

class HILTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        self.serial_conn = None
        self.network_conn = None
    
    def _setup_logging(self) -> logging.Logger:
        """设置日志记录"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('hil_test.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def setup_hardware(self) -> bool:
        """设置硬件连接"""
        try:
            # 连接串口
            self.serial_conn = serial.Serial(
                port=self.config['serial_port'],
                baudrate=self.config['baudrate'],
                timeout=5
            )
            
            # 设置网络连接
            self.network_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            self.logger.info("硬件连接设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"硬件设置失败: {e}")
            return False
    
    def flash_firmware(self, firmware_path: str) -> bool:
        """烧录固件"""
        try:
            cmd = [
                'st-flash', 'write', firmware_path, '0x8000000'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("固件烧录成功")
                time.sleep(2)  # 等待重启
                return True
            else:
                self.logger.error(f"固件烧录失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"烧录过程出错: {e}")
            return False
    
    def test_communication(self) -> bool:
        """测试通信功能"""
        try:
            # 发送测试命令
            test_cmd = b'\x01\x02\x03\x04'  # 示例命令
            self.network_conn.sendto(test_cmd, 
                (self.config['target_ip'], self.config['target_port']))
            
            # 等待响应
            self.network_conn.settimeout(5)
            response, addr = self.network_conn.recvfrom(1024)
            
            if response:
                self.logger.info(f"通信测试成功，收到响应: {response.hex()}")
                return True
            else:
                self.logger.error("通信测试失败，未收到响应")
                return False
                
        except Exception as e:
            self.logger.error(f"通信测试出错: {e}")
            return False
    
    def test_fan_control(self) -> bool:
        """测试风扇控制功能"""
        test_speeds = [0, 25, 50, 75, 100]
        
        for speed in test_speeds:
            try:
                # 发送风扇控制命令
                cmd = self._create_fan_command(speed)
                self.network_conn.sendto(cmd, 
                    (self.config['target_ip'], self.config['target_port']))
                
                time.sleep(1)  # 等待执行
                
                # 验证风扇状态
                if self._verify_fan_speed(speed):
                    self.logger.info(f"风扇速度 {speed}% 测试通过")
                else:
                    self.logger.error(f"风扇速度 {speed}% 测试失败")
                    return False
                    
            except Exception as e:
                self.logger.error(f"风扇控制测试出错: {e}")
                return False
        
        return True
    
    def _create_fan_command(self, speed: int) -> bytes:
        """创建风扇控制命令"""
        # 根据协议创建命令包
        # 这里需要根据实际协议实现
        return bytes([0x10, 0x01, speed, 0x00])
    
    def _verify_fan_speed(self, expected_speed: int) -> bool:
        """验证风扇速度"""
        # 这里可以通过传感器或反馈信号验证
        # 简化示例，实际需要根据硬件实现
        return True
    
    def run_full_test_suite(self) -> Dict[str, bool]:
        """运行完整测试套件"""
        results = {}
        
        self.logger.info("开始硬件在环测试")
        
        # 设置硬件
        results['hardware_setup'] = self.setup_hardware()
        if not results['hardware_setup']:
            return results
        
        # 烧录固件
        firmware_path = self.config.get('firmware_path')
        if firmware_path:
            results['firmware_flash'] = self.flash_firmware(firmware_path)
        
        # 通信测试
        results['communication'] = self.test_communication()
        
        # 风扇控制测试
        results['fan_control'] = self.test_fan_control()
        
        # 清理
        self.cleanup()
        
        self.logger.info(f"测试完成，结果: {results}")
        return results
    
    def cleanup(self):
        """清理资源"""
        if self.serial_conn:
            self.serial_conn.close()
        if self.network_conn:
            self.network_conn.close()

# 测试配置
if __name__ == "__main__":
    config = {
        'serial_port': 'COM3',
        'baudrate': 115200,
        'target_ip': '192.168.1.100',
        'target_port': 12345,
        'firmware_path': 'BUILD/NUCLEO_F429ZI/ARMC6/FCMkII_S.bin'
    }
    
    tester = HILTester(config)
    results = tester.run_full_test_suite()
    
    # 输出测试结果
    print("\n=== 测试结果 ===")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
```

### 4. 持续集成 (CI) 配置

#### GitHub Actions 配置

**配置文件** (`.github/workflows/ci.yml`)：
```yaml
name: Fan Club MkIV CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov pylint flake8 bandit mypy
        cd master && pip install -r requirements.txt
    
    - name: Run static analysis
      run: |
        cd master
        pylint fc/ --exit-zero
        flake8 fc/
        bandit -r fc/
        mypy fc/ --ignore-missing-imports
    
    - name: Run tests
      run: |
        cd master
        pytest tests/ --cov=fc --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./master/coverage.xml

  cpp-analysis:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install tools
      run: |
        sudo apt-get update
        sudo apt-get install -y cppcheck clang-tools
    
    - name: Run C++ static analysis
      run: |
        cppcheck --enable=all --xml --xml-version=2 slave_upgraded/ 2> cppcheck-result.xml
        clang-check slave_upgraded/*.cpp -- -I slave_upgraded/
    
    - name: Upload analysis results
      uses: actions/upload-artifact@v3
      with:
        name: cpp-analysis-results
        path: cppcheck-result.xml

  build-firmware:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup ARM toolchain
      run: |
        wget -q https://developer.arm.com/-/media/Files/downloads/gnu-rm/9-2020q2/gcc-arm-none-eabi-9-2020-q2-update-x86_64-linux.tar.bz2
        tar -xjf gcc-arm-none-eabi-9-2020-q2-update-x86_64-linux.tar.bz2
        echo "$PWD/gcc-arm-none-eabi-9-2020-q2-update/bin" >> $GITHUB_PATH
    
    - name: Install Mbed CLI
      run: |
        pip install mbed-cli
    
    - name: Build slave firmware
      run: |
        cd slave_upgraded
        mbed config -G GCC_ARM_PATH $PWD/../gcc-arm-none-eabi-9-2020-q2-update/bin
        mbed compile -t GCC_ARM -m NUCLEO_F429ZI
    
    - name: Build bootloader firmware
      run: |
        cd slave_bootloader_upgraded
        mbed compile -t GCC_ARM -m NUCLEO_F429ZI
    
    - name: Upload firmware artifacts
      uses: actions/upload-artifact@v3
      with:
        name: firmware-binaries
        path: |
          slave_upgraded/BUILD/NUCLEO_F429ZI/GCC_ARM/*.bin
          slave_bootloader_upgraded/BUILD/NUCLEO_F429ZI/GCC_ARM/*.bin
```

### 5. 代码质量监控

#### SonarQube 配置

**配置文件** (`sonar-project.properties`)：
```properties
# SonarQube 项目配置
sonar.projectKey=fan-club-mkiv
sonar.projectName=Fan Club MkIV
sonar.projectVersion=1.0

# 源代码路径
sonar.sources=master/fc,slave_upgraded,slave_bootloader_upgraded
sonar.tests=master/tests

# 语言设置
sonar.python.coverage.reportPaths=master/coverage.xml
sonar.cpp.file.suffixes=.cpp,.h

# 排除文件
sonar.exclusions=**/*.bin,**/*.hex,**/mbed-os/**,**/BUILD/**

# C++ 分析设置
sonar.cfamily.build-wrapper-output=bw-output
sonar.cfamily.cache.enabled=true
```

### 6. 自动化部署脚本

**部署脚本** (`scripts/auto_deploy.py`)：
```python
#!/usr/bin/env python3
"""
自动化部署脚本
"""

import os
import sys
import subprocess
import argparse
import logging
from pathlib import Path

class AutoDeployer:
    def __init__(self, config_file: str = None):
        self.logger = self._setup_logging()
        self.config = self._load_config(config_file)
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_config(self, config_file: str):
        # 加载部署配置
        default_config = {
            'build_dir': 'BUILD',
            'target_board': 'NUCLEO_F429ZI',
            'compiler': 'ARMC6',
            'flash_tool': 'st-flash'
        }
        return default_config
    
    def build_firmware(self, project_path: str) -> bool:
        """编译固件"""
        try:
            self.logger.info(f"开始编译 {project_path}")
            
            # 使用 Mbed Studio CLI 或 mbed compile
            cmd = [
                'mbed', 'compile',
                '-t', self.config['compiler'],
                '-m', self.config['target_board']
            ]
            
            result = subprocess.run(
                cmd, 
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("编译成功")
                return True
            else:
                self.logger.error(f"编译失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"编译过程出错: {e}")
            return False
    
    def flash_firmware(self, firmware_path: str) -> bool:
        """烧录固件"""
        try:
            self.logger.info(f"开始烧录 {firmware_path}")
            
            cmd = [
                self.config['flash_tool'],
                'write',
                firmware_path,
                '0x8000000'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("烧录成功")
                return True
            else:
                self.logger.error(f"烧录失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"烧录过程出错: {e}")
            return False
    
    def deploy_full_system(self) -> bool:
        """部署完整系统"""
        success = True
        
        # 编译从机固件
        if not self.build_firmware('slave_upgraded'):
            success = False
        
        # 编译引导程序
        if not self.build_firmware('slave_bootloader_upgraded'):
            success = False
        
        if success:
            # 烧录引导程序
            bootloader_bin = f"slave_bootloader_upgraded/{self.config['build_dir']}/{self.config['target_board']}/{self.config['compiler']}/main.bin"
            if os.path.exists(bootloader_bin):
                success &= self.flash_firmware(bootloader_bin)
            
            # 烧录主程序
            main_bin = f"slave_upgraded/{self.config['build_dir']}/{self.config['target_board']}/{self.config['compiler']}/FCMkII_S.bin"
            if os.path.exists(main_bin):
                success &= self.flash_firmware(main_bin)
        
        return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fan Club MkIV 自动部署工具')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--build-only', action='store_true', help='仅编译，不烧录')
    
    args = parser.parse_args()
    
    deployer = AutoDeployer(args.config)
    
    if args.build_only:
        success = (deployer.build_firmware('slave_upgraded') and 
                  deployer.build_firmware('slave_bootloader_upgraded'))
    else:
        success = deployer.deploy_full_system()
    
    sys.exit(0 if success else 1)
```

### 7. 性能监控和分析

#### 内存使用分析脚本

**脚本** (`scripts/memory_analysis.py`)：
```python
#!/usr/bin/env python3
"""
内存使用分析工具
"""

import subprocess
import re
import json
from typing import Dict, List

class MemoryAnalyzer:
    def __init__(self, elf_file: str):
        self.elf_file = elf_file
        self.arm_size = 'arm-none-eabi-size'
        self.arm_nm = 'arm-none-eabi-nm'
    
    def get_memory_usage(self) -> Dict[str, int]:
        """获取内存使用情况"""
        try:
            result = subprocess.run(
                [self.arm_size, '-A', self.elf_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"size 命令失败: {result.stderr}")
            
            memory_info = {}
            for line in result.stdout.split('\n'):
                if '.text' in line:
                    memory_info['flash_code'] = int(line.split()[1])
                elif '.data' in line:
                    memory_info['ram_data'] = int(line.split()[1])
                elif '.bss' in line:
                    memory_info['ram_bss'] = int(line.split()[1])
            
            return memory_info
            
        except Exception as e:
            print(f"内存分析失败: {e}")
            return {}
    
    def get_symbol_sizes(self) -> List[Dict[str, any]]:
        """获取符号大小信息"""
        try:
            result = subprocess.run(
                [self.arm_nm, '--print-size', '--size-sort', self.elf_file],
                capture_output=True,
                text=True
            )
            
            symbols = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        symbols.append({
                            'address': parts[0],
                            'size': int(parts[1], 16),
                            'type': parts[2],
                            'name': parts[3]
                        })
            
            return sorted(symbols, key=lambda x: x['size'], reverse=True)
            
        except Exception as e:
            print(f"符号分析失败: {e}")
            return []
    
    def generate_report(self) -> str:
        """生成内存分析报告"""
        memory_usage = self.get_memory_usage()
        symbols = self.get_symbol_sizes()[:20]  # 前20个最大符号
        
        report = "# 内存使用分析报告\n\n"
        
        # 内存使用概览
        report += "## 内存使用概览\n\n"
        if memory_usage:
            total_flash = memory_usage.get('flash_code', 0)
            total_ram = memory_usage.get('ram_data', 0) + memory_usage.get('ram_bss', 0)
            
            report += f"- Flash 使用: {total_flash} bytes\n"
            report += f"- RAM 使用: {total_ram} bytes\n"
            report += f"  - 初始化数据: {memory_usage.get('ram_data', 0)} bytes\n"
            report += f"  - 未初始化数据: {memory_usage.get('ram_bss', 0)} bytes\n\n"
        
        # 最大符号
        report += "## 最大符号 (前20个)\n\n"
        report += "| 符号名 | 大小 (bytes) | 类型 |\n"
        report += "|--------|-------------|------|\n"
        
        for symbol in symbols:
            report += f"| {symbol['name']} | {symbol['size']} | {symbol['type']} |\n"
        
        return report

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python memory_analysis.py <elf_file>")
        sys.exit(1)
    
    analyzer = MemoryAnalyzer(sys.argv[1])
    report = analyzer.generate_report()
    
    # 保存报告
    with open('memory_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("内存分析报告已保存到 memory_report.md")
    print(report)
```

## 使用指南

### 1. 快速开始

```bash
# 安装必要工具
pip install pytest pylint flake8 bandit mypy coverage
sudo apt-get install cppcheck clang-tools

# 运行 Python 代码分析
cd master
pylint fc/
flake8 fc/
bandit -r fc/

# 运行 C++ 代码分析
cppcheck --enable=all slave_upgraded/

# 运行单元测试
cd master
pytest tests/ --cov=fc
```

### 2. 集成到开发流程

1. **提交前检查**：在每次代码提交前运行静态分析
2. **持续集成**：配置 CI 流水线自动运行测试
3. **定期审查**：每周查看代码质量报告
4. **性能监控**：每次发布前进行内存和性能分析

### 3. 自定义配置

根据项目需求调整各工具的配置文件：
- `.pylintrc` - Pylint 配置
- `setup.cfg` - Flake8 配置
- `.bandit` - Bandit 配置
- `mypy.ini` - MyPy 配置

## 总结

这套自动化调试和质量保证系统提供了：

1. **全面的代码分析**：覆盖 Python 和 C++ 代码
2. **自动化测试**：单元测试和集成测试
3. **持续集成**：GitHub Actions 配置
4. **质量监控**：SonarQube 集成
5. **自动化部署**：一键编译和烧录
6. **性能分析**：内存使用和符号分析

通过这些工具和流程，可以显著提高代码质量，减少 bug，并确保系统的稳定性和可维护性。