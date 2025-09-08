# Relations and NER NLP Application - Complete Setup Guide

This guide provides step-by-step instructions to set up the Relations and NER NLP application with SpERT integration from scratch.

## Overview

This application is a Textual-based GUI for Named Entity Recognition (NER) and Relation Extraction using SpERT (Span-based Entity and Relation Transformer). It includes:

- **Main Application**: Textual-based GUI for text processing and analysis
- **SpERT Integration**: Span-based entity and relation extraction
- **Training Pipeline**: Custom model training capabilities
- **Prediction Interface**: Interactive prediction and analysis tools

## Prerequisites

- Python 3.8+ 
- Git
- Virtual environment support (venv)
- At least 4GB RAM (8GB+ recommended for training)

## Project Structure After Setup

```
fundamentos-final/
├── .venv/                          # Main app virtual environment
├── app/                            # Main application code
│   ├── app.py                     # Main application entry point
│   ├── components/                # UI components
│   ├── utils/                     # Utility functions
│   ├── models/                    # Data models
│   └── data/                      # Application data
├── spert/                         # SpERT framework
│   ├── .spert_env/               # Separate SpERT environment
│   ├── spert/                    # SpERT core modules
│   ├── data/                     # Training/prediction data
│   ├── configs/                  # Configuration files (includes your custom configs)
│   └── scripts/                  # Utility scripts
├── requirements.txt              # Main app dependencies
├── requirements-dev.txt          # Development dependencies
├── requirements-coref.txt        # Optional coreference dependencies
└── README.md
```

## Step 1: Clone and Set Up SpERT

### 1.1 Clone Original SpERT Repository
```bash
# Clone SpERT from the official repository
git clone https://github.com/lavis-nlp/spert.git
cd spert
```

### 1.2 Set Up SpERT Environment
```bash
# Create separate virtual environment for SpERT
python -m venv .spert_env
source .spert_env/bin/activate  # On Windows: .spert_env\Scripts\activate

# Install SpERT dependencies
pip install -r requirements.txt

# Install SpaCy model for tokenization
python -m spacy download en_core_web_sm

# Optional: Download sample datasets and models
bash ./scripts/fetch_datasets.sh
bash ./scripts/fetch_models.sh

# Deactivate SpERT environment
deactivate
```

## Step 2: Set Up Main Application Environment

### 2.1 Create Main Application Structure
```bash
# Navigate back to your project root or clone this repository
cd /path/to/your/project

# Create main application virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2.2 Install Main Application Dependencies
```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (RECOMMENDED - includes textual-dev, textual-serve)
pip install -r requirements-dev.txt

# Optional: Install coreference resolution dependencies
pip install -r requirements-coref.txt
```

### 2.3 Dependency Files Content

**requirements.txt:**
```pip-requirements
# Main Application Requirements
textual>=6.0.0,<7.0.0
textual-autocomplete>=4.0.4,<5.0.0
pandas>=2.0.0
spacy>=3.5.0
scikit-learn>=1.3.0
```

**requirements-dev.txt:**
```pip-requirements
# Development Dependencies (RECOMMENDED)
textual>=6.0.0,<7.0.0
textual-autocomplete>=4.0.4,<5.0.0
textual-dev>=1.7.0
textual-serve>=1.1.2
pandas>=2.0.0
spacy>=3.5.0
scikit-learn>=1.3.0
tqdm>=4.0.0
rich>=14.0.0
click>=8.2.0
# ... additional dev dependencies
```

## Step 3: Configure SpERT for Your Project

### 3.1 Add Your Custom Configuration Files

The application uses configuration files located in `spert/configs/`. You can add your custom training and prediction configurations to this directory.

**Example training config (spert/configs/argonauts_config_train.conf):**
```properties
label = relation_train
model_type = spert
model_path = bert-base-cased
tokenizer_path = bert-base-cased
train_path = data/train.json
valid_path = data/dev.json
types_path = data/types.json 
train_batch_size = 2
eval_batch_size = 2
neg_entity_count = 100
neg_relation_count = 100
epochs = 2
lr = 3e-5
lr_warmup = 0.1
weight_decay = 0.01
max_grad_norm = 1.0
rel_filter_threshold = 0.4
size_embedding = 25
prop_drop = 0.1
max_span_size = 10
store_predictions = true
store_examples = true
sampling_processes = 1
max_pairs = 1000
final_eval = true
log_path = data/log/
save_path = data/save/
no_overlapping = true
```

**Example prediction config (spert/configs/argonauts_predict.conf):**
```properties
model_type = spert
model_path = data/save/relation_train/[YOUR_TIMESTAMP]/final_model
tokenizer_path = data/save/relation_train/[YOUR_TIMESTAMP]/final_model
dataset_path = data/raw_text.json
types_path = data/types.json
predictions_path = data/predictions.json
spacy_model = en_core_web_sm
eval_batch_size = 1
rel_filter_threshold = 0.4
size_embedding = 25
prop_drop = 0.1
max_span_size = 10
sampling_processes = 4
max_pairs = 1000
```

### 3.2 Configuration Notes

**Important:** All configuration files should be placed in `spert/configs/` directory. The application's trainer and predictor components automatically scan this directory for:
- Training configs: Files containing `*train*.conf` 
- Prediction configs: Files containing `*predict*.conf`

You can copy the example configurations provided by SpERT and modify them for your specific needs:

```bash
# Navigate to SpERT configs directory
cd spert/configs

