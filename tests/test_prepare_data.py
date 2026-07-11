import subprocess
import sys


def test_prepare_data_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/prepare_data.py", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--source" in result.stdout
    assert "--output" in result.stdout
