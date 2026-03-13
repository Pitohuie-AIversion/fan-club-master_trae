import os
import re
import sys
import json
import ast
from collections import defaultdict, Counter

SEVERITY_ORDER = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}

def read_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except Exception:
        return []

def snippet(lines, lineno, context=2):
    start = max(1, lineno - context)
    end = min(len(lines), lineno + context)
    return "\n".join(str(i).rjust(5) + ": " + lines[i-1].rstrip("\n") for i in range(start, end+1))

def add_issue(issues, path, severity, lineno, message, code):
    issues[path].append({
        "severity": severity,
        "line": lineno,
        "message": message,
        "code": code
    })

def estimate_complexity(node):
    count = 0
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.And, ast.Or, ast.BoolOp)):
            count += 1
    return count

def check_python(path, issues):
    lines = read_lines(path)
    text = "".join(lines)
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        add_issue(issues, path, "Critical", getattr(e, "lineno", 1) or 1, "语法错误", "")
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            comp = estimate_complexity(node)
            if comp >= 20:
                add_issue(issues, path, "High", node.lineno, f"函数复杂度过高: {comp}", node.name)
            end = getattr(node, "end_lineno", node.lineno)
            size = end - node.lineno + 1
            if size >= 200:
                add_issue(issues, path, "Medium", node.lineno, f"函数长度过大: {size} 行", node.name)
            if not re.match(r"^[a-z_][a-z0-9_]*$", node.name):
                add_issue(issues, path, "Low", node.lineno, "函数命名不符合snake_case", node.name)
        if isinstance(node, ast.ClassDef):
            if not re.match(r"^[A-Z][A-Za-z0-9]*$", node.name):
                add_issue(issues, path, "Low", node.lineno, "类命名不符合PascalCase", node.name)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                add_issue(issues, path, "High", node.lineno, f"使用危险函数: {node.func.id}", node.func.id)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
                for kw in node.keywords or []:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        add_issue(issues, path, "High", node.lineno, "subprocess以shell=True运行存在注入风险", "subprocess.run")
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                add_issue(issues, path, "Medium", node.lineno, "裸except可能掩盖错误", "except:")
            elif isinstance(node.type, ast.Name) and node.type.id in {"Exception"}:
                add_issue(issues, path, "Low", node.lineno, "广泛捕获Exception可能掩盖错误", "except Exception")

    token_lines = [re.sub(r"\s+", " ", l.strip()) for l in lines if l.strip()]
    counts = Counter(token_lines)
    for i, l in enumerate(lines, 1):
        norm = re.sub(r"\s+", " ", l.strip())
        if norm and counts[norm] >= 10:
            add_issue(issues, path, "Low", i, "存在大量重复代码片段", norm[:80])
            break

    for i, l in enumerate(lines, 1):
        if re.search(r"threading\.|multiprocessing\.", l) and not re.search(r"Lock|RLock|Semaphore|Event|Queue", "".join(lines[max(1, i-20)-1:i+20])):
            add_issue(issues, path, "Medium", i, "使用并发但附近未发现同步原语", l.strip()[:80])

def cpp_find_decl_without_init(line):
    return bool(re.search(r"\b([A-Za-z_][A-Za-z0-9_:<>]*)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:;|,)", line)) and not ("=" in line or "(" in line or ")" in line)

def check_cpp(path, issues):
    lines = read_lines(path)
    dangerous = {"strcpy": "使用不安全的strcpy可能导致缓冲区溢出", "strcat": "使用不安全的strcat可能导致缓冲区溢出", "sprintf": "使用不安全的sprintf可能导致缓冲区溢出", "gets": "使用不安全的gets导致溢出"}
    for i, l in enumerate(lines, 1):
        for fn, msg in dangerous.items():
            if fn in l:
                add_issue(issues, path, "High", i, msg, l.strip())
        if re.search(r"while\s*\(\s*true\s*\)\s*\{", l):
            add_issue(issues, path, "Medium", i, "无限循环可能导致CPU占用过高，需合理休眠", l.strip())
        if cpp_find_decl_without_init(l):
            add_issue(issues, path, "Low", i, "变量声明未初始化可能导致未定义行为", l.strip())
        if re.search(r"Thread\s*\(" , l) or "Thread" in l:
            window = "".join(lines[max(1, i-30)-1:i+30])
            if not re.search(r"Mutex|Semaphore|Atomic|lock|unlock", window):
                add_issue(issues, path, "Medium", i, "线程使用附近未发现同步保护，可能存在竞争", l.strip())
        if re.search(r"new\s+", l) and not re.search(r"delete\s+", "".join(lines[i-1:i+200])):
            add_issue(issues, path, "Low", i, "new后未发现对应delete，可能存在内存泄漏", l.strip())

    text = "".join(lines)
    m = re.search(r"char\s+version\s*\[\s*(\d+)\s*\]\s*;", text)
    if m:
        size = int(m.group(1))
        for i, l in enumerate(lines, 1):
            if "strcpy" in l and "version" in l:
                sev = "High" if size < 64 else "Medium"
                add_issue(issues, path, sev, i, f"将外部字符串拷贝到尺寸为{size}的version，存在溢出风险，建议使用strncpy并校验长度", l.strip())

def analyze(paths):
    issues = defaultdict(list)
    for p in paths:
        if p.endswith(".py") or p.lower().endswith(".py"):
            check_python(p, issues)
        elif p.lower().endswith(".cpp") or p.lower().endswith(".h") or p.lower().endswith(".hpp"):
            check_cpp(p, issues)
    return issues

def sort_issues(issues):
    def key(i):
        return -SEVERITY_ORDER.get(i["severity"], 0), i["line"]
    return {p: sorted(lst, key=key) for p, lst in issues.items()}

def format_report(issues):
    out = []
    for path, lst in issues.items():
        lines = read_lines(path)
        out.append({"path": path, "findings": [{
            "severity": i["severity"],
            "line": i["line"],
            "message": i["message"],
            "snippet": snippet(lines, i["line"])
        } for i in lst]})
    return out

def main():
    paths = [p for p in sys.argv[1:] if os.path.exists(p)]
    issues = analyze(paths)
    issues = sort_issues(issues)
    report = format_report(issues)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
