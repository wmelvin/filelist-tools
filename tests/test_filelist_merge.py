import pytest

from importlib import reload
from pathlib import Path

import filelist_merge
import mkfilelist


def test_filelist_merge():
    """
    An initial test to get things started.
    TODO: Add some real tests.
    """
    assert filelist_merge.app_name
    assert filelist_merge.app_version


@pytest.fixture
def path_to_sqlite_dbs(tmpdir_with_files, tmp_path) -> Path:
    outdir: Path = tmp_path / "output"
    outdir.mkdir()

    dir1: Path = tmpdir_with_files
    assert dir1.exists()
    dir2 = dir1 / "a"
    assert dir2.exists()
    dir3 = dir1 / "b"
    assert dir3.exists()

    args = [
        "mkfilelist.py",
        str(dir1),
        "test_dir1",
        f"--name={outdir / 'test_dir1.sqlite'}",
    ]
    result = mkfilelist.main(args)
    assert 0 == result

    args = [
        "mkfilelist.py",
        str(dir2),
        "test_dir2",
        f"--name={outdir / 'test_dir2.sqlite'}",
    ]
    result = mkfilelist.main(args)
    assert 0 == result

    args = [
        "mkfilelist.py",
        str(dir3),
        "test_dir3",
        f"--name={outdir / 'test_dir3.sqlite'}",
    ]
    result = mkfilelist.main(args)
    assert 0 == result

    return outdir


def test_dbs_created(path_to_sqlite_dbs):
    dbs_path: Path = path_to_sqlite_dbs
    dbfiles = list(dbs_path.glob("*.sqlite"))
    assert len(dbfiles) == 3, "Should create 3 .sqlite files."
    assert (dbs_path / "mkfilelist.log").exists(), "Should make a log file."


def test_merge_two_dbs(path_to_sqlite_dbs):
    dbs_path: Path = path_to_sqlite_dbs
    dbfiles = list(dbs_path.glob("*.sqlite"))
    assert len(dbfiles) == 3, "Should be 3 *.sqlite files."
    dbfiles.sort()
    args = [
        "filelist_merge.py",
        str(dbfiles[0]),
        str(dbfiles[1]),
        "-o",
        str(dbs_path),
        "--name",
        "test_merge_two_dbs.sqlite",
    ]
    result = filelist_merge.main(args)
    assert result == 0
    assert (dbs_path / "test_merge_two_dbs.sqlite").exists()


def test_merge_three_dbs(path_to_sqlite_dbs):
    dbs_path: Path = path_to_sqlite_dbs

    test_output = Path.cwd() / "output_from_test"
    if not test_output.exists():
        test_output.mkdir()
    (test_output / "test_merge_three_dbs.txt").write_text(
        f"{dbs_path}\n"
    )

    dbfiles = list(dbs_path.glob("*.sqlite"))
    assert len(dbfiles) == 3, "Should be 3 *.sqlite files."
    dbfiles.sort()

    args = [
        "filelist_merge.py",
        str(dbfiles[0]),
        str(dbfiles[1]),
        str(dbfiles[2]),
        "-o",
        str(dbs_path),
        "--name",
        "test_merge_three_dbs.sqlite",
    ]

    result = filelist_merge.main(args)

    assert result == 0
    assert (dbs_path / "test_merge_three_dbs.sqlite").exists()


def test_merge_and_append(path_to_sqlite_dbs):
    dbs_path: Path = path_to_sqlite_dbs
    dbfiles = list(dbs_path.glob("*.sqlite"))
    assert len(dbfiles) == 3, "Should be 3 *.sqlite files."
    dbfiles.sort()

    args = [
        "filelist_merge.py",
        str(dbfiles[0]),
        str(dbfiles[1]),
        "-o",
        str(dbs_path),
        "--name",
        "test_merge_and_append.sqlite",
    ]
    result = filelist_merge.main(args)
    assert result == 0
    assert (dbs_path / "test_merge_and_append.sqlite").exists()

    reload(filelist_merge)

    args = [
        "filelist_merge.py",
        str(dbfiles[2]),
        "-o",
        str(dbs_path),
        "--name",
        "test_merge_and_append.sqlite",
        "--append"
    ]
    result = filelist_merge.main(args)
    assert result == 0


# def test_name_required_for_append(path_to_sqlite_dbs):
#     dbs_path: Path = path_to_sqlite_dbs
#     dbfiles = list(dbs_path.glob("*.sqlite"))
#     assert len(dbfiles) == 3, "Should be 3 *.sqlite files."
#     dbfiles.sort()

#     args = [
#         "filelist_merge.py",
#         str(dbfiles[0]),
#         "--append"
#     ]
#     with pytest.raises(SystemExit):
#         filelist_merge.get_opts(args)
