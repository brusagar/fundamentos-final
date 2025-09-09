#!/bin/bash
# Fix SpERT compatibility with newer transformers

echo "SpERT Compatibility Fixer"
echo "-------------------------"

# Check if we're in the right directory
if [ ! -d "spert" ]; then
    echo "Error: 'spert' directory not found!"
    echo "Run this from the project root directory."
    exit 1
fi

# Check if spert_trainer.py exists
TRAINER_FILE="spert/spert/spert_trainer.py"
if [ ! -f "$TRAINER_FILE" ]; then
    echo "Error: $TRAINER_FILE not found!"
    echo "Make sure SpERT is properly cloned."
    exit 1
fi

echo "Fixing $TRAINER_FILE..."

# Create a backup
cp "$TRAINER_FILE" "$TRAINER_FILE.backup"
echo "  Created backup"

# Fix AdamW import
if grep -q "from transformers import AdamW, BertConfig" "$TRAINER_FILE"; then
    echo "  Fixing AdamW import..."
    sed -i 's/from transformers import AdamW, BertConfig/from torch.optim import Optimizer, AdamW\nfrom transformers import BertConfig/' "$TRAINER_FILE"
fi

# Remove deprecated parameter
if grep -q "correct_bias=False" "$TRAINER_FILE"; then
    echo "  Removing deprecated parameter..."
    sed -i 's/, correct_bias=False//' "$TRAINER_FILE"
fi

echo "SpERT compatibility fixed!"
echo "Backup saved as $TRAINER_FILE.backup"
