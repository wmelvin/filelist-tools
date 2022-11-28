# filelist-tools


## mkfilelist.py

```
usage: mkfilelist.py [-h] [-o OUTDIR] [-t] [-u] scandir title

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
  -u, --used-dirs-only  Only save directory paths for directories that have
                        files. By default, all parent paths of a file's parent
                        directory are stored.
```

## filelist_export.py

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
                        By default the output is created in the currrent
                        working directory.
  --fullname            Also create the 'FullNames' CSV file.
  --alt                 Also create the 'Alt' (wide) CSV file.
```

---
