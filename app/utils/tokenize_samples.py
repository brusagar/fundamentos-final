import json
import spacy
import argparse
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Tokenize text files for SpERT prediction')
    parser.add_argument('--input', required=True, help='Input text file path')
    parser.add_argument('--output', default="spert/data/raw_text.json", help='Output JSON file path')
    return parser.parse_args()

def tokenize_text_file(input_file: str, output_file: str):
    """Tokenize a text file and save it in SpERT format"""
    
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read().strip()
    
    if not text:
        raise ValueError(f"Input file is empty: {input_file}")
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        raise RuntimeError("SpaCy English model not found. Please install with: python -m spacy download en_core_web_sm")
    
    tokenized_data = []
    
    doc = nlp(text)
    for sent in doc.sents:
        tokens = [token.text for token in sent]
        if len(tokens) >= 3:
            tokenized_data.append({
                "tokens": tokens,
                "entities": [],
                "relations": []
            })
    
    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True, parents=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tokenized_data, f, ensure_ascii=False, indent=2)
    
    return len(tokenized_data)

def main():
    args = parse_arguments()
    
    try:
        num_sentences = tokenize_text_file(args.input, args.output)
        print(f"Successfully tokenized {num_sentences} sentences")
        print(f"Input: {args.input}")
        print(f"Output: {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

