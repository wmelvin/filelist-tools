import pytest

from pathlib import Path
from typing import Tuple

from mkfilelist import (
    get_args,
    get_opts,
    get_hashes,
    get_file_info,
    get_output_file_name,
    AppOptions,
    main,
)


@pytest.fixture(scope="session")
def test_file_fixture(tmp_path_factory) -> Tuple[Path, str, str]:
    """
    Creates a file, in a temporary directory, with specific binary content.

    The GNU 'sha1sum' utility was used to get the SHA1 hash of an instance
    of the file. The result is in sha1sum_result.

    The GNU 'md5sum' utility was used to get the MD5 hash of an instance
    of the file. The result is in md5sum_result.

    Returns a tuple (test_file: Path, sha1sum_result: str, md5sum_result: str).
    """

    byte_data = b"sometextturnedintobytes"

    #  Result from running the sha1sum command on a file created with the
    #  byte_data value.
    sha1sum_result = "aac734c0bd8710dcc14b3d6b0b38b5b58a62ca33"

    #  Result from running the md5sum command on the same file.
    md5sum_result = "c8c0a87f8d62fd6e0c342c40c90a7fb5"

    test_file: Path = tmp_path_factory.mktemp("files") / "test_file_1.data"
    print(f"Writing '{test_file}'.")
    test_file.write_bytes(byte_data)
    return (test_file, sha1sum_result, md5sum_result)


@pytest.fixture(scope="session")
def test_files_path(tmp_path_factory) -> Path:
    """
    Returns a Path to a test directory with some files to list.
    """
    dir1: Path = tmp_path_factory.mktemp("testdir")
    dir2a = dir1 / "a"
    dir2a.mkdir()
    (dir2a / "file2a1.data").write_bytes(b"1")
    (dir2a / "file2a2.data").write_bytes(b"2")
    dir2b = dir1 / "b"
    dir2b.mkdir()
    (dir2b / "file2a1.data").write_bytes(b"3")
    (dir2b / "file2a2.data").write_bytes(b"4")
    return dir1


def test_get_hashes(test_file_fixture):
    test_file, sha1sum_result, md5sum_result = test_file_fixture
    sha1, md5, err = get_hashes(test_file)
    assert sha1sum_result == sha1
    assert md5sum_result == md5
    assert "" == err


def test_get_file_info(test_file_fixture):
    test_file, sha1sum_result, md5sum_result = test_file_fixture
    opts = AppOptions(str(test_file.parent), None, 0, "TITLE", False)
    file_info = get_file_info(str(test_file), opts)
    assert str(test_file.name) == file_info.file_name
    assert str(test_file.parent) == file_info.dir_name
    assert sha1sum_result == file_info.sha1
    assert md5sum_result == file_info.md5


def test_get_args():
    args = ["mkfilelist.py", "DIRPATH", "TITLE"]
    result = get_args(args)
    assert "DIRPATH" == result.scandir
    assert "TITLE" == result.title


def test_path_not_found():
    args = ["mkfilelist.py", "badpath", "TITLE"]
    with pytest.raises(SystemExit):
        get_opts(args)


def test_get_opts(test_file_fixture):
    args = ["mkfilelist.py", str(test_file_fixture[0].parent), "TITLE"]
    opts = get_opts(args)
    assert opts.scandir == str(test_file_fixture[0].parent)
    assert 0 == opts.dirname_start


def test_file_info_from_args_w_trim_parent(test_file_fixture):
    test_file, sha1sum_result, md5sum_result = test_file_fixture

    args = [
        "mkfilelist.py",
        str(test_file_fixture[0].parent),
        "TITLE",
        "--trim-parent",
    ]

    opts = get_opts(args)

    file_info = get_file_info(str(test_file), opts)

    assert str(test_file.parent.name) == file_info.dir_name, (
        "Should have only the name of the test files's parent directory, "
        "not the full path."
    )
    assert str(test_file.name) == file_info.file_name
    assert sha1sum_result == file_info.sha1
    assert md5sum_result == file_info.md5


def test_main_runs(tmp_path):
    scandir = tmp_path / "scanme"
    scandir.mkdir()  # Dir exists, but no files.
    args = ["mkfilelist.py", str(scandir), "TITLE"]
    result = main(args)
    assert 0 == result


def test_output_dir_arg(tmp_path):
    scandir = tmp_path / "scanme"
    scandir.mkdir()
    scandir = str(scandir)
    outdir = tmp_path / "outhere"
    outdir.mkdir()
    outdir = str(outdir)

    args = ["mkfilelist.py", scandir, "TITLE", "--output-to", outdir]
    opts = get_opts(args)
    assert outdir == opts.outdir

    args = ["mkfilelist.py", scandir, "TITLE", "-o", outdir]
    opts = get_opts(args)
    assert outdir == opts.outdir


def test_creates_sqlite_db(test_files_path, tmp_path):
    outdir = tmp_path / "output"
    outdir.mkdir()

    test_output = Path.cwd() / "test_output"
    if not test_output.exists():
        test_output.mkdir()

    args = [
        "mkfilelist.py",
        str(test_files_path),
        "test_creates_sqlite_db",
        f"--output-to={outdir}",
    ]

    #  Write the path to the temporary SQLite database to a text file,
    #  within the project tree, where it can be used to open the
    #  database file in the DB Browser for SQLite (sqlitebrowser)
    #  for manual review.
    opts = get_opts(args)
    fn = get_output_file_name(opts)
    (test_output / "test_creates_sqlite_db.txt").\
        write_text(f"output_file_name:\n{fn}\n\nsqlitebrowser {fn}\n")

    result = main(args)
    assert 0 == result
    dbfiles = list(outdir.glob("*.sqlite"))
    assert dbfiles, "Should create a .sqlite file in the output directory."


def test_w_trim_parent_option(test_files_path, tmp_path):
    outdir = tmp_path / "output"
    outdir.mkdir()
    args = [
        "mkfilelist.py",
        str(test_files_path),
        "test_creates_sqlite_db",
        f"--output-to={outdir}",
        "-t"
    ]
    result = main(args)
    assert 0 == result
    dbfiles = list(outdir.glob("*.sqlite"))
    assert dbfiles, "Should create a .sqlite file in the output directory."


def test_w_used_dirs_option(test_files_path, tmp_path):
    outdir = tmp_path / "output"
    outdir.mkdir()
    args = [
        "mkfilelist.py",
        str(test_files_path),
        "test_creates_sqlite_db",
        f"--output-to={outdir}",
        "-u"
    ]
    result = main(args)
    assert 0 == result
    dbfiles = list(outdir.glob("*.sqlite"))
    assert dbfiles, "Should create a .sqlite file in the output directory."
