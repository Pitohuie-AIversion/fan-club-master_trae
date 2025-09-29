# 数据标准化功能测试报告

生成时间：2025-09-17 16:12:49

## 测试结果概览

- 单元测试：✗ 失败

## 测试覆盖范围

### 单元测试
- 网络诊断数据标准化功能
- DC数据标准化转换功能
- 断开从机连接异常处理逻辑
- 数据验证和格式检查函数
- 可扩展标准化框架
- 集成测试

## 测试文件

- `tests/test_standards.py` - 单元测试
- `tests/test_standards_performance.py` - 性能测试
- `run_tests.py` - 测试运行脚本

## 使用说明

```bash
# 运行所有测试
python run_tests.py --all

# 仅运行单元测试
python run_tests.py --unit

# 仅运行性能测试
python run_tests.py --performance

# 运行快速测试
python run_tests.py --quick
```
