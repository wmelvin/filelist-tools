from __future__ import annotations

from pathlib import Path

import pytest

from mkfilelist import (
    AppOptions,
    get_args,
    get_file_info,
    get_hashes,
    get_opts,
    get_output_file_path,
    get_percent_complete,
    main,
)


@pytest.fixture(scope="session")
def test_file_fixture(tmp_path_factory) -> tuple[Path, str, str]:
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


def test_get_hashes(test_file_fixture):
    test_file, sha1sum_result, md5sum_result = test_file_fixture
    sha1, md5, err = get_hashes(test_file)
    assert sha1sum_result == sha1
    assert md5sum_result == md5
    assert err == ""


def test_get_file_info(test_file_fixture):
    test_file, sha1sum_result, md5sum_result = test_file_fixture
    opts = AppOptions(str(test_file.parent), None, None, False, 0, "TITLE", None, True)
    file_info = get_file_info(str(test_file), opts)
    assert str(test_file.name) == file_info.file_name
    assert str(test_file.parent) == file_info.dir_name
    assert sha1sum_result == file_info.sha1
    assert md5sum_result == file_info.md5


def test_get_args():
    args = ["mkfilelist.py", "DIRPATH", "TITLE"]
    result = get_args(args)
    assert result.scandir == "DIRPATH"
    assert result.title == "TITLE"


def test_path_not_found(capsys):
    args = ["mkfilelist.py", "badpath", "TITLE"]
    with pytest.raises(SystemExit):
        get_opts(args)
    assert "Path not found" in capsys.readouterr().err


def test_get_opts(test_file_fixture):
    args = [
        "mkfilelist.py",
        str(test_file_fixture[0].parent),
        "TITLE",
        "--name",
        "TestFileList.sqlite",
    ]
    opts: AppOptions = get_opts(args)
    assert opts.scandir == str(test_file_fixture[0].parent)
    assert opts.dirname_start == 0
    assert Path(opts.outfilename).name == "TestFileList.sqlite"
    assert opts.do_overwrite is False


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
    assert result == 0


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


def test_creates_sqlite_db(tmpdir_with_files, tmp_path):
    outdir = tmp_path / "output"
    outdir.mkdir()

    test_output = Path.cwd() / "output_from_test"
    if not test_output.exists():
        test_output.mkdir()

    args = [
        "mkfilelist.py",
        str(tmpdir_with_files),
        "test_creates_sqlite_db",
        f"--output-to={outdir}",
    ]

    #  Write the path to the temporary SQLite database to a text file,
    #  within the project tree, where it can be used to open the
    #  database file in the DB Browser for SQLite (sqlitebrowser)
    #  for manual review.
    opts = get_opts(args)
    fn = get_output_file_path(opts)
    (test_output / "test_creates_sqlite_db.txt").write_text(
        f"output_file_name:\n{fn}\n\nsqlitebrowser {fn}\n"
    )

    result = main(args)
    assert result == 0
    dbfiles = list(outdir.glob("*.sqlite"))
    assert dbfiles, "Should create a .sqlite file in the output directory."
    assert (outdir / "mkfilelist.log").exists(), "Should make a log file."


def test_w_trim_parent_option(tmpdir_with_files, tmp_path):
    outdir = tmp_path / "output"
    outdir.mkdir()
    args = [
        "mkfilelist.py",
        str(tmpdir_with_files),
        "test_w_trim_parent_option",
        f"--output-to={outdir}",
        "-t",
        "--no-log",
    ]
    result = main(args)
    assert result == 0
    dbfiles = list(outdir.glob("*.sqlite"))
    assert dbfiles, "Should create a .sqlite file in the output directory."
    assert not (
        outdir / "mkfilelist.log"
    ).exists(), "Should not make a log file given '--no-log'."


def test_get_pct_complete():
    pct, pct_str = get_percent_complete(0, 0)
    assert pct == 0.0
    assert pct_str == "(?)"

    pct, pct_str = get_percent_complete(1, 0)
    assert pct == 0.0
    assert pct_str == "(?)"

    pct, pct_str = get_percent_complete(0, 1)
    assert pct == 0.0
    assert pct_str == "0%"

    pct, pct_str = get_percent_complete(100, 200)
    assert pct == 0.5
    assert pct_str == "50.0%"

    pct, pct_str = get_percent_complete(200, 200)
    assert pct == 1.0
    assert pct_str == "99.9%", "Should not display over 99.9%."


def test_specify_output_filename(tmpdir_with_files, tmp_path, capsys):
    outdir = tmp_path / "output"
    outdir.mkdir()
    scan_dir = str(tmpdir_with_files)
    args = [
        "mkfilelist.py",
        scan_dir,
        "test_specify_output_filename",
        f"--output-to={outdir}",
        "-t",
        "--name=TestFilelist.sqlite",
    ]
    result = main(args)
    assert result == 0

    dbfiles = list(outdir.glob("*.sqlite"))

    assert len(dbfiles) == 1, "Should create one .sqlite file."

    assert dbfiles[0].name == "TestFilelist.sqlite", "Should use specified file name."

    #  Running again should raise a SystemExit because the output
    #  file already exists.
    with pytest.raises(SystemExit):
        main(args)

    assert "Output file already exists" in capsys.readouterr().err

    #  Add the --force option and run again.
    args = [
        "mkfilelist.py",
        scan_dir,
        "test_specify_output_filename",
        f"--output-to={outdir}",
        "-t",
        "--name=TestFilelist.sqlite",
        "--force",
    ]
    result = main(args)
    assert result == 0, "Should succeed replacing previous output file."
