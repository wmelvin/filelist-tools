#!/usr/bin/env python3

import argparse
import hashlib
import os
import socket
import sqlite3
import stat
import sys
import time
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import NamedTuple

app_name = Path(__file__).name

app_version = "2024.01.1"

db_version = 1

log_file_name = None


class AppOptions(NamedTuple):
    scandir: str
    outdir: str
    outfilename: str
    do_overwrite : bool
    dirname_start: int
    title: str
    log_path: str


class FileInfo(NamedTuple):
    file_name: str
    dir_name: str
    dir_level: int
    sha1: str
    md5: str
    size: int
    mtime: str
    err: str


run_dt = datetime.now()
start_dt = run_dt


def write_log(message: str):
    if log_file_name is None:
        return
    with Path(log_file_name).open("a") as f:
        f.write(
            "[{}]: {}\n".format(
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), message
            )
        )


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
        "-n",
        "--name",
        dest="outfilename",
        action="store",
        help="Name of the output file to create. Optional. "
        "By default the output file is named using the title and a current "
        "date_time tag. An existing file with the same name will not be "
        "overwritten unless the --force option is used.",
    )

    ap.add_argument(
        "--force",
        dest="do_overwrite",
        action="store_true",
        help="Allow an existing output file to be overwritten.",
    )

    ap.add_argument(
        "-t",
        "--trim-parent",
        dest="trim_parent",
        action="store_true",
        help="Trim parent directory from scandir in output.",
    )

    ap.add_argument(
        "--no-log",
        dest="no_log",
        action="store_true",
        help="Do not create a log file.",
    )

    return ap.parse_args(argv[1:])


def get_opts(argv):
    args = get_args(argv)

    if not Path(args.scandir).exists():
        sys.stderr.write(f"\nPath not found (scandir): {args.scandir}\n")
        sys.exit(1)

    outdir = args.outdir
    if outdir:
        if not Path(outdir).exists():
            sys.stderr.write(f"\nPath not found (outdir): {outdir}\n")
            sys.exit(1)
    else:
        outdir = str(Path.cwd())

    dirname_start = len(str(Path(args.scandir).parent)) + 1 if args.trim_parent else 0

    title = str(args.title).replace(" ", "_")

    if args.outfilename:
        dn, fn = os.path.split(args.outfilename)
        if dn:
            if args.outdir:
                sys.stderr.write(
                    "\nDo not use outdir (-o, --output-to) when including the "
                    "directory in outfilename (--name).\n"
                )
                sys.exit(1)
            outdir = dn
        check_fn = Path(outdir) / fn
        if check_fn.exists() and not args.do_overwrite:
            sys.stderr.write(f"\nOutput file already exists: {check_fn}\n")
            sys.exit(1)
        outfilename = fn
    else:
        outfilename = None

    log_path = None if args.no_log else Path(outdir) / "mkfilelist.log"

    return AppOptions(
        args.scandir,
        outdir,
        outfilename,
        args.do_overwrite,
        dirname_start,
        title,
        log_path,
    )


def get_hashes(file_name: str):
    """
    Returns a tuple as (sha1, md5, err):.
    """
    BUFFER_SIZE = 65535
    md5 = hashlib.md5()  # noqa: S324
    sha1 = hashlib.sha1()  # noqa: S324
    try:
        with Path(file_name).open("rb") as f:
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
    assert isinstance(file_name, str)  # noqa: S101
    filesize = 0
    mtime = 0
    sha1 = ""
    md5 = ""
    err_str = ""
    dir_level = 0

    p = Path(file_name)
    # dir_name, base_name = os.path.split(file_name)

    dir_name = str(p.parent)[opts.dirname_start :]

    # file_mode = os.lstat(file_name).st_mode
    file_stat = p.stat()
    file_mode = file_stat.st_mode

    if stat.S_ISFIFO(file_mode):
        err_str = "(named pipe)"

    if stat.S_ISLNK(file_mode):
        err_str = "(link)"

    if len(err_str) == 0:
        # filesize = os.path.getsize(file_name)
        filesize = file_stat.st_size

        mtime = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(file_stat.st_mtime)
        )

        if filesize == 0:
            err_str = "(empty file)"
        else:
            sha1, md5, err_str = get_hashes(file_name)

        dir_level = dir_name.count(os.path.sep)

    return FileInfo(
        p.name, dir_name, dir_level, sha1, md5, filesize, mtime, err_str
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
        os.sep,
        db_version,
        app_name,
        app_version,
    )

    stmt = "INSERT INTO db_info VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"
    run_sql(cur, stmt, data)
    con.commit()
    cur.close()


