#!/usr/bin/env python3
"""
DDD 产物表格标签与代码锚点校验脚本

校验白名单 md 文件中的表格：
1. 表头标签完整性：每张表要么恰好各 1 个 <anchor:ddd> / <anchor:code> / <anchor:desc>（全有），
   要么三个标签全无（附属属性表，如 domain-model.md 的行为归属表）
2. 锚点格式合规性：<anchor:code> 列的值符合三类格式之一：
   - 类名：PascalCase（如 WorkerConnector）
   - 类名.函数名：PascalCase.snake_case（如 WorkerConnector.start）
   - HTTP方法:/路径（如 POST:/connectors）

白名单文件：
  business-flow.md / invariants.md / contracts.md / domain-events.md / domain-model.md

豁免文件：
  context-map.md / technical-constraints.md / index.md

用法：
    python check_ddd_anchors.py --docs-root docs/ddd
    python check_ddd_anchors.py --single-file docs/ddd/features/connect-runtime/invariants.md
    python check_ddd_anchors.py --docs-root docs/ddd --quiet

输出：
    JSON 报告输出到 stdout，摘要信息到 stderr
    退出码：0 通过 / 1 有违规
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Windows 环境强制 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 白名单文件名（参与校验的 BC 级产物）
WHITELIST_FILES = {
    'business-flow.md',
    'invariants.md',
    'contracts.md',
    'domain-events.md',
    'domain-model.md',
}

# 豁免文件名（不参与校验）
EXEMPT_FILES = {
    'context-map.md',
    'technical-constraints.md',
    'index.md',
}

# 三类锚点格式正则
ANCHOR_PATTERNS = {
    '类名': re.compile(r'^[A-Z][A-Za-z0-9_]*$'),
    '类名.函数名': re.compile(r'^[A-Z][A-Za-z0-9_]*\.[a-z_][A-Za-z0-9_]*$'),
    'HTTP方法:/路径': re.compile(r'^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS):/[A-Za-z0-9/_{}.\-]*$'),
}

# 标签定义
LABELS = ['<anchor:ddd>', '<anchor:code>', '<anchor:desc>']


def strip_backticks(value: str) -> str:
    """去除单元格值中的反引号包围"""
    value = value.strip()
    if value.startswith('`') and value.endswith('`'):
        return value[1:-1]
    return value


def parse_table_header(header_line: str) -> List[Tuple[str, Optional[str]]]:
    """解析表头行，返回 [(列名, 标签或None), ...]

    列名中可能包含 <anchor:xxx> 标签，标签在列名末尾。
    """
    # 去除首尾 |
    line = header_line.strip()
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]

    columns = []
    for cell in line.split('|'):
        cell = cell.strip()
        # 检查是否包含标签
        label = None
        for tag in LABELS:
            if tag in cell:
                label = tag
                cell = cell.replace(tag, '').strip()
                break
        columns.append((cell, label))

    return columns


def is_separator_line(line: str) -> bool:
    """判断是否为表格分隔行（如 |---|---|）"""
    line = line.strip()
    if not line.startswith('|'):
        return False
    # 去除首尾 |
    if line.startswith('|'):
        line = line[1:]
    if line.endswith('|'):
        line = line[:-1]
    cells = line.split('|')
    for cell in cells:
        cell = cell.strip()
        if not re.match(r'^[-:]+$', cell):
            return False
    return True


def parse_table_rows(data_lines: List[str]) -> List[List[str]]:
    """解析表格数据行，返回 [[cell1, cell2, ...], ...]"""
    rows = []
    for line in data_lines:
        line = line.strip()
        if not line.startswith('|'):
            break
        # 去除首尾 |
        if line.startswith('|'):
            line = line[1:]
        if line.endswith('|'):
            line = line[:-1]
        rows.append([cell.strip() for cell in line.split('|')])
    return rows


def find_tables(content: str) -> List[Dict]:
    """从 markdown 内容中提取所有表格

    返回 [{"header": [(col_name, label), ...], "rows": [[cell, ...], ...], "line_number": N}, ...]
    """
    lines = content.split('\n')
    tables = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 寻找表格起始（| 开头的行）
        if line.startswith('|') and i + 1 < len(lines) and is_separator_line(lines[i + 1]):
            # 这是一个表格
            header = parse_table_header(line)
            # 收集数据行（从分隔行后开始）
            data_start = i + 2
            data_lines = []
            j = data_start
            while j < len(lines) and lines[j].strip().startswith('|'):
                data_lines.append(lines[j])
                j += 1
            rows = parse_table_rows(data_lines)
            tables.append({
                'header': header,
                'rows': rows,
                'line_number': i + 1,  # 1-indexed
            })
            i = j
        else:
            i += 1
    return tables


def validate_table(table: Dict, file_path: str) -> List[Dict]:
    """校验单个表格的标签和锚点格式

    返回违规列表 [{"file", "line", "table_line", "violation_type", "detail", "actual"}, ...]

    规则：每张表要么三个标签全有（各恰好 1 个），要么三个标签全无（附属属性表）。
    仅当 0 < 总标签数 < 3 或某个标签 >1 时才判违规。
    """
    violations = []
    header = table['header']
    table_line = table['line_number']

    # 统计标签数量
    label_counts = {tag: 0 for tag in LABELS}
    code_col_idx = None
    for idx, (col_name, label) in enumerate(header):
        if label:
            label_counts[label] = label_counts.get(label, 0) + 1
            if label == '<anchor:code>':
                code_col_idx = idx

    total_labels = sum(label_counts.values())

    # 规则：要么三个标签全有，要么三个标签全无
    # 全无（0 个）→ 合法通过（附属属性表，如 domain-model.md 的行为归属表）
    # 全有（3 个，各恰好 1 个）→ 校验锚点格式
    # 部分有（0 < total < 3 或某个标签 >1）→ 违规
    if total_labels == 0:
        # 附属属性表，合法通过
        return violations

    if total_labels < 3:
        # 部分有标签——违规，报告缺失
        for tag in LABELS:
            count = label_counts.get(tag, 0)
            if count == 0:
                violations.append({
                    'file': file_path,
                    'table_line': table_line,
                    'violation_type': 'MISSING_LABEL',
                    'detail': f'表头缺少标签 {tag}（要么三个标签全有，要么全无）',
                    'actual': f'found 0 occurrences',
                })

    # 校验每个标签恰好 1 个（全有情况下，>1 也是违规）
    for tag in LABELS:
        count = label_counts.get(tag, 0)
        if count > 1:
            violations.append({
                'file': file_path,
                'table_line': table_line,
                'violation_type': 'DUPLICATE_LABEL',
                'detail': f'表头有 {count} 个 {tag} 标签（应恰好 1 个）',
                'actual': f'found {count} occurrences',
            })

    # 校验 anchor:code 列的值格式（仅当该列存在时）
    if code_col_idx is not None:
        for row_idx, row in enumerate(table['rows']):
            if code_col_idx >= len(row):
                continue
            raw_value = row[code_col_idx]
            # 跳过空值和占位符
            value = strip_backticks(raw_value)
            if not value or value in ('—', 'N/A', '{ClassName}', '{ClassName}.{method}',
                                       '{ServiceName}.{method}', '{PortName}.{method}',
                                       '{TaskClass}', '{TopicName}', '{HTTP_METHOD}:/{path}',
                                       '{锚点}'):
                continue

            # 校验是否符合三类格式之一
            matched = False
            matched_format = None
            for fmt_name, pattern in ANCHOR_PATTERNS.items():
                if pattern.match(value):
                    matched = True
                    matched_format = fmt_name
                    break

            if not matched:
                violations.append({
                    'file': file_path,
                    'table_line': table_line + 2 + row_idx,  # 表头+分隔行+行偏移
                    'violation_type': 'INVALID_ANCHOR_FORMAT',
                    'detail': f'代码锚点 "{value}" 不符合三类格式（类名/类名.函数名/HTTP方法:/路径）',
                    'actual': value,
                })

    return violations


def check_file(file_path: str) -> List[Dict]:
    """校验单个 md 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return [{
            'file': file_path,
            'table_line': 0,
            'violation_type': 'FILE_READ_ERROR',
            'detail': str(e),
            'actual': '',
        }]

    tables = find_tables(content)
    all_violations = []
    for table in tables:
        violations = validate_table(table, file_path)
        all_violations.extend(violations)
    return all_violations