# List existing example configs
ls *.conf

# Create your custom configs based on examples
cp example_train.conf argonauts_config_train.conf
cp example_predict.conf argonauts_predict.conf

# Edit the configs as needed
nano argonauts_config_train.conf
nano argonauts_predict.conf
```

## Step 4: Running the Application

### 4.1 Environment Management

**To work on the main application:**
```bash
# Activate main app environment
source .venv/bin/activate
```

**To work with SpERT (training/prediction):**
```bash
# Navigate to SpERT directory and activate SpERT environment
cd spert
source .spert_env/bin/activate
```

### 4.2 Running the Application

**Method 1: Browser-based (RECOMMENDED)**
```bash
# Activate main app environment
source .venv/bin/activate

# Run in browser
textual serve app/app.py
# OR if textual command doesn't work:
python -m textual serve app/app.py
```

**Method 2: Terminal-based**
```bash
# Activate main app environment
source .venv/bin/activate

# Run in terminal
textual run app/app.py
# OR:
python -m textual run app/app.py
```

**Method 3: Direct Python**
```bash
# Activate main app environment
source .venv/bin/activate

# Run directly
python app/app.py
```

## Step 5: Training and Prediction Workflow

### 5.1 Training a Model
```bash
# Activate SpERT environment
cd spert
source .spert_env/bin/activate

# Train using your configuration
python spert.py train --config configs/argonauts_config_train.conf
```

### 5.2 Making Predictions
```bash
# Still in SpERT environment
python spert.py predict --config configs/argonauts_predict.conf
```

### 5.3 Updating Prediction Config
After training, update the model paths in `spert/configs/argonauts_predict.conf`:
```properties
model_path = data/save/relation_train/[YOUR_ACTUAL_TIMESTAMP]/final_model
tokenizer_path = data/save/relation_train/[YOUR_ACTUAL_TIMESTAMP]/final_model
```

## Step 6: Data Preparation

### 6.1 Required Data Files

Ensure you have these files in your `spert/data/` directory:
- `train.json` - Training data
- `dev.json` - Validation data  
- `test.json` - Test data
- `types.json` - Entity and relation type definitions
- `raw_text.json` - Raw text for prediction

### 6.2 Data Format Examples

**types.json:**
```json
{
  "entities": [
    {"type": "PERSON", "short": "PER"},
    {"type": "LOCATION", "short": "LOC"},
    {"type": "ORGANIZATION", "short": "ORG"}
  ],
  "relations": [
    {"type": "located_in", "short": "located_in"},
    {"type": "works_for", "short": "works_for"}
  ]
}
```

## Troubleshooting

### Common Issues and Solutions

**1. Textual command not found:**
```bash
# Solution: Use Python module syntax
python -m textual serve app/app.py
python -m textual run app/app.py
```

**2. Import errors:**
```bash
# Ensure you're in the correct virtual environment
which python
# Should show .venv/bin/python or .spert_env/bin/python
```

**3. SpaCy model missing:**
```bash
# Install English model
python -m spacy download en_core_web_sm
```

**4. CUDA/GPU issues:**
```bash
# Force CPU usage in config files
cpu = true
```

**5. Version conflicts:**
- Keep SpERT in separate environment (.spert_env)
- Use exact versions from requirements-spert.txt if issues persist

## Development Tips

1. **Use browser mode** (`textual serve`) for better development experience
2. **Keep environments separate** to avoid dependency conflicts
3. **Test with small datasets** first before full training
4. **Monitor GPU memory** usage during training
5. **Save configuration changes** before switching between environments

## Additional Resources

- [SpERT Paper](https://arxiv.org/abs/1909.07755)
- [Textual Documentation](https://textual.textualize.io/)
- [Transformers Library](https://huggingface.co/docs/transformers/)

## Support

If you encounter issues:
1. Check that all virtual environments are properly activated
2. Verify all required dependencies are installed
3. Ensure configuration file paths are correct
4. Check that SpaCy models are downloaded
5. Review log files in `spert/data/log/` for detailed error messages
