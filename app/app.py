from model import *
from pdf import *
from tags import *
from pathlib import Path
import pandas as pd





        

if __name__ == "__main__":
    documents = list_documents("./data/raw/")
    print("Documents found:", documents)
    texts = extract_text_from_files(documents, "./data/raw/")
    # import tags from data/eval/tags.txt
    tags_path = Path("./data/eval/tags.txt")
    tags = pd.import_csv(tags_path, header=None).squeeze().tolist()
    for doc, content in texts.items():
        print(f"Extracted text from {doc} (length: {len(content)} characters)")
        print(f"Labels: {classify_documents_texts({doc: content}, tags, multi_label=False)}")

