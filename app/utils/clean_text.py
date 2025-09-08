import re
from tqdm import tqdm

CLEAN_RE = re.compile(r"\d+|[_*#=]+")

def preprocess_stream(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as fin, \
         open(output_file, "w", encoding="utf-8") as fout:

        inside_book = False
        for line in tqdm(fin, desc="Cleaning text"):
            if "START OF THE PROJECT GUTENBERG EBOOK" in line:
                inside_book = True
                continue
            if "END OF THE PROJECT GUTENBERG EBOOK" in line:
                break

            if not inside_book:
                continue

            line = CLEAN_RE.sub("", line)
            line = re.sub(r"[ \t]+", " ", line).strip()

            if line:
                fout.write(line + "\n")
