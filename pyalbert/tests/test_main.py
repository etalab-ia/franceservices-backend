import sys
from pathlib import Path

import pytest

# Add the parent directory of pyalbert to the system path
local_parent_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(local_parent_dir))

from pyalbert.albert import main

# A list of commands to test
commands_to_test = [
    (["__main__"], "IGNORED"),
    (["__main__", "--help"], "IGNORED"),
]


@pytest.mark.parametrize("cmd_args, expected_output", commands_to_test)
def test_main(monkeypatch, capsys, cmd_args, expected_output):
    # Set argv to simulate a command line call
    # monkeypatch.setattr(sys, 'argv', cmd_args)
    test_args = ["__main__", "--help"]
    original_argv = sys.argv
    # Replace sys.argv with test_args
    sys.argv = test_args

    try:
        with pytest.raises(SystemExit):  # docopt calls sys.exit() after printing help
            main()

        # Capture the output / use the capsys fixture
        captured = capsys.readouterr()
        print(captured)

    finally:
        # Restore the original sys.argv
        sys.argv = original_argv

    assert True
