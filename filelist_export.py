#!/usr/bin/env python3

import argparse
import sqlite3
import string
import sys

from collections import namedtuple
from pathlib import Path
from textwrap import dedent

# from rich import print as rprint

app_name = Path(__file__).name

app_version = "230212.1"

AppOptions = namedtuple(
    "AppOptions", "db_path, out_path, do_fullname, do_alt, do_dfn"
)


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
        "By default the output is created in the current working "
        "directory.",
    )

    ap.add_argument(
        "--fullname",
        dest="do_fullname",
        action="store_true",
        help="Also create the 'FullNames' CSV file.",
    )

    ap.add_argument(
        "--alt",
        dest="do_alt",
        action="store_true",
        help="Also create the 'Alt' (wide) CSV file.",
    )

    ap.add_argument(
        "--dfn",
        dest="do_dfn",
        action="store_true",
        help="Create a CSV file by Directory and FileName where those are the "
        "first two columns.",
    )

    return ap.parse_args(argv[1:])


def get_opts(argv) -> AppOptions:
    args = get_args(argv)

    # rprint(args)

    db_path = Path(args.db_file)

    assert db_path.exists()
    # TODO: Handle error.

    outdir = args.outdir
    if outdir:
        out_path = Path(outdir)
    else:
        out_path = Path.cwd()

    assert out_path.exists()

    return AppOptions(
        db_path, out_path, args.do_fullname, args.do_alt, args.do_dfn
    )


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
    fn = "FileList-{}-{}.csv".format(db_info["title"], fn)
    fn = str(out_path / fn)

    print("Writing '{}'.".format(fn))

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
    fn = "FileList-{}-{}-FullName.csv".format(db_info["title"], fn)
    fn = str(out_path / fn)

    print("Writing '{}'.".format(fn))

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


def is_hex(s: str) -> bool:
    return all(c in string.hexdigits for c in s)


def is_not_extension(s: str) -> bool:
    #  Set of characters observed in what are not really file extensions.
    unexpected_chars = set("=&")
    return any(c in unexpected_chars for c in s)


def extension_type(s: str) -> str:
    if s.startswith("."):
        ext = s[1:]
    else:
        ext = s

    if ext.isnumeric():
        return "Num"
    elif "~" in ext:
        return "Bak"
    elif len(ext) > 5 and is_hex(ext):
        # Require a minimum length. For example, the extension '.accdb'
        # is valid hexadecimal, but should be type 'Txt'.
        return "Hex"
    elif is_not_extension(ext):
        return "Not"
    else:
        return "Txt"


def export_filelist_alt_csv(db_info, out_path: Path, con: sqlite3.Connection):
    fn = str(db_info["created"])
    fn = fn.replace(" ", "_").replace("-", "").replace(":", "")
    fn = "FileList-{}-{}-Alt.csv".format(db_info["title"], fn)
    fn = str(out_path / fn)

    print("Writing '{}'.".format(fn))

    sep = db_info["host_path_sep"]

    cur = con.cursor()

    stmt = dedent(
        """
        SELECT
            sha1,
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
    i_sha1 = 0
    i_file_name = 1
    i_file_size = 2
    i_last_modified = 3
    i_dir_level = 4
    i_dir_name = 5
    i_error = 6

    with open(fn, "w") as f:
        f.write(
            '"KEY","SHA1","FileName","DirName","LastModified","Size",'
            '"FileExt","ExtType","Level","FullName","Error"\n'
        )
        for row in cur.execute(stmt):
            key = "{}:{}".format(row[i_sha1], row[i_file_name])
            full_name = "{}{}{}".format(row[i_dir_name], sep, row[i_file_name])
            file_ext = Path(row[i_file_name]).suffix
            f.write(
                '"{}","{}","{}","{}","{}","{}","{}","{}","{}","{}",'
                '"{}"\n'.format(
                    key,
                    row[i_sha1],
                    row[i_file_name],
                    row[i_dir_name],
                    row[i_last_modified],
                    row[i_file_size],
                    file_ext,
                    extension_type(file_ext),
                    row[i_dir_level],
                    full_name,
                    row[i_error],
                )
            )

    cur.close()


def export_filelist_dfn_csv(db_info, out_path: Path, con: sqlite3.Connection):
    """
    Export the filelist to CSV By Directory and File name.
    """
    fn = str(db_info["created"])
    fn = fn.replace(" ", "_").replace("-", "").replace(":", "")
    fn = "FileList-{}-{}-DirFileName.csv".format(db_info["title"], fn)
    fn = str(out_path / fn)

    print("Writing '{}'.".format(fn))

    cur = con.cursor()

    stmt = dedent(
        """
        SELECT
            sha1,
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
    i_sha1 = 0
    i_file_name = 1
    i_file_size = 2
    i_last_modified = 3
    i_dir_level = 4
    i_dir_name = 5
    i_error = 6

    with open(fn, "w") as f:
        f.write(
            '"DirName","FileName","LastModified","Size","SHA1",'
            '"Level","Error"\n'
        )
        for row in cur.execute(stmt):
            f.write(
                '"{}","{}","{}","{}","{}","{}","{}"\n'.format(
                    row[i_dir_name],
                    row[i_file_name],
                    row[i_last_modified],
                    row[i_file_size],
                    row[i_sha1],
                    row[i_dir_level],
                    row[i_error],
                )
            )

    cur.close()


def main(argv):
    print("\n{} (version {})\n".format(app_name, app_version))

    # db_path, out_path, do_fullname, do_alt, do_dfn = get_args(argv)
    opts = get_opts(argv)

    print("Reading '{}'.".format(opts.db_path))

    con = sqlite3.connect(str(opts.db_path))

    db_info = get_db_info(con)

    bar = "-" * 42
    print("\n\nFileList database details:\n{}".format(bar))
    for k, v in db_info.items():
        print("  {:>15}: {}".format(k, v))
    print("{}\n".format(bar))

    export_filelist_csv(db_info, opts.out_path, con)

    if opts.do_fullname:
        export_fullname_csv(db_info, opts.out_path, con)

    if opts.do_alt:
        export_filelist_alt_csv(db_info, opts.out_path, con)

    if opts.do_dfn:
        export_filelist_dfn_csv(db_info, opts.out_path, con)

    con.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
