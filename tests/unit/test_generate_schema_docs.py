from pathlib import Path
import pytest
from scripts.generate_schema_docs import generate_markdown


def test_generate_markdown_valid(tmp_path: Path) -> None:
    # Create a dummy models file with a dataclass
    models_file = tmp_path / "models.py"
    models_file.write_text(
        """
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestModel:
    \"\"\"A test model.\"\"\"
    id: int
    name: str
    description: Optional[str]
    \"\"\"Some description.\"\"\"
"""
    )

    md = generate_markdown(str(models_file))

    assert "# Pinergy API Models Schema" in md
    assert "## TestModel" in md
    assert "A test model." in md
    assert "| `id` | `int` |" in md
    assert "| `description` | `Optional[str]` | Some description. |" in md


def test_generate_markdown_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        generate_markdown("non_existent_file.py")


def test_generate_markdown_no_dataclasses(tmp_path: Path) -> None:
    models_file = tmp_path / "models.py"
    models_file.write_text(
        """
class NotADataclass:
    id: int
"""
    )
    with pytest.raises(ValueError, match="No dataclasses detected"):
        generate_markdown(str(models_file))
