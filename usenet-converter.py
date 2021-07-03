import tarfile
import argparse
import re
from pprint import pprint
from pathlib import Path


def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="target directory")
    args = parser.parse_args()
    return args


def extract(path):
    for file in Path(path).iterdir():
        tarfile.open(file, 'r:gz').extractall(".tmp")


def scrape(path):
    files = []
    for file in list(Path(path).rglob('*')):
        if file.is_file():
            try:
                files.append(file.read_text())
            except UnicodeDecodeError:
                pass
    return files


def sort(files):
    db = {}
    for mail in files:
        try:
            groups = re.search(r"(Newsgroups:.*)", mail).group(0)
            group = re.search(r"([\w]*\.+[\w.]*)", groups).group(0)
            x = group.split('.')
            if not x[0] in db:
                db[x[0]] = {}
            try:
                if x[1]:
                    majorkey = db[x[0]]
                    if not x[1] in majorkey:
                        majorkey[x[1]] = {}
            except IndexError:
                pass
            try:
                if x[2]:
                    minorkey = majorkey[x[1]]
                    if not x[2] in minorkey:
                        minorkey[x[2]] = {}
            except IndexError:
                pass
            try:
                if x[3]:
                    smallkey = minorkey[x[2]]
                    if not x[3] in minorkey:
                        smallkey[x[3]] = {}
            except IndexError:
                pass
        except AttributeError:
            pass
    return db


if __name__ == "__main__":
    args = get_arg()
    if not Path('.tmp').exists():
        extract(args.dir)
    files = scrape('.tmp')
    db = sort(files)
    pprint(db)
    quit()
