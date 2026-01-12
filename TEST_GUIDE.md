# StatsTracker 测试指南

完整的测试运行和调试指南。

## 🚀 快速开始

### 运行所有测试
```bash
# 在项目根目录运行
python -m pytest tests/ -v

# 预期输出：
# 55 passed ✅
```

### 运行特定模块的测试
```bash
# Email notifier 测试 (48 个)
python -m pytest tests/email_notifier/ -v

# Player database 测试 (7 个)
python -m pytest tests/player_database/ -v
```

## 📝 测试命令详解

### 基础命令

| 命令 | 说明 |
|------|------|
| `pytest tests/` | 运行所有测试（简洁输出） |
| `pytest tests/ -v` | 详细模式（显示每个测试名称） |
| `pytest tests/ -vv` | 超详细模式（显示更多细节） |
| `pytest tests/ -q` | 安静模式（最少输出） |

### 选择性运行

```bash
# 运行特定文件
pytest tests/email_notifier/test_notifier.py -v

# 运行特定类的所有测试
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier -v

# 运行特定测试函数
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init -v

# 使用关键字匹配测试名称
pytest tests/ -k "email" -v          # 运行名称包含 "email" 的测试
pytest tests/ -k "smtp" -v           # 运行名称包含 "smtp" 的测试
pytest tests/ -k "not slow" -v       # 运行不包含 "slow" 的测试
```

### 调试和输出

```bash
# 显示 print 输出
pytest tests/ -v -s

# 显示局部变量（调试失败的测试）
pytest tests/ -v -l

# 失败时进入调试器
pytest tests/ --pdb

# 第一个失败后停止
pytest tests/ -x

# 最多允许 N 个失败
pytest tests/ --maxfail=3
```

### 重新运行失败的测试

```bash
# 只运行上次失败的测试
pytest --lf

# 先运行上次失败的，再运行其他的
pytest --ff
```

### 测试覆盖率

```bash
# 生成覆盖率报告（需要先安装 pytest-cov）
pip install pytest-cov

# 查看 email_notifier 的覆盖率
pytest tests/email_notifier/ --cov=src/email_notifier --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest tests/ --cov=src --cov-report=html
# 然后打开 htmlcov/index.html 查看
```

## 🎯 Email Notifier 测试示例

### 场景 1：开发新功能前运行测试
确保现有功能正常：
```bash
pytest tests/email_notifier/ -v
```

### 场景 2：修改代码后快速验证
```bash
# 只运行相关测试
pytest tests/email_notifier/test_notifier.py -v

# 或者使用关键字
pytest tests/ -k "notifier" -v
```

### 场景 3：调试失败的测试
```bash
# 详细输出 + 显示 print + 显示局部变量
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_send_test_email_success -vv -s -l
```

### 场景 4：测试错误处理
```bash
# 运行所有错误处理相关的测试
pytest tests/ -k "error or exception" -v
```

## 📂 测试文件结构

```
tests/
├── email_notifier/              # Email 模块测试
│   ├── __init__.py
│   ├── test_notifier.py         # EmailNotifier 类测试 (22个)
│   ├── test_templates.py        # EmailTemplate 类测试 (26个)
│   └── README.md               # 详细测试文档
├── player_database/            # 数据库模块测试
│   ├── __init__.py
│   └── test_database.py        # PlayerDatabase 测试 (7个)
└── (未来会添加其他模块的测试)
```

## ✅ 测试最佳实践

### 1. 提交代码前运行测试
```bash
# 确保所有测试通过
pytest tests/ -v

# 检查你修改的模块
pytest tests/email_notifier/ -v
```

### 2. 编写新功能时的TDD流程
```bash
# 1. 先写测试（会失败）
# 2. 运行测试确认失败
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_new_feature -v

# 3. 实现功能
# 4. 再次运行测试直到通过
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_new_feature -v

# 5. 运行所有测试确保没有破坏其他功能
pytest tests/ -v
```

### 3. 修复 bug 的流程
```bash
# 1. 先写一个复现 bug 的测试（应该失败）
# 2. 修复 bug
# 3. 运行测试确认修复
pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_bug_fix -v

# 4. 运行相关的所有测试
pytest tests/email_notifier/ -v
```

