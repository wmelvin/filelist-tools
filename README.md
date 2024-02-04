# filelist-tools

Tools for creating and working with a *filelist*. A filelist is a simple table of information about each file found under a specified directory path. It **includes** the File Name, Directory Path, Last Modified timestamp, File Size, and SHA1 and MD5 hashes for each file. It **does not** include detailed metadata such as file type (other than the file extension), extracted thumbnails, EXIF data for images, ID3 data for audio, etc. There are other applications available for building detailed file catalogs.

This set of tools was built to replace earlier versions that created one or more CSV files.

## mkfilelist.py

This is the "scanner" utility that creates a filelist as a SQLite database file. It does not require any modules not in the Python Standard Library so it can be used standalone on any host with Python installed `(TODO: minimum version?)`.

Having the data in a SQLite file affords using tools such as [DB Browser for SQLite](https://sqlitebrowser.org/) to run queries on the data.

#### Command-line Usage

```
usage: mkfilelist.py [-h] [-o OUTDIR] [-n OUTFILENAME] [--force] [-t]
                     [--no-log]
                     scandir title

Scans a specified directory path and creates a SQLite database containing some
basic information about each file: File name, Directory path, Last Modified
timestamp, Size, SHA1 and MD5 hashes.

positional arguments:
  scandir               Directory path to scan for files. The scan is always
                        recursive, so all files in any sub-directories of the
                        specified path are included.
  title                 Title to identify the filelist. The title is used in
                        the name of the output file.

options:
  -h, --help            show this help message and exit
  -o OUTDIR, --output-to OUTDIR
                        Directory in which to create the output file.
                        Optional. By default the output file is created in the
                        currrent working directory.
  -n OUTFILENAME, --name OUTFILENAME
                        Name of the output file to create. Optional. By
                        default the output file is named using the title and a
                        current date_time tag. An existing file with the same
                        name will not be overwritten unless the --force option
                        is used.
  --force               Allow an existing output file to be overwritten.
  -t, --trim-parent     Trim parent directory from scandir in output.
  --no-log              Do not create a log file.
```

---

## filelist_export.py

This utility reads a SQLite database file, created by `mkfilelist.py`, and writes CSV files. Currently, the CSV files it writes match the layout of those created by an earlier utility script. This makes it easy to use a diff-tool to see that the old and new tools create the same output. It also lets one work with the data in *LibreOffice Calc* or *Excel* as was done with the CSV files produced by the earlier tools. More output formats may be added later.

#### Command-line Usage

```
usage: filelist_export.py [-h] [-o OUTDIR] [--fullname] [--alt] [--dfn]
                          db_file

Export data from a SQLite database created by 'mkfilelist.py'.

positional arguments:
  db_file               Name of SQLite database file created by
                        'mkfilelist.py'. Include the full path to the file
                        unless it is in the current working directory.

options:
  -h, --help            show this help message and exit
  -o OUTDIR, --output-to OUTDIR
                        Directory in which to create output files. Optional.
                        By default the output is created in the current
                        working directory.
  --fullname            Also create the 'FullNames' CSV file.
  --alt                 Also create the 'Alt' (wide) CSV file.
  --dfn                 Create a CSV file by Directory and FileName where
                        those are the first two columns.
```

---

## filelist_merge.py

This utility reads SQLite database files, created by `mkfilelist.py`, and merges the data into a new SQLite database. Additional files can be appended to an existing *MergeFileLists* database.

#### Command-line Usage

```
usage: filelist_merge.py [-h] [-o OUTDIR] [-n OUTFILENAME] [--force] [-a]
                         [source_files ...]

Merges two or more SQLite databases created by mkfilelist.py.

positional arguments:
  source_files          Files to be merged. Multiple file names are separated
                        by spaces. A single file name may be given in the case
                        of appending to an existing merged database. In that
                        case, the destination file must also be specified in
                        the --name parameter. Also, a Tag (short name for a
                        filelist to use instead of its Title) can be included
                        after a file name using a comma (with no spaces)
                        followed by the tag (filename,tag).

options:
  -h, --help            show this help message and exit
  -o OUTDIR, --output-to OUTDIR
                        Directory in which to create the output file.
                        Optional. By default the output file is created in the
                        currrent working directory.
  -n OUTFILENAME, --name OUTFILENAME
                        Name of the output file to create. Optional. By
                        default the output file is named starting with
                        'MergeFileLists' followed by a current date_time tag.
                        An existing file with the same name will not be
                        overwritten unless the --force option is used.
  --force               Allow an existing output file to be overwritten.
  -a, --append          Append the filelist data to an existing merged
                        database. The destination file name must be specified
                        using the --name parameter.
```

---

#### TODO:

- Build an application-specific UI tool for browsing, querying, and merging filelists.
