"""代码生成写入安全契约测试。"""

import pytest

from app.api.v1.module_generator.gencode.service import GenTableService
from app.core.exceptions import CustomException


def test_preflight_rejects_existing_targets(tmp_path) -> None:
    existing = tmp_path / "generated.py"
    existing.write_text("manual marker", encoding="utf-8")

    with pytest.raises(CustomException, match="目标文件已存在"):
        GenTableService._preflight_generation_outputs(
            [(existing, "new content")],
            repository_root=tmp_path,
        )

    assert existing.read_text(encoding="utf-8") == "manual marker"


def test_preflight_rejects_duplicate_targets(tmp_path) -> None:
    target = tmp_path / "generated.py"

    with pytest.raises(CustomException, match="输出路径重复"):
        GenTableService._preflight_generation_outputs(
            [(target, "first"), (target, "second")],
            repository_root=tmp_path,
        )


@pytest.mark.asyncio
async def test_write_rolls_back_new_files_when_later_target_conflicts(tmp_path) -> None:
    created = tmp_path / "created.py"
    existing = tmp_path / "existing.py"
    existing.write_text("manual marker", encoding="utf-8")

    with pytest.raises(CustomException):
        await GenTableService._write_generation_outputs(
            [(created, "generated"), (existing, "must not overwrite")],
            [],
        )

    assert not created.exists()
    assert existing.read_text(encoding="utf-8") == "manual marker"
