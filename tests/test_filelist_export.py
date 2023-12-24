
from pathlib import Path

import pytest

import filelist_export
import mkfilelist



def test_get_opts(tmp_path):
    fake_db: Path = tmp_path / "fake.sqlite"
    fake_db.write_text("That's no database.")
    args = ["filelist_export.py", str(fake_db)]
    opts = filelist_export.get_opts(args)
    assert isinstance(opts.db_path, Path)
    assert isinstance(opts.out_path, Path)


def test_main(tmp_path):
    scan_path: Path = tmp_path / "test_main_input"
    scan_path.mkdir()
    (scan_path / "file1.txt").write_text("file1")
    (scan_path / "file2.txt").write_text("file2")
    out_path: Path = tmp_path / "test_main_ouput"
    out_path.mkdir()

    print(f"\n{out_path=}")

    args1 = ["mkfilelist.py", str(scan_path), "test_main", "-o", str(out_path)]
    assert 0 == mkfilelist.main(args1)

    db_files = list(out_path.glob("*.sqlite"))
    assert 1 == len(db_files), "mkfilelist.py should make one .sqlite file."

    db_file = str(db_files[0])

    args2 = ["filelist_export.py", db_file, f"--output-to={out_path}"]
    result = filelist_export.main(args2)
    assert 0 == result

    csv_files = list(out_path.glob("*.csv"))
    assert 1 == len(csv_files), "Should make one .csv file."


def test_bad_file_name(tmp_path, capsys):
    bad_filename = str(tmp_path / "im-not-here.sqlite")
    args = [
        "filelist_export.py",
        bad_filename,
        f"--output-to={tmp_path}"
    ]
    with pytest.raises(SystemExit):
        filelist_export.main(args)

    captured = capsys.readouterr()

    assert f"Cannot find '{bad_filename}'" in captured.err


def test_bad_output_dir_name(tmp_path: Path, capsys):
    fake_db = tmp_path / "fake.db"
    fake_db.write_text(
        "Not really a database, but that shouldn't matter here."
    )
    assert fake_db.exists()

    bad_out_dir = tmp_path / "im-not-here"
    assert not bad_out_dir.exists()

    args = [
        "filelist_export.py",
        str(fake_db),
        f"--output-to={str(bad_out_dir)}"
    ]
    with pytest.raises(SystemExit):
        filelist_export.main(args)

    captured = capsys.readouterr()

    assert f"Directory not found: '{bad_out_dir}'" in captured.err