def db_info_finish(con: sqlite3.Connection, opts: AppOptions):
    print("Updating table 'db_info'.")
    key = run_dt.strftime("%Y-%m-%d %H:%M:%S")
    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = con.cursor()
    stmt = "UPDATE db_info SET finished = '{}' WHERE created = '{}'".format(dt, key)  # noqa: S608
    run_sql(cur, stmt)
    con.commit()
    cur.close()


def db_add_directory(cur: sqlite3.Cursor, dir_id: int, dir_path: str):
    run_sql(
        cur,
        "INSERT INTO directories VALUES (?, ?)",
        (dir_id, dir_path),
    )


def get_output_file_path(opts: AppOptions) -> Path:
    if opts.outfilename is None:
        name = "FileListDb-{0}-{1}.sqlite".format(
            opts.title, run_dt.strftime("%Y%m%d_%H%M%S")
        )
    else:
        name = opts.outfilename
    return Path(opts.outdir) / name


def get_percent_complete(completed, total):
    if total < 1:
        return (0.0, "(?)")
    if completed < 1:
        return (0.0, "0%")
    pct = completed / total
    #  Do not return 100% because, for large input values, the result may
    #  display as 100% well before the process is finished.
    if pct > 0.999:
        return pct, "99.9%"
    return (pct, "{:0.1%}".format(pct))


def get_est_finish(pct_complete):
    if pct_complete == 0.0:
        return "(?)"
    now_dt = datetime.now()
    est_done = start_dt + ((now_dt - start_dt) / pct_complete)
    return est_done.strftime("%H:%M:%S")


def main(argv):
    opts = get_opts(argv)
    global log_file_name
    log_file_name = opts.log_path
    has_warnings = False

    write_log("START {} (version {})".format(app_name, app_version))
    print("\n{} (version {})\n".format(app_name, app_version))

    write_log("SCAN '{0}'".format(opts.scandir))
    print("Scanning '{0}'.\n".format(opts.scandir))

    filelist = []
    total_size = 0

    for this_dir, _, file_names in os.walk(opts.scandir):
        for file_name in file_names:
            full_path = Path(this_dir) / file_name
            if full_path.is_file():
                filelist.append(str(full_path))
                total_size += full_path.stat().st_size
            else:
                has_warnings = True
                write_log(f"WARNING: Not a valid file: '{full_path}'")

    # print("Getting total file size.")

    # total_size = sum(os.path.getsize(fn) for fn in filelist)

    write_log("Total size: {:,}".format(total_size))
    print("  {:,}".format(total_size))

    print("Preparing list of files.")
    filelist.sort()

    if filelist:
        outfile = get_output_file_path(opts)

        print("Writing '{}'.".format(outfile))

        write_log("Writing '{}'".format(outfile))

        if outfile.exists():
            if opts.do_overwrite:
                write_log("Overwrite existing file.")
                outfile.unlink()
            else:
                sys.stderr.write("\nCannot replace existing output file.\n")
                sys.exit(1)

        n_files = len(filelist)

        con = sqlite3.connect(outfile)
        create_tables_and_views(con)
        db_info_start(con, opts)

        cur = con.cursor()

        dirs = {}
        dir_id = 0
        completed_size = 0

        #  Set start_dt here so initial scan time is not included when
        #  calculating the estimated finish time.
        global start_dt
        start_dt = datetime.now()

        for lst_idx, filename in enumerate(filelist, start=1):
            pct, pct_str = get_percent_complete(completed_size, total_size)
            est = "estimated finish at {}".format(get_est_finish(pct))
            print(
                "[ File {0:,} of {1:,} ({2}) - {3} ]\n{4}".format(
                    lst_idx, n_files, pct_str, est, filename
                )
            )

            fileinfo = get_file_info(filename, opts)

            completed_size += fileinfo.size

            if fileinfo.dir_name not in dirs:
                dir_id += 1
                dirs[fileinfo.dir_name] = dir_id
                db_add_directory(cur, dir_id, fileinfo.dir_name)

            data = (
                lst_idx,
                fileinfo.sha1,
                fileinfo.md5,
                fileinfo.file_name,
                fileinfo.size,
                fileinfo.mtime,
                fileinfo.dir_level,
                dirs[fileinfo.dir_name],
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

        #  Include initial scan in total run time.
        run_time = datetime.now() - run_dt

        msg = (
                "Finished at {0} (100%): {1:,} files, {2:,} bytes. "
                "Run time {3}"
            ).format(
            datetime.now().strftime("%H:%M:%S"),
            n_files,
            completed_size,
            run_time,
        )

        write_log(msg)
        print("\n{}\n".format(msg))

        db_info_finish(con, opts)

        con.close()

        print("Data written to '{}'.\n".format(outfile))
        if has_warnings:
            print("WARNINGS written to '{}'.".format(log_file_name))
    else:
        write_log("No files found.")
        print("\nNo files found in '{}'.\n".format(opts.scandir))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
