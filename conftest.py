"""Pytest 全局配置。

- 确保项目根目录在 sys.path 上，测试可以直接 `from app import app`；
- 把存档目录指向临时目录，测试不会写脏真实存档。
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="ai-test-report-")