## 🔍 理解测试输出

### 成功的测试
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init PASSED [  1%]
```
- `PASSED` = 测试通过 ✅
- `[  1%]` = 进度百分比

### 失败的测试
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init FAILED [ 1%]

================================== FAILURES ===================================
_________________________ TestEmailNotifier.test_init _________________________

    def test_init(self):
>       assert result == expected
E       AssertionError: assert 'actual' == 'expected'

tests/email_notifier/test_notifier.py:75: AssertionError
```
- 显示失败的位置
- 显示断言的实际值和期望值
- 帮助你快速定位问题

### 错误的测试
```
tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init ERROR [ 1%]
```
- `ERROR` = 测试在运行前就出错（通常是导入错误或 fixture 问题）

## 🛠️ 常见问题解决

### 问题 1：找不到模块
```bash
ModuleNotFoundError: No module named 'src'
```

**解决方案**：确保在项目根目录运行测试
```bash
cd /Users/zero_legend/StatsTracker
python -m pytest tests/ -v
```

### 问题 2：导入错误
```bash
ImportError: cannot import name 'EmailNotifier'
```

**解决方案**：检查 `__init__.py` 文件是否正确导出
```python
# src/email_notifier/__init__.py
from .notifier import EmailNotifier
from .templates import EmailTemplate
```

### 问题 3：测试依赖缺失
```bash
ModuleNotFoundError: No module named 'pytest'
```

**解决方案**：安装测试依赖
```bash
pip install pytest pytest-mock
# 或安装所有依赖
pip install -r requirements.txt
```

## 📊 当前测试状态

```
✅ Total: 55 tests
   ├── Email Notifier: 48 tests
   │   ├── test_notifier.py: 22 tests
   │   └── test_templates.py: 26 tests
   └── Player Database: 7 tests
       └── test_database.py: 7 tests

Status: All passing ✅
```

## 🎓 学习资源

### Pytest 文档
- 官方文档: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Parametrize: https://docs.pytest.org/en/stable/parametrize.html

### 项目特定测试文档
- Email Notifier 测试详情: [tests/email_notifier/README.md](tests/email_notifier/README.md)
- 测试覆盖哪些功能、如何使用 fixtures、测试策略等

## 💡 快捷命令别名

可以在 `.bashrc` 或 `.zshrc` 中添加别名：

```bash
# 测试别名
alias test-all="python -m pytest tests/ -v"
alias test-email="python -m pytest tests/email_notifier/ -v"
alias test-db="python -m pytest tests/player_database/ -v"
alias test-quick="python -m pytest tests/ -q"
alias test-failed="python -m pytest --lf -v"
```

然后就可以简单地运行：
```bash
test-all       # 运行所有测试
test-email     # 运行邮件测试
test-failed    # 重跑失败的测试
```

## 🚦 CI/CD 集成

### GitHub Actions 示例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## 📈 下一步

1. **安装覆盖率工具**
   ```bash
   pip install pytest-cov
   pytest tests/ --cov=src --cov-report=html
   ```

2. **为其他模块添加测试**
   - milestone_detector
   - gameday_checker
   - website_fetcher

3. **添加集成测试**
   - 测试模块之间的交互
   - 端到端测试

4. **性能测试**
   - 使用 `pytest-benchmark`
   - 测试大数据集处理

---

**快速参考卡片**

| 我想要... | 命令 |
|----------|------|
| 运行所有测试 | `pytest tests/ -v` |
| 运行邮件测试 | `pytest tests/email_notifier/ -v` |
| 运行单个测试 | `pytest tests/email_notifier/test_notifier.py::TestEmailNotifier::test_init -v` |
| 调试失败的测试 | `pytest tests/ -vv -s -l` |
| 只重跑失败的 | `pytest --lf` |
| 查看覆盖率 | `pytest tests/ --cov=src` |
| 按名称过滤 | `pytest tests/ -k "email" -v` |
| 第一个失败就停 | `pytest tests/ -x` |
