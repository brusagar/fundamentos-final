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

## Step 1: Clone This Repository

```bash
# Clone this repository (SpERT is already included)
git clone https://github.com/brusagar/fundamentos-final.git
cd fundamentos-final
```

## Step 2: Set Up SpERT Environment
```bash
cd spert

# Create separate virtual environment for SpERT
python -m venv .spert_env
source .spert_env/bin/activate  

# Install SpERT dependencies
pip install -r requirements.txt

# Install SpaCy model for tokenization
python -m spacy download en_core_web_sm

# Optional: Download sample datasets and models
bash ./scripts/fetch_datasets.sh
bash ./scripts/fetch_models.sh

# Deactivate SpERT environment
deactivate

# Return to project root
cd ..
```

## Step 3: Set Up Main Application Environment

```bash
# Create main application virtual environment
python -m venv .venv
source .venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (RECOMMENDED - includes textual-dev, textual-serve)
pip install -r requirements-dev.txt

# Optional: Install coreference resolution dependencies
pip install -r requirements-coref.txt
```

## Step 4: Configure SpERT for Your Project

Your configuration files should be placed in `spert/configs/`. The repository includes example configurations:

**spert/configs/argonauts_config_train.conf:**
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

**spert/configs/argonauts_predict.conf:**
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

Feel free to modify them as you wish. To try different models or maybe different training parameters.

## Step 5: Running the Application

### Environment Management

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

### Running the Textual Application

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

## Step 6: Training and Prediction Workflow

ONLY IF YOU WANT TO TRY MANUALLY OR WANT TO TRY DIFFERENT MODELS. THE APP TAKES CARE OF TRIANING AND PREDICTIONS.

### Training a Model
```bash
# Activate SpERT environment
cd spert
source .spert_env/bin/activate

# Train using your configuration (configs are now in spert/configs/)
python spert.py train --config configs/argonauts_config_train.conf
```

### Making Predictions
```bash
# Still in SpERT environment
python spert.py predict --config configs/argonauts_predict.conf
```

### Updating Prediction Config
After training, update the model paths in `spert/configs/argonauts_predict.conf`:
```properties
model_path = data/save/relation_train/[YOUR_ACTUAL_TIMESTAMP]/final_model
tokenizer_path = data/save/relation_train/[YOUR_ACTUAL_TIMESTAMP]/final_model
```

## Step 7: Data Preparation

### Required Data Files

Ensure you have these files in your `spert/data/` directory:
- `train.json` - Training data
- `dev.json` - Validation data  
- `test.json` - Test data
- `types.json` - Entity and relation type definitions
- `raw_text.json` - Raw text for prediction

### Data Format Examples

**types.json:**
```json
{
  "entities": [
    {"type": "PERSON", "short": "PER"},
    {"type": "LOCATION", "short": "LOC"},
    {"type": "ORGANIZATION", "short": "ORG"},
    {"type": "EVENT", "short": "EVT"}
  ],
  "relations": [
    {"type": "located_in", "short": "located_in"},
    {"type": "works_for", "short": "works_for"},
    {"type": "part_of", "short": "part_of"}
  ]
}
```

**Example prediction output (spert/data/model_predictions/predictions.json):**
```json
[
  {
    "tokens": ["Moving", "Westwards", "from", "Digumenu", "..."],
    "entities": [
      {"type": "LOCATION", "start": 3, "end": 4},
      {"type": "EVENT", "start": 8, "end": 9}
    ],
    "relations": [
      {"type": "part_of", "head": 0, "tail": 1}
    ]
  }
]
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
# Install English model in SpERT environment
cd spert
source .spert_env/bin/activate
python -m spacy download en_core_web_sm
```

**4. CUDA/GPU issues:**
```bash
# Force CPU usage in config files
cpu = true
```

**5. Configuration file not found:**
- Ensure configs are in `spert/configs/`, not in root `configs/`
- Use relative paths in SpERT commands: `configs/your_config.conf`

**6. Version conflicts:**
- Keep SpERT in separate environment (`.spert_env`)
- Use exact versions from SpERT requirements if issues persist

## Dependencies

### Main Application (requirements-dev.txt)
```pip-requirements
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
```

### SpERT Environment
SpERT uses its own `requirements.txt` with specific versions for:
- PyTorch/Transformers
- BERT models
- Scientific computing libraries

## Additional Resources

- [SpERT Paper](https://arxiv.org/abs/1909.07755)
- [Textual Documentation](https://textual.textualize.io/)
- [Transformers Library](https://huggingface.co/docs/transformers/)
