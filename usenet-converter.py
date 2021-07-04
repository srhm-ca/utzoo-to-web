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


def info(target):
    metadata = {}
    groups = re.search(r"(Newsgroups:.*)", target).group(0)
    subject = re.search(r"(Subject:.*)", target).group(0)
    date = re.search(r"(Date:.*)", target).group(0)
    author = re.search(r"(From:.*)", target).group(0)
    metadata["newsgroups"] = re.search(r"([\w]*\.+[\w.]*)", groups).group(0)
    metadata["subject"] = subject[9:]
    metadata["author"] = author[6:]
    metadata["date"] = date[6:]
    for x, line in enumerate(target.splitlines()):
        if not re.search(r".*:.*", line):
            metadata["length"] = x
            break
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
            metadata = info(mail)
            key = crawl(metadata["newsgroups"].split("."), db)
            if "threads" not in key:
                key["threads"] = {}
            key = key["threads"]
            if not re.search(r"^[Rr][Ee]:", metadata["subject"]):
                key[metadata["subject"]] = [mail]
            else:
                if metadata["subject"][4:] in key:
                    key[metadata["subject"][4:]].append(mail)
        except AttributeError:
            pass
    return db


def generate(db):
    index = open("test.html", "w")
    key = crawl(["rec", "music", "gaffa", "threads"], db)
    for thread in key:
        for x, response in enumerate(key[thread]):
            metadata = info(response)
            length = metadata.pop("length")
            if x > 0:
                index.write("<blockquote>")
            for value in metadata:
                index.write("<b>"
                            + value + ": </b>" + str(metadata[value])
                            + "<br>")
            index.write("<br>")
            for y, line in enumerate(response.splitlines()):
                if y <= length:
                    pass
                elif line == "" and response.splitlines()[y - 1] != "":
                    index.write("<br><br>")
                else:
                    index.write(line + " ")
            if x > 0:
                index.write("</blockquote>")
        index.write("<hr>")


if __name__ == "__main__":
    args = get_arg()
    if not Path(".tmp").exists():
        extract(args.dir)
    files = scrape(".tmp")
    db = populate(files)
    generate(db)
    quit()
