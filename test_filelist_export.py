from pathlib import Path

import filelist_export
import mkfilelist


def test_main(tmp_path):
    scan_path: Path = tmp_path / "test_main_input"
    scan_path.mkdir()
    (scan_path / "file1.txt").write_text("file1")
    (scan_path / "file2.txt").write_text("file2")
    out_path: Path = tmp_path / "test_main_ouput"
    out_path.mkdir()

    args1 = ["mkfilelist.py", str(scan_path), "test_main", "-o", str(out_path)]
    assert 0 == mkfilelist.main(args1)

    db_files = list(out_path.glob("*.sqlite"))
    assert db_files, "mkfilelist.py should make a .sqlite file."

    db_file = str(db_files[0])

    args2 = ["filelist_export.py", db_file, f"--output-to={out_path}"]
    result = filelist_export.main(args2)
    assert 0 == result
