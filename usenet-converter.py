#!/usr/bin/env python3
import tarfile
import argparse
import re
from pathlib import Path


def get_arg():
    """Retrieve arguments from command-line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("dir", help="target directory")
    args = parser.parse_args()
    return args


def extract(path):
    """Extract all .tar.gz in directory"""
    for file in Path(path).iterdir():
        tarfile.open(file, "r:gz").extractall(".tmp")


def scrape(path):
    """Recursively scrape text from a directory"""
    files = []
    for file in list(Path(path).rglob("*")):
        if file.is_file():
            try:
                files.append(file.read_text())
            except UnicodeDecodeError:
                pass
    return files


def info(target):
    """Return metadata for target article"""
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
    # Should seek to enable support for <1985 articles
    return metadata


def crawl(path, key):
    """Recursively traverse dict tree, return target layer"""
    if not path[0] in key:
        key[path[0]] = {}
    if len(path) > 1:
        key = crawl(path[1:], key[path[0]])
    else:
        key = key[path[0]]
    return key


def populate(files):
    """Create and populate dict database with usenet articles"""
    db = {}
    db["map"] = []
    for mail in files:
        try:
            metadata = info(mail)
            key = crawl(metadata["newsgroup"].split("."), db)
            if "threads" not in key:
                key["threads"] = {}
            key = key["threads"]
            if not re.search(r"^[Rr][Ee]:", metadata["subject"]):
                key[metadata["subject"]] = [mail]
            else:
                if metadata["subject"][4:] in key:
                    key[metadata["subject"][4:]].append(mail)
            if metadata["newsgroup"].split(".") not in db["map"]:
                db["map"].append((metadata["newsgroup"].split(".")))
                db["map"].sort()
        except AttributeError:
            pass
    return db


def write_posts(path, key):
    """Write out dict tree layer to HTML file"""
    file = open("output/" + path + ".html", "w")
    file.write("<!DOCTYPE html>")
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
                elif re.search(r"writes:|[Ii]n [Aa]rticle|^[>]|~\|\|>|\|", line):
                    file.write(
                        "<blockquote><em>" + line + "</em></blockquote> ")
                else:
                    file.write(line + " ")
            if x > 0:
                file.write("</blockquote>")
        file.write("<hr>")
    file.close()


def generate(db):
    """Generate HTML files & index for db"""
    index = open("output/index.html", "w")
    index.write("<!DOCTYPE html><table style=\"width:50%\">")
    for path in db["map"]:
        path.append("threads")
        key = crawl(path, db)
        write_posts("_".join(path[:-1]), key)
        index.write("<tr><th style=\"text-align:left;\">"
                    + "<a href=\"" + "_".join(path[:-1]) + ".html\">"
                    + ".".join(path[:-1]) + "</th><th>" + str(len(key))
                    + " threads</th></tr>")
    index.write("</table>")
    index.close()


if __name__ == "__main__":
    args = get_arg()
    if not Path(".tmp").exists():
        extract(args.dir)
    files = scrape(".tmp")
    db = populate(files)
    generate(db)
    quit()
