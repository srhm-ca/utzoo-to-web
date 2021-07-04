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
    metadata["newsgroup"] = re.search(r"([\w]*\.+[\w.]*)", groups).group(0)
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
    db["map"] = []
    for mail in files:
        try:
            metadata = info(mail)
            db["map"].append(metadata["newsgroup"].split("."))
            key = crawl(db["map"][-1:][0], db)
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


def write_posts(path, key):
    file = open("output/" + path + ".html", "w")
    for thread in key:
        for x, response in enumerate(key[thread]):
            metadata = info(response)
            length = metadata.pop("length")
            if x > 0:
                file.write("<blockquote>")
            for value in metadata:
                file.write("<b>"
                           + value + ": </b>" + str(metadata[value])
                           + "<br>")
            file.write("<br>")
            for y, line in enumerate(response.splitlines()):
                if y <= length:
                    pass
                elif line == "" and response.splitlines()[y - 1] != "":
                    file.write("<br><br>")
                elif re.search(r"writes:|[Ii]n [Aa]rticle|^[>]|~\|", line):
                    file.write(
                        "<blockquote><em>" + line + "</em></blockquote> ")
                else:
                    file.write("</em>" + line + " ")
            if x > 0:
                file.write("</blockquote>")
        file.write("<hr>")
    file.close()


def generate(db):
    for path in db["map"]:
        path.append("threads")
        key = crawl(path, db)
        write_posts("_".join(path), key)


if __name__ == "__main__":
    args = get_arg()
    if not Path(".tmp").exists():
        extract(args.dir)
    files = scrape(".tmp")
    db = populate(files)
    generate(db)
    quit()
