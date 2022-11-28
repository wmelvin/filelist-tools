# filelist-tools


## mkfilelist.py

```
usage: mkfilelist.py [-h] [-o OUTDIR] [-t] [-u] scandir title

Creates a SQLite database containing file information.

positional arguments:
  scandir               Directory path to scan for files.
  title                 Title to use in output file name.

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
usage: filelist_export.py [-h] [-o OUTDIR] db_file

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
```

---
