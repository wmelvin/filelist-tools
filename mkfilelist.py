#!/usr/bin/env python3

import argparse
import hashlib
import os
import socket
import sqlite3
import stat
import sys
import time

from collections import namedtuple
from datetime import datetime
from textwrap import dedent


app_name = os.path.basename(__file__)

app_version = "221128.1"

db_version = 1


AppOptions = namedtuple(
    "AppOptions", "scandir, outdir, dirname_start, title, do_all_paths"
)

FileInfo = namedtuple(
    "FileInfo", "file_name,dir_name,dir_level,sha1,md5,size,mtime,err"
)

run_dt = datetime.now()


def get_args(argv):
    ap = argparse.ArgumentParser(
        description="Scans a specified directory path and creates a SQLite "
        "database containing some basic information about each file: "
        "File name, Directory path, Last Modified timestamp, Size, "
        "SHA1 and MD5 hashes.\n"
    )

    ap.add_argument(
        "scandir",
        action="store",
        help="Directory path to scan for files. The scan is always "
        "recursive, so all files in any sub-directories of the "
        "specified path are included.",
    )

    ap.add_argument(
        "title",
        action="store",
        help="Title to identify the filelist. "
        "The title is used in the name of the output file.",
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
        "-t",
        "--trim-parent",
        dest="trim_parent",
        action="store_true",
        help="Trim parent directory from scandir in output.",
    )

    ap.add_argument(
        "-u",
        "--used-dirs-only",
        dest="used_dirs",
        action="store_true",
        help="Only save directory paths for directories that have files. By "
        "default, all parent paths of a file's parent directory are stored.",
    )

    return ap.parse_args(argv[1:])


def get_opts(argv):
    args = get_args(argv)

    if not os.path.exists(args.scandir):
        raise SystemExit("Path not found (scandir): " + args.scandir)

    outdir = args.outdir
    if outdir:
        if not os.path.exists(outdir):
            raise SystemExit("Path not found (outdir): " + outdir)
    else:
        outdir = os.getcwd()

    if args.trim_parent:
        dirname_start = len(args.scandir) - len(
            os.path.relpath(args.scandir, os.path.dirname(args.scandir))
        )
    else:
        dirname_start = 0

    do_all_paths = not args.used_dirs

    return AppOptions(
        args.scandir, outdir, dirname_start, args.title, do_all_paths
    )


def get_hashes(file_name: str):
    """
    Returns a tuple as (sha1, md5, err):.
    """
    BUFFER_SIZE = 65535
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    try:
        with open(file_name, "rb") as f:
            while True:
                data = f.read(BUFFER_SIZE)
                if not data:
                    break
                md5.update(data)
                sha1.update(data)

        hashes = (sha1.hexdigest(), md5.hexdigest(), "")

    except Exception as ex:
        hashes = ("", "", "{}".format(ex))

    return hashes


def get_file_info(file_name: str, opts: AppOptions):
    # assert isinstance(file_name, str)
    filesize = 0
    mtime = 0
    sha1 = ""
    md5 = ""
    err_str = ""

    dir_name, base_name = os.path.split(file_name)

    dir_name = dir_name[opts.dirname_start :]  # noqa: E203

    file_mode = os.lstat(file_name).st_mode

    if stat.S_ISFIFO(file_mode):
        err_str = "(named pipe)"

    if stat.S_ISLNK(file_mode):
        err_str = "(link)"

    if len(err_str) == 0:

        filesize = os.path.getsize(file_name)

        mtime = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(file_name))
        )

        if filesize == 0:
            err_str = "(empty file)"
        else:
            sha1, md5, err_str = get_hashes(file_name)

        dir_level = dir_name.count(os.path.sep)

    return FileInfo(
        base_name, dir_name, dir_level, sha1, md5, filesize, mtime, err_str
    )


def prep_text(text: str) -> str:
    return text.replace("'", "''")


def run_sql(cur: sqlite3.Cursor, stmt: str, data=None):
    try:
        if data:
            cur.execute(stmt, data)
        else:
            cur.execute(stmt)
    except Exception as e:
        print(f"\n{stmt}\n")
        raise e


def create_tables_and_views(con: sqlite3.Connection):
    cur = con.cursor()

    print("Creating table 'db_info'.")
    stmt = dedent(
        """
        CREATE TABLE db_info (
            created TEXT PRIMARY KEY,
            host TEXT,
            scandir TEXT,
            title TEXT,
            finished TEXT,
            do_all_paths INTEGER,
            host_path_sep TEXT,
            db_version INTEGER,
            app_name TEXT,
            app_version TEXT
        )
        """
    )
    run_sql(cur, stmt)

    print("Creating table 'directories'.")
    stmt = dedent(
        """
        CREATE TABLE directories (
            id INTEGER PRIMARY KEY,
            dir_name TEXT
        )
        """
    )
    run_sql(cur, stmt)

    print("Creating table 'files'.")
    stmt = dedent(
        """
        CREATE TABLE files (
            id INTEGER PRIMARY KEY,
            sha1 TEXT,
            md5 TEXT,
            file_name TEXT,
            file_size INTEGER,
            last_modified TEXT,
            dir_level INTEGER,
            dir_id INTEGER,
            error TEXT
        )
        """
    )
    run_sql(cur, stmt)

    print("Creating view 'view_filelist'.")
    stmt = dedent(
        """
        CREATE VIEW view_filelist AS
            SELECT
                a.id,
                a.sha1,
                a.md5,
                a.file_name,
                a.file_size,
                a.last_modified,
                a.dir_level,
                a.dir_id,
                b.dir_name,
                a.error
            FROM files a
            JOIN directories b
            ON a.dir_id = b.id;
        """
    )
    run_sql(cur, stmt)

    con.commit()
    cur.close()


