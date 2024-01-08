import pytest

from pathlib import Path


# @pytest.fixture(scope="session")
@pytest.fixture
def tmpdir_with_files(tmp_path_factory) -> Path:
    """
    Returns a Path to a test directory with some files to list.
    """
    dir1: Path = tmp_path_factory.mktemp("testdir")

    (dir1 / "file'1.data").write_bytes(b"11")
    #  Note: A file name containing a single-quote character caused a failure
    #  during use of the application. The above file name covers that case.

    dir2a = dir1 / "a"
    dir2a.mkdir()
    (dir2a / "file2a1.data").write_bytes(b"21")
    (dir2a / "file2a2.data").write_bytes(b"22")

    dir2b = dir1 / "b"
    dir2b.mkdir()
    (dir2b / "file2b1.data").write_bytes(b"23")
    (dir2b / "file2b2.data").write_bytes(b"24")

    return dir1
