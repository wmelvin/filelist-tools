# filelist-tools

Tools for creating and working with a *filelist*. A filelist is a simple table of information about each file found under a specified directory path. It **includes** the File Name, Directory Path, Last Modified timestamp, File Size, and SHA1 and MD5 hashes for each file. It **does not** include detailed metadata such as file type (other than the file extension), extracted thumbnails, EXIF data for images, ID3 data for audio, etc. There are other applications available for building detailed file catalogs.

This set of tools was built to replace earlier versions that created one or more CSV files.

## mkfilelist.py

This is the "scanner" utility that creates a filelist as a SQLite database file. It does not require any modules not in the Python Standard Library so it can be used standalone on any host with Python installed `(TODO: minimum version?)`.

Having the data in a SQLite file affords using tools such as [DB Browser for SQLite](https://sqlitebrowser.org/) to run queries on the data.

#### Command-line Usage

```
usage: mkfilelist.py [-h] [-o OUTDIR] [-t] scandir title

Scans a specified directory path and creates a SQLite database containing some
basic information about each file: File name, Directory path, Last Modified
timestamp, Size, SHA1 and MD5 hashes.

positional arguments:
  scandir               Directory path to scan for files. The scan is always
                        recursive, so all files in any sub-directories of the
                        specified path are included.
  title                 Title to identify the filelist. The title is used in
                        the name of the output file.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTDIR, --output-to OUTDIR
                        Directory in which to create the output file.
                        Optional. By default the output file is created in the
                        currrent working directory.
  -t, --trim-parent     Trim parent directory from scandir in output.
```

## filelist_export.py

This utility reads a SQLite database file, created by `mkfilelist.py`, and writes CSV files. Currently, the CSV files it writes match the layout of those created by an earlier utility script. This makes it easy to use a diff-tool to see that the old and new tools create the same output. It also lets one work with the data in *LibreOffice Calc* or *Excel* as was done with the CSV files produced by the earlier tools. More output formats may be added later.

#### Command-line Usage

```
usage: filelist_export.py [-h] [-o OUTDIR] [--fullname] [--alt] db_file

Export data from a SQLite database created by 'mkfilelist.py'.

positional arguments:
  db_file               Name of SQLite database file created by
                        'mkfilelist.py'. Include the full path to the file
                        unless it is in the current working directory.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTDIR, --output-to OUTDIR
                        Directory in which to create output files. Optional.
                        By default the output is created in the current
                        working directory.
  --fullname            Also create the 'FullNames' CSV file.
  --alt                 Also create the 'Alt' (wide) CSV file.
```

---

#### TODO:

- Build an application-specific UI tool for browsing, querying, and merging filelists.