def db_info_start(con: sqlite3.Connection, opts: AppOptions):
    print("Writing table 'db_info'.")
    cur = con.cursor()
    data = (
        run_dt.strftime("%Y-%m-%d %H:%M:%S"),
        socket.gethostname(),
        opts.scandir,
        opts.title,
        "",
        opts.do_all_paths,
        os.sep,
        db_version,
        app_name,
        app_version,
    )

    stmt = "INSERT INTO db_info VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    run_sql(cur, stmt, data)
    con.commit()
    cur.close()


def db_info_finish(con: sqlite3.Connection, opts: AppOptions):
    print("Updating table 'db_info'.")
    key = run_dt.strftime("%Y-%m-%d %H:%M:%S")
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = con.cursor()
    stmt = f"UPDATE db_info SET finished = '{dt}' WHERE created = '{key}'"
    run_sql(cur, stmt)
    con.commit()
    cur.close()


def db_add_directory(cur: sqlite3.Cursor, dir_id: int, dir_path: str):
    run_sql(
        cur,
        "INSERT INTO directories VALUES (?, ?)",
        (dir_id, dir_path),
    )


def get_output_file_name(opts: AppOptions):
    name = "FileList-{0}-{1}.sqlite".format(
        opts.title, run_dt.strftime("%Y%m%d_%H%M%S")
    )
    return os.path.join(opts.outdir, name)


def get_percent_complete_str(completed, total):
    if completed < 1:
        return "0%"
    if total < 1:
        return "(?)"
    pct = completed / total
    #  Do not return 100% because, for large input values, the result may
    #  display as 100% well before the process is finished.
    if 0.999 < pct:
        return "99.9%"
    return f"{pct:0.1%}"


def main(argv):
    opts = get_opts(argv)
    filelist = []

    print("\nScanning '{0}'.\n".format(opts.scandir))

    for thisDir, subDirs, fileNames in os.walk(opts.scandir):
        for fileName in fileNames:
            fullName = os.path.join(thisDir, fileName)
            filelist.append(fullName)

    print("Getting total file size.")

    total_size = sum(os.path.getsize(fn) for fn in filelist)
    print(f"  {total_size:,}")

    print("Preparing list of files.")
    filelist.sort()

    if filelist:
        outfile = get_output_file_name(opts)

        print(f"Writing '{outfile}'.")

        n_files = len(filelist)

        con = sqlite3.connect(outfile)
        create_tables_and_views(con)
        db_info_start(con, opts)

        cur = con.cursor()

        dirs = {}
        dir_id = 0
        completed_size = 0

        for lst_idx, filename in enumerate(filelist, start=1):
            pct = get_percent_complete_str(completed_size, total_size)
            print(f"{lst_idx:,} of {n_files:,} ({pct}): {filename}")

            fileinfo = get_file_info(filename, opts)

            completed_size += fileinfo.size

            dir_name = prep_text(fileinfo.dir_name)

            if opts.do_all_paths:
                #  Insert all directory paths so even those with no files are
                #  in the 'directories' table.
                dir_split = dir_name.split(os.sep)
                dir_path = dir_split[0]
                if dir_path not in dirs:
                    dir_id += 1
                    dirs[dir_path] = dir_id
                    db_add_directory(cur, dir_id, dir_path)

                for dir_idx in range(1, len(dir_split)):
                    dir = dir_split[dir_idx]
                    dir_path += f"{os.sep}{dir}"
                    if dir_path not in dirs:
                        dir_id += 1
                        dirs[dir_path] = dir_id
                        db_add_directory(cur, dir_id, dir_path)
            else:
                if dir_name not in dirs:
                    dir_id += 1
                    dirs[dir_name] = dir_id
                    db_add_directory(cur, dir_id, dir_name)

            data = (
                lst_idx,
                fileinfo.sha1,
                fileinfo.md5,
                prep_text(fileinfo.file_name),
                fileinfo.size,
                fileinfo.mtime,
                fileinfo.dir_level,
                dirs[dir_name],
                fileinfo.err,
            )
            stmt = "INSERT INTO files VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            run_sql(cur, stmt, data)

            #  Commit along the way when doing a large number of files.
            #  No need for rollback.
            if lst_idx % 1024 == 0:
                print("---")
                con.commit()

        con.commit()
        cur.close()
        print(f"Finished (100%): {n_files:,} files, {completed_size:,} bytes.")
        db_info_finish(con, opts)
        con.close()
    else:
        print(f"No files found in '{opts.scandir}'.")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
