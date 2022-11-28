#!/usr/bin/env python3

import argparse
import sqlite3
import sys

from pathlib import Path
from textwrap import dedent

# from rich import print as rprint


def get_args(argv):
    ap = argparse.ArgumentParser(
        description="Export data from a SQLite database created by "
        "'mkfilelist.py'."
    )

    ap.add_argument(
        "db_file",
        action="store",
        help="Name of SQLite database file created by 'mkfilelist.py'. "
        "Include the full path to the file unless it is in the current "
        "working directory.",
    )

    ap.add_argument(
        "-o",
        "--output-to",
        dest="outdir",
        action="store",
        help="Directory in which to create output files. Optional. "
        "By default the output is created in the currrent working "
        "directory.",
    )

    args = ap.parse_args(argv[1:])

    # rprint(args)

    db_path = Path(args.db_file)

    assert db_path.exists()

    outdir = args.outdir
    if outdir:
        out_path = Path(outdir)
    else:
        out_path = Path.cwd()

    assert out_path.exists()

    return db_path, out_path


def get_db_info(con: sqlite3.Connection):
    cur = con.cursor()
    stmt = "SELECT * FROM db_info"
    row = cur.execute(stmt).fetchone()
    rowdict = {}
    for i, desc in enumerate(cur.description):
        rowdict[desc[0]] = row[i]
    cur.close()
    return rowdict


def export_filelist_csv(db_info, out_path: Path, con: sqlite3.Connection):
    fn = str(db_info["created"])
    fn = fn.replace(" ", "_").replace("-", "").replace(":", "")
    fn = f"FileList-{db_info['title']}-{fn}.csv"
    fn = str(out_path / fn)

    print(f"Writing '{fn}'.")

    cur = con.cursor()

    stmt = dedent(
        """
        SELECT
            sha1,
            md5,
            file_name,
            file_size,
            last_modified,
            dir_level,
            dir_name,
            error
        FROM view_filelist
        ORDER BY dir_name, file_name
        """
    )

    with open(fn, "w") as f:
        f.write(
            '"SHA1","MD5","FileName","Size","LastModified","Level",'
            '"DirName","Error"\n'
        )

        for row in cur.execute(stmt):
            f.write(
                '"{}","{}","{}",{},"{}",{},"{}","{}"\n'.format(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                )
            )

    cur.close()


def export_fullname_csv(db_info, out_path: Path, con: sqlite3.Connection):
    fn = str(db_info["created"])
    fn = fn.replace(" ", "_").replace("-", "").replace(":", "")
    fn = f"FileList-{db_info['title']}-{fn}-FullName.csv"
    fn = str(out_path / fn)

    print(f"Writing '{fn}'.")

    sep = db_info["host_path_sep"]

    cur = con.cursor()

    stmt = (
        "SELECT dir_name, file_name FROM view_filelist "
        "ORDER BY dir_name, file_name"
    )

    with open(fn, "w") as f:
        f.write('"FullName"\n')
        for row in cur.execute(stmt):
            f.write('"{}{}{}"\n'.format(row[0], sep, row[1]))

    cur.close()


def main(argv):
    db_path, out_path = get_args(argv)

    assert isinstance(db_path, Path)
    assert isinstance(out_path, Path)

    print(f"Reading '{db_path}'.")

    con = sqlite3.connect(str(db_path))

    db_info = get_db_info(con)

    print("\nFileList database details:")
    for k, v in db_info.items():
        print(f"  {k:>15} = {v}")

    # export_filelist_csv(db_info, out_path, con)

    # export_fullname_csv(db_info, out_path, con)

    con.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
