import pandas as pd
import json
import os
import random
from sklearn.model_selection import train_test_split
from collections import Counter

# ===============================
# 1️⃣ Load CSV
# ===============================
df = pd.read_csv("first_annotations.csv")  
# required columns: sentence, entity1, entity1_label, entity2, entity2_label, relation

# ===============================
# 2️⃣ Convert CSV to SPERT JSON
# ===============================
data = []
entity_types = set()
relation_types = set()

for _, row in df.iterrows():
    sentence = row['sentence']
    tokens = sentence.split()  # basic whitespace tokenization

    # Find start indices of entities
    e1_tokens = row['entity1'].split() if isinstance(row['entity1'], str) else []
    e2_tokens = row['entity2'].split() if isinstance(row['entity2'], str) else []

    def find_entity_index(tokens, entity_tokens):
        for i in range(len(tokens)):
            if tokens[i:i+len(entity_tokens)] == entity_tokens:
                return i
        return None

    e1_start = find_entity_index(tokens, e1_tokens) if e1_tokens else None
    e2_start = find_entity_index(tokens, e2_tokens) if e2_tokens else None

    entities = []
    relations = []

    if e1_start is not None:
        entities.append({
            "id": len(entities),
            "start": e1_start,
            "end": e1_start + len(e1_tokens),
            "type": row['entity1_label']
        })
        entity_types.add(row['entity1_label'])

    if e2_start is not None:
        entities.append({
            "id": len(entities),
            "start": e2_start,
            "end": e2_start + len(e2_tokens),
            "type": row['entity2_label']
        })
        entity_types.add(row['entity2_label'])

    if len(entities) == 2 and isinstance(row['relation'], str) and row['relation'].strip():
        relations.append({
            "head": 0,
            "tail": 1,
            "type": row['relation'],
            "direction": "L2R"
        })
        relation_types.add(row['relation'])

    data.append({
        "tokens": tokens,
        "entities": entities,
        "relations": relations
    })

# ===============================
# 3️⃣ Split into train/dev/test
# ===============================
os.makedirs("data", exist_ok=True)

# Stratify by relation type if possible
stratify_labels = []
for ex in data:
    if ex.get("relations"):
        stratify_labels.append(ex["relations"][0]["type"])
    else:
        stratify_labels.append("NoRelation")

if len(set(stratify_labels)) > 1:
    train_data, temp_data, _, _ = train_test_split(
        data, stratify_labels, test_size=0.2, random_state=42, stratify=stratify_labels
    )
else:
    train_data, temp_data = train_test_split(data, test_size=0.2, random_state=42)

dev_data, test_data = train_test_split(temp_data, test_size=0.5, random_state=42)

splits = {"train.json": train_data, "dev.json": dev_data, "test.json": test_data}
for filename, split_data in splits.items():
    path = os.path.join("data", filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(split_data, f, ensure_ascii=False, indent=2)

# ===============================
# 4️⃣ Generate types.json
# ===============================
types = {
    "entities": {},
    "relations": {}
}

for et in sorted(entity_types):
    types["entities"][et] = {
        "short": et,
        "verbose": et
    }

for rt in sorted(relation_types):
    types["relations"][rt] = {
        "short": rt,
        "verbose": rt,
        "symmetric": False
    }

with open("data/types.json", "w", encoding="utf-8") as f:
    json.dump(types, f, ensure_ascii=False, indent=2)

# ===============================
# 5️⃣ Print relation distribution
# ===============================
def count_relations(dataset):
    counter = Counter()
    for ex in dataset:
        for r in ex.get("relations", []):
            counter[r["type"]] += 1
    return dict(counter)

print("Train relations:", count_relations(train_data))
print("Dev relations:", count_relations(dev_data))
print("Test relations:", count_relations(test_data))
print("Generated types.json with", len(entity_types), "entity types and", len(relation_types), "relation types.")
