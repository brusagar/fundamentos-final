
import spacy
import json
import csv
import re
import argparse
import gc
from typing import List, Dict, Tuple, Optional
from pathlib import Path

try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False

try:
    # neuralcoref is broken on Python 3.11+, use spacy-experimental instead
    import spacy
    import spacy_experimental
    SPACY_EXPERIMENTAL_AVAILABLE = True
except ImportError:
    SPACY_EXPERIMENTAL_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Print availability warnings only once
if not STANZA_AVAILABLE:
    print("Warning: Stanza not available. Install with: pip install stanza")
if not SPACY_EXPERIMENTAL_AVAILABLE:
    print("Warning: spaCy experimental not available. Install with: pip install spacy-experimental")
if not TRANSFORMERS_AVAILABLE:
    print("Warning: Transformers not available. Install with: pip install transformers torch")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Process text for NER and relation extraction')
    parser.add_argument('--input', default="text.txt", help='Input text file')
    parser.add_argument('--output', default="relation_candidates_good.csv", help='Output CSV file')
    parser.add_argument('--patterns', default="patterns.json", help='Patterns JSON file')
    parser.add_argument('--stanza-coref', action='store_true', help='Use Stanza coreference resolution (requires more memory)')
    parser.add_argument('--spacy-experimental', action='store_true', help='Use spaCy experimental coreference resolution')
    parser.add_argument('--transformers-coref', action='store_true', help='Use Transformers-based coreference resolution')
    parser.add_argument('--no-coref', action='store_true', help='Skip coreference resolution entirely')
    return parser.parse_args()

