import tarfile
import argparse
import re
from pathlib import Path


def get_arg():
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="target directory")
    args = parser.parse_args()
    return args


def extract(path):
    for file in Path(path).iterdir():
        tarfile.open(file, "r:gz").extractall(".tmp")


def scrape(path):
    files = []
    for file in list(Path(path).rglob("*")):
        if file.is_file():
            try:
                files.append(file.read_text())
            except UnicodeDecodeError:
                pass
    return files


def get_metadata(target):
    metadata = []
    newsgroups = re.search(r"(Newsgroups:.*)", target).group(0)
    subject = re.search(r"(Subject:.*)", target).group(0)
    metadata.append(re.search(r"([\w]*\.+[\w.]*)", newsgroups).group(0))
    metadata.append(subject[9:])
    return metadata


def crawl(path, key):
    if not path[0] in key:
        key[path[0]] = {}
    if len(path) > 1:
        key = crawl(path[1:], key[path[0]])
    else:
        key = key[path[0]]
    return key


def populate(files):
    db = {}
    for mail in files:
        try:
            metadata = get_metadata(mail)
            key = crawl(metadata[0].split("."), db)
            if "threads" not in key:
                key["threads"] = {}
            key = key["threads"]
            if not re.search(r"^[Rr][Ee]:", metadata[1]):
                key[metadata[1]] = [mail]
            else:
                if metadata[1][4:] in key:
                    key[metadata[1][4:]].append(mail)
        except AttributeError:
            pass
    return db


def generate(db):
    index = open("test.html", "w")
    key = crawl(["alt", "hypertext", "threads"], db)
    for thread in key:
        text = re.sub(r"\n", "<br>", str(key[thread]))
        index.write(text + "<hr>")


if __name__ == "__main__":
    args = get_arg()
    if not Path(".tmp").exists():
        extract(args.dir)
    files = scrape(".tmp")
    db = populate(files)
    generate(db)
    quit()
