#!/usr/bin/env python3

import argparse
import sqlite3
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import List, Tuple


app_name = Path(__file__).name

app_version = "230104.1"

run_dt = datetime.now()


AppOptions = namedtuple(
    "AppOptions", "src_dbs, outpath, outfilename, do_overwrite, do_append"
)


def run_sql(cur: sqlite3.Cursor, stmt: str, data=None):
    try:
        if data:
            cur.execute(stmt, data)
        else:
            cur.execute(stmt)
    except Exception as e:
        print("\n{}\n".format(stmt))
        raise e


def create_tables(con: sqlite3.Connection):
    cur = con.cursor()

    print("Creating table 'filelists'.")
    stmt = dedent(
        """
        CREATE TABLE filelists (
            id INTEGER PRIMARY KEY,
            tag TEXT,
            file_name TEXT,
            created TEXT,
            host TEXT,
            scandir TEXT,
            title TEXT,
            finished TEXT,
            host_path_sep TEXT,
            db_version INTEGER,
            app_name TEXT,
            app_version TEXT
        )
        """
    )
    run_sql(cur, stmt)

    print("Creating table 'files'.")
    stmt = dedent(
        """
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            filelist_id,
            file_id INTEGER,
            sha1 TEXT,
            md5 TEXT,
            file_name TEXT,
            file_size INTEGER,
            last_modified TEXT,
            dir_name TEXT,
            dir_level INTEGER,
            error TEXT
        )
        """
    )
    run_sql(cur, stmt)


def create_view_for_filelist(dst_con: sqlite3.Connection, filelist_id: int):
    cur = dst_con.cursor()
    view_name = "filelist{}".format(filelist_id)
    print("Creating view '{}'.".format(view_name))
    stmt = dedent(
        """
        CREATE VIEW {} AS
            SELECT
                b.tag,
                a.id,
                a.sha1,
                a.md5,
                a.file_name,
                a.file_size,
                a.last_modified,
                a.dir_name,
                a.dir_level,
                a.error
            FROM files a
            JOIN filelists b
            ON a.filelist_id = b.id
            WHERE b.id = {}
            ORDER BY a.dir_name, a.file_name;
        """
    ).format(view_name, filelist_id)
    run_sql(cur, stmt)
    dst_con.commit()


def get_tag_from_src_title(src_con: sqlite3.Connection) -> str:
    cur = src_con.cursor()
    stmt = "SELECT title FROM db_info;"
    cur.execute(stmt)
    result = cur.fetchone()[0]
    cur.close()
    return str(result)


def insert_filelist(
    dst_con: sqlite3.Connection,
    src_con: sqlite3.Connection,
    src_tag: str,
    src_path: Path,
):
    if src_tag is None:
        src_tag = get_tag_from_src_title(src_con)

    dst_cur = dst_con.cursor()

    dst_cur.execute(
        "SELECT COUNT(*) FROM filelists WHERE tag = '{}'".format(src_tag)
    )
    result = dst_cur.fetchone()[0]
    if result:
        print("Tag '{}' already in destination.".format(src_tag))
        return

    src_cur = src_con.cursor()

    stmt = dedent(
        """
        SELECT
            created,
            host,
            scandir,
            title,
            finished,
            host_path_sep,
            db_version,
            app_name,
            app_version
        FROM db_info
        """
    )

    src_cur.execute(stmt)

    db_info = src_cur.fetchone()

    data = (
        None,
        src_tag,
        src_path.name,
        db_info[0],
        db_info[1],
        db_info[2],
        db_info[3],
        db_info[4],
        db_info[5],
        db_info[6],
        db_info[7],
        db_info[8],
    )

    stmt = "INSERT INTO filelists VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

    run_sql(dst_cur, stmt, data)

    filelist_id = dst_cur.lastrowid

    dst_con.commit()

    sel_stmt = dedent(
        """
        SELECT
            id,
            sha1,
            md5,
            file_name,
            file_size,
            last_modified,
            dir_name,
            dir_level,
            error
        FROM view_filelist
        """
    )

    for row in src_cur.execute(sel_stmt):
        data = (
            None,
            filelist_id,
            row[0],
            row[1],
            row[2],
            row[3],
            row[4],
            row[5],
            row[6],
            row[7],
            row[8],
        )
        ins_stmt = "INSERT INTO files VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"

        # CREATE TABLE files (
        #     id INTEGER PRIMARY KEY,
        #     filelist_id,
        #     file_id INTEGER,
        #     sha1 TEXT,
        #     md5 TEXT,
        #     file_name TEXT,
        #     file_size INTEGER,
        #     last_modified TEXT,
        #     dir_name TEXT,
        #     dir_level INTEGER,
        #     error TEXT
        # )

        run_sql(dst_cur, ins_stmt, data)

    src_cur.close()

    dst_con.commit()
    dst_cur.close()

    create_view_for_filelist(dst_con, filelist_id)