def main():
    """Main function to run the NER and relation extraction pipeline."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Use command line arguments or defaults
    INPUT_FILE = args.input
    OUTPUT_FILE = args.output
    PATTERNS_FILE = args.patterns
    
    print("=" * 60)
    print("NER PREPROCESSING PIPELINE STARTED")
    print("=" * 60)
    
    # Check if input file exists
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"ERROR: Input file {INPUT_FILE} not found.")
        return
    
    # Load and clean text
    print(f"[1/5] Loading text from {INPUT_FILE}...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"[2/5] Cleaning text...")
    text = clean_text(text)
    print(f"      Text cleaned. Length: {len(text)} characters.")
    
    # Apply coreference resolution
    print("[3/5] Applying coreference resolution...")
    if args.no_coref:
        print("      Skipping coreference resolution...")
        resolved_text = text  # Use original text without coreference resolution
    elif args.stanza_coref:
        print("      Using Stanza coreference resolution...")
        resolved_text = safe_coref_resolution(text, "stanza")
    elif args.spacy_experimental:
        print("      Using spaCy experimental coreference resolution...")
        resolved_text = safe_coref_resolution(text, "spacy_experimental")
    elif args.transformers_coref:
        print("      Using Transformers coreference resolution...")
        resolved_text = safe_coref_resolution(text, "transformers")
    else:
        # Default behavior: no coreference resolution
        print("      Skipping coreference resolution (default)...")
        resolved_text = text
    print(f"      Coreference processing completed.")
    
    # Load spaCy model
    print("[4/5] Loading spaCy model...")
    nlp = load_spacy_model()
    print("      spaCy model loaded successfully.")
    
    # Load and add patterns if available
    patterns = load_patterns(PATTERNS_FILE)
    if patterns:
        print(f"      Adding {len(patterns)} custom patterns...")
        ruler = nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(patterns)
        print("      Custom patterns added successfully.")
    else:
        print("      No custom patterns to add.")
    
    # Process resolved text with NER
    print("[5/5] Processing text with NER...")
    resolved_doc = nlp(resolved_text)
    print("      NER processing completed.")
    
    # Generate relation candidates
    print("Generating relation candidates...")
    rows = generate_relation_candidates(resolved_doc.sents)
    print(f"      Generated {len(rows)} relation candidates.")
    
    # Save to CSV
    print(f"Saving results to {OUTPUT_FILE}...")
    save_to_csv(rows, OUTPUT_FILE)
    
    print("=" * 60)
    print(f"SUCCESS: Exported {len(rows)} sentences with at least one NE to {OUTPUT_FILE}")
    print("=" * 60)

def clean_text(text: str) -> str:
    """
    Remove unwanted characters and patterns from the text.
    Args:
        text (str): Raw input text
    Returns:
        str: Cleaned text
    """
    # Define patterns to remove
    patterns = [
        r'\[\d+\]',          # Remove citation numbers like [63]
        r'PLATE [IVXLC]+',   # Remove plate references like PLATE XII
        r'PLATES [IVXLC]+',  # Remove plate references like PLATES XII
        r'Fig\. \d+',        # Remove figure references like Fig. 12
        r'\(\d+\)',          # Remove parenthetical numbers like (123)
        r'§+',               # Remove section symbols
        r'\*+',              # Remove asterisks
        r'_{2,}',           # Remove multiple underscores
        r'={2,}',           # Remove multiple equal signs
    ]
    
    # Combine all patterns
    combined_pattern = '|'.join(patterns)
    
    # Remove all matched patterns
    cleaned_text = re.sub(combined_pattern, '', text)
    
    # Remove extra whitespace
    cleaned_text = ' '.join(cleaned_text.split())
    
    return cleaned_text


def chunk_text(text: str, max_chunk_size: int = 5000) -> List[str]:
    """
    Split text into smaller chunks for safer processing.
    Tries to split on sentence boundaries when possible.
    """
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    sentences = re.split(r'[.!?]+\s+', text)
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed chunk size
        if len(current_chunk) + len(sentence) > max_chunk_size:
            if current_chunk:  # Save current chunk if not empty
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:  # Single sentence too long, force split
                # Split long sentence into smaller parts
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 > max_chunk_size:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            # Single word too long, just add it
                            chunks.append(word)
                    else:
                        temp_chunk += " " + word if temp_chunk else word
                if temp_chunk:
                    current_chunk = temp_chunk
        else:
            current_chunk += ". " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def safe_coref_resolution(text: str, method: str) -> str:
    """
    Safely apply coreference resolution with chunking for large texts.
    """
    # Define size limits for each method
    size_limits = {
        "stanza": 30000,
        "spacy_experimental": 50000,
        "transformers": 20000
    }
    
    max_size = size_limits.get(method, 50000)
    
    if len(text) <= max_size:
        # Text is small enough, process directly
        if method == "stanza":
            return stanza_coref_resolution(text)
        elif method == "spacy_experimental":
            return spacy_experimental_coref_resolution(text)
        elif method == "transformers":
            return transformers_coref_resolution(text)
        else:
            return text
    else:
        # Text is too large, process in chunks
        print(f"      Text is large ({len(text)} chars), processing in chunks...")
        chunks = chunk_text(text, max_size)
        resolved_chunks = []
        
        for i, chunk in enumerate(chunks):
            print(f"      Processing chunk {i+1}/{len(chunks)}...")
            try:
                if method == "stanza":
                    resolved_chunk = stanza_coref_resolution(chunk)
                elif method == "spacy_experimental":
                    resolved_chunk = spacy_experimental_coref_resolution(chunk)
                elif method == "transformers":
                    resolved_chunk = transformers_coref_resolution(chunk)
                else:
                    resolved_chunk = chunk
                resolved_chunks.append(resolved_chunk)
            except Exception as e:
                print(f"      Warning: Chunk {i+1} failed, using original text: {e}")
                resolved_chunks.append(chunk)
        
        return " ".join(resolved_chunks)


def stanza_coref_resolution(text: str) -> str:
    """
    Proper coreference resolution using Stanza.
    Memory-safe implementation with proper cleanup.
    """
    nlp_stanza = None
    try:
        # Check if Stanza is available
        if not STANZA_AVAILABLE:
            print("      Stanza not available, falling back to original text...")
            return text
        
        # Limit text size to prevent crashes
        if len(text) > 50000:  # Limit to ~50KB
            print("      Text too large for Stanza, using original text...")
            return text
        
        # Initialize Stanza pipeline with coreference resolution
        print("      Initializing Stanza pipeline...")
        nlp_stanza = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma,ner,coref', use_gpu=False)
        
        # Process the text
        print("      Processing text with Stanza...")
        doc = nlp_stanza(text)
        
        # Resolve coreferences
        resolved_text = []
        
        # Get sentences and tokens
        sentences = doc.sentences
        
        # Create a mapping of token positions to resolved mentions
        token_replacements = {}
        
        if hasattr(doc, 'coref') and doc.coref:
            print(f"      Found {len(doc.coref)} coreference chains...")
            for coref_chain in doc.coref:
                # Find the representative mention (usually the first or longest)
                representative = None
                for mention in coref_chain:
                    if representative is None or len(mention.text) > len(representative.text):
                        representative = mention
                
                # Replace all other mentions with the representative
                for mention in coref_chain:
                    if mention != representative:
                        # Map this mention's position to the representative text
                        start_pos = mention.start_char
                        end_pos = mention.end_char
                        token_replacements[(start_pos, end_pos)] = representative.text
        
        # Apply replacements to the original text
        resolved_text = text
        # Sort by position (descending) to avoid position shifts when replacing
        for (start, end), replacement in sorted(token_replacements.items(), reverse=True):
            resolved_text = resolved_text[:start] + replacement + resolved_text[end:]
        
        return resolved_text
        
    except Exception as e:
        print(f"      Warning: Stanza coreference resolution failed: {e}")
        print("      Falling back to original text...")
        return text
    
    finally:
        # Memory cleanup
        if nlp_stanza is not None:
            del nlp_stanza
        gc.collect()
        print("      Memory cleanup completed.")


def spacy_experimental_coref_resolution(text: str) -> str:
    """
    Coreference resolution using spaCy experimental features.
    More stable than neuralcoref and works with modern Python versions.
    """
    try:
        # Check if spaCy experimental is available
        if not SPACY_EXPERIMENTAL_AVAILABLE:
            print("      spaCy experimental not available, falling back to original text...")
            return text
        
        # Limit text size to prevent crashes
        if len(text) > 80000:  # Limit to ~80KB
            print("      Text too large for spaCy experimental, using original text...")
            return text
        
        # Load spaCy model with experimental coreference
        print("      Loading spaCy with experimental coreference...")
        nlp = spacy.load('en_core_web_sm')
        
        # Add experimental coreference component
        nlp.add_pipe("experimental_coref")
        
        # Process the text
        print("      Processing text with spaCy experimental...")
        doc = nlp(text)
        
        # Apply coreference resolution
        resolved_text = text
        
        # Get coreference clusters and resolve them
        if doc.spans.get("coref_clusters"):
            clusters = doc.spans["coref_clusters"]
            print(f"      Found {len(clusters)} coreference clusters")
            
            # Simple resolution: replace pronouns with their antecedents
            # This is a basic implementation - spaCy experimental may have better methods
            for cluster in clusters:
                # Find the main mention (usually the longest or first proper noun)
                main_mention = None
                for mention in cluster:
                    if not main_mention or (len(mention.text) > len(main_mention.text) and mention.text[0].isupper()):
                        main_mention = mention
                
                if main_mention:
                    # Replace pronouns in the cluster with the main mention
                    for mention in cluster:
                        if mention != main_mention and mention.text.lower() in ['he', 'she', 'it', 'they', 'him', 'her', 'them']:
                            # Simple replacement (this could be improved)
                            resolved_text = resolved_text.replace(mention.text, main_mention.text)
        else:
            print("      No coreference clusters found")
        
        return resolved_text
            
    except Exception as e:
        print(f"      Warning: spaCy experimental coreference resolution failed: {e}")
        print("      Falling back to original text...")
        return text


def transformers_coref_resolution(text: str) -> str:
    """
    Coreference resolution using Transformers library.
    Uses pre-trained models from HuggingFace.
    """
    try:
        # Check if Transformers is available
        if not TRANSFORMERS_AVAILABLE:
            print("      Transformers not available, falling back to original text...")
            return text
        
        # Limit text size to prevent crashes
        if len(text) > 30000:  # Conservative limit for transformers
            print("      Text too large for Transformers, using original text...")
            return text
        
        # Initialize the coreference resolution pipeline
        print("      Loading Transformers coreference pipeline...")
        # Note: This is a conceptual implementation - actual transformers coref might need different models
        coref_pipeline = pipeline("text2text-generation", model="google/flan-t5-base")
        
        # Create a prompt for coreference resolution
        prompt = f"Resolve all pronouns and coreferences in the following text, replacing them with their actual referents: {text}"
        
        print("      Processing text with Transformers...")
        result = coref_pipeline(prompt, max_length=len(text) + 100, do_sample=False)
        
        resolved_text = result[0]['generated_text']
        print("      Transformers coreference resolution completed")
        return resolved_text
        
    except Exception as e:
        print(f"      Warning: Transformers coreference resolution failed: {e}")
        print("      Falling back to original text...")
        return text


def load_spacy_model() -> spacy.Language:
    """Load and configure the spaCy model."""
    try:
        # Try to load the English model
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("English model not found. Please install it with:")
        print("python -m spacy download en_core_web_sm")
        raise
    
    return nlp


def load_patterns(patterns_file: str) -> List[Dict]:
    """Load entity patterns from JSON file."""
    patterns_path = Path(patterns_file)
    if patterns_path.exists():
        with open(patterns_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print(f"Warning: Patterns file {patterns_file} not found. Continuing without custom patterns.")
        return []


def extract_entities(sent) -> List[Tuple[str, str]]:
    """Extract entities from a sentence, filtering out unwanted types."""
    return [(ent.text, ent.label_) 
            for ent in sent.ents 
            if ent.label_ not in ["CARDINAL", "ORDINAL"]]


def generate_relation_candidates(sentences) -> List[Dict[str, str]]:
    """Generate relation candidates from processed sentences."""
    rows = []
    
    for sent in sentences:
        # Extract entities from the sentence
        ents = extract_entities(sent)
        
        # Keep only sentences with at least 1 NE (after filtering cardinals)
        if len(ents) >= 1:
            if len(ents) >= 2:
                # Generate all possible entity pairs
                for i in range(len(ents)):
                    for j in range(i+1, len(ents)):
                        e1_text, e1_label = ents[i]
                        e2_text, e2_label = ents[j]
                        rows.append({
                            "sentence": sent.text.strip(),
                            "entity1": e1_text,
                            "entity1_label": e1_label,
                            "entity2": e2_text,
                            "entity2_label": e2_label,
                            "relation": ""  # leave blank for annotation
                        })
            else:
                # Sentence has only one NE -> still include for reference (no pair)
                e1_text, e1_label = ents[0]
                rows.append({
                    "sentence": sent.text.strip(),
                    "entity1": e1_text,
                    "entity1_label": e1_label,
                    "entity2": "",
                    "entity2_label": "",
                    "relation": ""
                })
    
    return rows


def save_to_csv(rows: List[Dict[str, str]], output_file: str) -> None:
    """Save relation candidates to CSV file."""
    fieldnames = [
        "sentence", 
        "entity1", "entity1_label",
        "entity2", "entity2_label",
        "relation"
    ]
    
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)



if __name__ == "__main__":
    main()