def scan_directory(docs_root: str) -> List[Dict]:
    """扫描目录下所有白名单 md 文件"""
    docs_root_path = Path(docs_root)
    if not docs_root_path.exists():
        print(f"Error: docs root not found: {docs_root_path}", file=sys.stderr)
        sys.exit(1)

    all_violations = []
    checked_files = []

    for root, dirs, files in os.walk(docs_root_path):
        for filename in files:
            if filename in WHITELIST_FILES:
                file_path = os.path.join(root, filename)
                file_path = file_path.replace('\\', '/')
                checked_files.append(file_path)
                violations = check_file(file_path)
                all_violations.extend(violations)

    return all_violations, checked_files


def main():
    parser = argparse.ArgumentParser(description='DDD 产物表格标签与代码锚点校验')

    parser.add_argument('--docs-root', help='DDD 文档根目录（如 docs/ddd）')
    parser.add_argument('--single-file', help='校验单个文件')
    parser.add_argument('--quiet', action='store_true', help='静默模式（只输出违规项）')

    args = parser.parse_args()

    if args.single_file:
        # 单文件模式
        file_path = args.single_file
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)

        filename = Path(file_path).name
        if filename in EXEMPT_FILES:
            print(f"[SKIP] {file_path}: 豁免文件（{filename}）", file=sys.stderr)
            sys.exit(0)

        if filename not in WHITELIST_FILES:
            print(f"[SKIP] {file_path}: 非白名单文件（{filename}）", file=sys.stderr)
            sys.exit(0)

        violations = check_file(file_path)
        checked_files = [file_path]
    elif args.docs_root:
        # 目录模式
        violations, checked_files = scan_directory(args.docs_root)
    else:
        parser.error("需要提供 --docs-root 或 --single-file")
        return

    # 构建报告
    report = {
        'metadata': {
            'checked_at': datetime.now().isoformat(),
            'mode': 'single_file' if args.single_file else 'directory',
            'checked_files': checked_files,
        },
        'summary': {
            'total_files_checked': len(checked_files),
            'total_violations': len(violations),
            'violation_breakdown': {
                'MISSING_LABEL': sum(1 for v in violations if v['violation_type'] == 'MISSING_LABEL'),
                'DUPLICATE_LABEL': sum(1 for v in violations if v['violation_type'] == 'DUPLICATE_LABEL'),
                'INVALID_ANCHOR_FORMAT': sum(1 for v in violations if v['violation_type'] == 'INVALID_ANCHOR_FORMAT'),
                'FILE_READ_ERROR': sum(1 for v in violations if v['violation_type'] == 'FILE_READ_ERROR'),
            },
            'overall_pass': len(violations) == 0,
        },
        'violations': violations,
    }

    # JSON 报告输出到 stdout
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 摘要信息到 stderr
    if not args.quiet:
        print(f"\n=== DDD Anchor Check Summary ===", file=sys.stderr)
        print(f"Files checked: {len(checked_files)}", file=sys.stderr)
        print(f"Total violations: {len(violations)}", file=sys.stderr)
        if violations:
            print(f"\nViolations by type:", file=sys.stderr)
            for vtype, count in report['summary']['violation_breakdown'].items():
                if count > 0:
                    print(f"  {vtype}: {count}", file=sys.stderr)
            print(f"\nDetails:", file=sys.stderr)
            for v in violations:
                print(f"  [{v['violation_type']}] {v['file']}:{v.get('table_line', '?')}", file=sys.stderr)
                print(f"    {v['detail']}", file=sys.stderr)
                if v.get('actual'):
                    print(f"    actual: {v['actual']}", file=sys.stderr)
        else:
            print(f"[PASS] All tables have correct labels and anchor formats.", file=sys.stderr)

    sys.exit(0 if len(violations) == 0 else 1)


if __name__ == '__main__':
    main()