def get_args(argv):
    ap = argparse.ArgumentParser(
        description="Merges two or more SQLite databases created by "
        "mkfilelist.py.\n"
    )

    ap.add_argument(
        "source_files",
        nargs="*",
        action="store",
        help="Files to be merged. Multiple file names are separated by "
        "spaces. A single file name may be given in the case of appending "
        "to an existing merged database. In that case, the destination "
        "file must also be specified in the --name parameter. Also, a Tag "
        "(short name for a filelist to use instead of its Title) can be "
        "included after a file name using a comma (with no spaces) followed "
        "by the tag (filename,tag).",
    )

    ap.add_argument(
        "-o",
        "--output-to",
        dest="outdir",
        action="store",
        help="Directory in which to create the output file. Optional. "
        "By default the output file is created in the currrent working "
        "directory.",
    )

    ap.add_argument(
        "-n",
        "--name",
        dest="outfilename",
        action="store",
        help="Name of the output file to create. Optional. "
        "By default the output file is named starting with 'MergeFileLists' "
        "followed by a current date_time tag. An existing file with the "
        "same name will not be overwritten unless the --force option "
        "is used.",
    )

    ap.add_argument(
        "--force",
        dest="do_overwrite",
        action="store_true",
        help="Allow an existing output file to be overwritten.",
    )

    ap.add_argument(
        "-a",
        "--append",
        dest="do_append",
        action="store_true",
        help="Append the filelist data to an existing merged database. "
        "The destination file name must be specified using the --name "
        "parameter.",
    )

    return ap.parse_args(argv[1:])


def get_opts(argv):
    args = get_args(argv)

    if not args.source_files:
        raise SystemExit("No source files specified.")

    src_dbs: List[Tuple[Path, str]] = []  # (filename, tag).

    for src in args.source_files:
        #  Tag may be included in arg as 'filename,tag'.
        src_parts = src.split(",")

        src_path = Path(src_parts[0])

        if not src_path.exists():
            raise SystemExit("File not found: '{}'".format(src_parts[0]))

        if len(src_parts) == 1:
            src_dbs.append((src_path, None))
        elif len(src_parts) == 2:
            src_dbs.append((src_path, src_parts[1]))
        else:
            raise SystemExit("Invalid file name and tag (too many commas).")

    if args.outdir:
        outpath = Path(args.outdir)
        if not (outpath.exists() and outpath.is_dir()):
            raise SystemExit("Path not found (outdir): " + outpath)
    else:
        outpath = Path.cwd()

    if args.outfilename:
        p = Path(args.outfilename)
        if p.parent.name:
            if args.outdir:
                raise SystemExit(
                    "Do not use outdir (-o, --output-to) when including the "
                    "directory in outfilename (--name)."
                )
            outpath = p.parent

        check_fn = outpath.joinpath(p.name)
        if check_fn.exists() and not (args.do_overwrite or args.do_append):
            raise SystemExit("Output file already exists: {}".format(check_fn))

        outfilename = p.name
    else:
        outfilename = "MergeFileLists-{}.sqlite".format(
            run_dt.strftime("%Y%m%d_%H%M%S")
        )

    return AppOptions(
        src_dbs, outpath, outfilename, args.do_overwrite, args.do_append
    )


def main(argv):
    print("\n{} (version {})\n".format(app_name, app_version))

    opts = get_opts(argv)

    output_path: Path = opts.outpath / opts.outfilename

    print(
        "{} '{}'.".format(
            ("Appending" if opts.do_append else "Writing"), output_path
        )
    )

    if output_path.exists():
        if opts.do_overwrite:
            print("Overwrite existing file.")
            output_path.unlink()
        elif not opts.do_append:
            raise SystemExit("Cannot replace existing output file.")
    elif opts.do_append:
        raise SystemExit("Destination file not found. Cannot append.")

    out_con = sqlite3.connect(output_path)

    if not opts.do_append:
        create_tables(out_con)

    for db_path, src_tag in opts.src_dbs:
        assert db_path.exists()
        print("Reading '{}'.".format(db_path))

        in_con = sqlite3.connect(str(db_path))

        insert_filelist(out_con, in_con, src_tag, db_path)

        in_con.rollback()
        in_con.close()

    out_con.close()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
