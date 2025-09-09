#!/usr/bin/env python3
"""
Fix SpERT compatibility with newer transformers versions
"""

import os
import sys
from pathlib import Path

def fix_spert_trainer():
    spert_trainer_path = Path("spert/spert/spert_trainer.py")
    
    if not spert_trainer_path.exists():
        print("Error: spert/spert/spert_trainer.py not found!")
        print("Make sure SpERT is cloned and you're in the project root.")
        return False
    
    print(f"Fixing {spert_trainer_path}...")
    
    with open(spert_trainer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes_made = False
    
    # Fix AdamW import
    old_import = "from transformers import AdamW, BertConfig"
    new_import = "from torch.optim import Optimizer, AdamW\nfrom transformers import BertConfig"
    
    if old_import in content:
        print("  Fixing AdamW import...")
        content = content.replace(old_import, new_import)
        changes_made = True
    
    # Remove deprecated parameter
    old_optimizer = "optimizer = AdamW(optimizer_params, lr=args.lr, weight_decay=args.weight_decay, correct_bias=False)"
    new_optimizer = "optimizer = AdamW(optimizer_params, lr=args.lr, weight_decay=args.weight_decay)"
    
    if old_optimizer in content:
        print("  Removing deprecated parameter...")
        content = content.replace(old_optimizer, new_optimizer)
        changes_made = True
    
    if changes_made:
        with open(spert_trainer_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("SpERT compatibility fixed!")
        return True
    else:
        print("No changes needed - already compatible")
        return True

def main():
    print("SpERT Compatibility Fixer")
    print("-" * 25)
    
    if not Path("spert").exists():
        print("Error: 'spert' directory not found!")
        print("Run this from the project root where 'spert' folder exists.")
        sys.exit(1)
    
    success = fix_spert_trainer()
    
    if success:
        print("\nDone! SpERT is now compatible.")
    else:
        print("\nSomething went wrong.")
        sys.exit(1)

if __name__ == "__main__":
    main()
