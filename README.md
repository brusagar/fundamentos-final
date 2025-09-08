# Relations and NER NLP Application

This guide provides step-by-step instructions to set up the Relations and NER NLP application with SpERT integration from scratch.

## Overview

This application is a **Textual-based GUI** for Named Entity Recognition (NER) and Relation Extraction using **SpERT** (Span-based Entity and Relation Transformer). It provides an interactive terminal interface that can also run in your browser.

### Key Features
- **Textual GUI**: Modern terminal-based interface with browser support
- **SpERT Integration**: State-of-the-art span-based entity and relation extraction
- **Training Pipeline**: Custom model training with your own data
- **Interactive Prediction**: Real-time analysis and visualization
- **Data Management**: Built-in tools for data preprocessing and annotation
- **Multi-Environment**: Separate environments for main app and SpERT to avoid conflicts

## Prerequisites

- **Python 3.8+** (Python 3.11 recommended)
- **Git**
- **Terminal/Command Line Access**

## Project Structure After Setup

```
fundamentos-final/                 # Your main repository
├── .venv/                         # Main app virtual environment
├── app/                           # Main application code
│   ├── app.py                    # Main application entry point
│   ├── components/               # UI components and screens
│   ├── utils/                    # Utility functions
│   ├── models/                   # Data models
│   └── data/                     # Application data and samples
├── requirements.txt              # Main app dependencies
├── requirements-dev.txt          # Development dependencies (includes textual-dev)
├── requirements-coref.txt        # Optional coreference dependencies
├── .gitignore                    # Git ignore file (includes spert/)
└── README.md                     # This file

spert/                            # SpERT framework (cloned separately)
├── .spert_env/                   # Separate SpERT virtual environment
├── spert/                        # SpERT core modules
├── data/                         # Training/prediction data
├── configs/                      # Configuration files (your custom configs)
└── scripts/                      # SpERT utility scripts
```

## Quick Start

### 1. Clone This Repository

```bash
git clone https://github.com/brusagar/fundamentos-final.git
cd fundamentos-final
```

### 2. Set Up SpERT (For Training/Prediction)

```bash
# Clone SpERT framework (separate from main repo)
git clone https://github.com/lavis-nlp/spert.git
cd spert

# Create SpERT environment
python -m venv .spert_env
source .spert_env/bin/activate  # On Windows: .spert_env\Scripts\activate

# Install custom SpERT dependencies
pip install -r ./requirements-spert.txt
python -m spacy download en_core_web_sm

# Return to main project
deactivate
cd ..
```

### 3. Set Up Main Application

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

## Running the Application

### Method 1: Browser Interface (RECOMMENDED)
```bash
# Activate main app environment
source .venv/bin/activate

# Serve in browser (opens automatically)
textual serve app/app.py

```

### Method 2: Terminal Interface
```bash
# Activate main app environment
source .venv/bin/activate

# Run in terminal
textual run app/app.py
```

### Method 3: Direct Python Execution
```bash
# Activate main app environment
source .venv/bin/activate

# Run directly
python app/app.py
```

## SpERT Configuration and Usage

### Creating Configuration Files

The application expects SpERT configuration files in `spert/configs/`. Create these files for your specific use case:

**Training Configuration (`spert/configs/argonauts_config_train.conf`):**
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

**Prediction Configuration (`spert/configs/argonauts_predict.conf`):**
```properties
model_type = spert
model_path = data/save/relation_train/[TIMESTAMP]/final_model
tokenizer_path = data/save/relation_train/[TIMESTAMP]/final_model
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

### Manual Training and Prediction (Optional)

The application handles training and prediction through its GUI, but you can also run SpERT manually:

```bash
# Switch to SpERT environment
cd spert
source .spert_env/bin/activate

# Train a model
python spert.py train --config configs/argonauts_config_train.conf

# Make predictions
python spert.py predict --config configs/argonauts_predict.conf

# Return to main app
deactivate
cd ..
```

## Data Requirements and Format

### Required Data Files

For SpERT training and prediction, ensure you have these files in your `spert/data/` directory:

- **`train.json`** - Training data in SpERT format
- **`dev.json`** - Validation data for training
- **`test.json`** - Test data for evaluation
- **`types.json`** - Entity and relation type definitions
- **`raw_text.json`** - Raw text for prediction (generated by app)

### Data Format Examples

**Entity and Relation Types (`spert/data/types.json`):**
```json
{
  "entities": [
    {"type": "PERSON", "short": "PER", "verbose": "Person names"},
    {"type": "LOCATION", "short": "LOC", "verbose": "Geographic locations"},
    {"type": "ORGANIZATION", "short": "ORG", "verbose": "Organizations"},
    {"type": "EVENT", "short": "EVT", "verbose": "Historical events"}
  ],
  "relations": [
    {"type": "located_in", "short": "located_in", "verbose": "Spatial relation"},
    {"type": "works_for", "short": "works_for", "verbose": "Employment relation"},
    {"type": "part_of", "short": "part_of", "verbose": "Part-whole relation"}
  ]
}
```

**Training Data Example (`spert/data/train.json`):**
```json
[
  {
    "tokens": ["John", "works", "for", "Google", "in", "California"],
    "entities": [
      {"type": "PERSON", "start": 0, "end": 1},
      {"type": "ORGANIZATION", "start": 3, "end": 4},
      {"type": "LOCATION", "start": 5, "end": 6}
    ],
    "relations": [
      {"type": "works_for", "head": 0, "tail": 1},
      {"type": "located_in", "head": 1, "tail": 2}
    ]
  }
]
```

### Using the Application's Data Tools

The application includes built-in tools for:
- **Text Preprocessing**: Clean and prepare raw text data
- **Entity Search**: Find and annotate entities using gazetteers
- **Manual Annotation**: Interactive entity and relation annotation
- **Data Conversion**: Convert between different formats (CSV, JSON, SpERT format)

## Application Features

### Main Interface Components

1. **Text Preprocessor**: Clean and chunk large text files
2. **Entity Search**: Automated entity recognition using pattern matching
3. **Sentence Editor**: Manual annotation interface for entities and relations
4. **SpERT Trainer**: Configure and run model training
5. **SpERT Predictor**: Run predictions on new text
6. **Processing Preview**: Visualize preprocessing results

### Workflow Example

1. **Import Text**: Load your raw text data
2. **Preprocess**: Clean and chunk text into manageable segments
3. **Entity Recognition**: Use automated tools to identify potential entities
4. **Manual Annotation**: Review and correct entity/relation annotations
5. **Export Training Data**: Convert annotations to SpERT format
6. **Train Model**: Use SpERT trainer with your custom data
7. **Predict**: Apply trained model to new text
8. **Visualize Results**: View predictions in the application interface

## Troubleshooting

### Common Issues and Solutions

**❌ `textual` command not found**
```bash
# Solution: Use Python module syntax
python -m textual serve app/app.py
python -m textual run app/app.py
```

**❌ Import errors or module not found**
```bash
# Check you're in the correct environment
which python
# Should show .venv/bin/python for main app
# Or .spert_env/bin/python for SpERT

# Reinstall dependencies if needed
pip install -r requirements-dev.txt
```

**❌ SpaCy model missing**
```bash
# Install in SpERT environment
cd spert
source .spert_env/bin/activate
python -m spacy download en_core_web_sm
```

**❌ CUDA/GPU issues**
```bash
# Force CPU usage in SpERT config files
# Add this line to your .conf files:
cpu = true
```

**❌ Permission denied or command not found**
```bash
# On Windows, use:
.venv\Scripts\activate
.spert_env\Scripts\activate

# On Linux/Mac, ensure script permissions:
chmod +x .venv/bin/activate
```

**❌ Port already in use (browser mode)**
```bash
# Use different port
python -m textual serve app/app.py --port 8081
```

**❌ Configuration file errors**
- Ensure config files are in `spert/configs/`, not root `configs/`
- Use forward slashes in paths, even on Windows
- Check file paths exist relative to `spert/` directory

### Getting Help

If you encounter issues:
1. Check the error message carefully
2. Ensure you're in the correct virtual environment
3. Verify all file paths in configuration files
4. Try running the application in different modes (browser vs terminal)
5. Check the application logs in `textual.log`

## Dependencies

### Main Application Environment (`.venv`)
```txt
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

### SpERT Environment (`.spert_env`)
SpERT manages its own dependencies including:
- PyTorch and Transformers
- BERT and other transformer models
- Scientific computing libraries (NumPy, SciPy)
- SpaCy for tokenization

### Optional Extensions
- **Coreference Resolution**: Install `requirements-coref.txt` for advanced NLP features
- **GPU Support**: CUDA-compatible PyTorch versions (configured in SpERT environment)

## Performance Tips

- **Use Browser Mode**: Generally faster and more responsive than terminal mode
- **Separate Environments**: Keeps dependencies isolated and prevents conflicts
- **GPU Training**: Configure CUDA in SpERT for faster model training
- **Batch Processing**: Process multiple documents using the application's batch features
- **Memory Management**: Use smaller batch sizes if you encounter memory issues

## Advanced Usage

### Custom Model Integration
- Replace BERT with other transformer models in SpERT configs
- Experiment with different model architectures
- Fine-tune hyperparameters for your specific domain

### Data Pipeline Automation
- Use the application's scripting features for batch processing
- Integrate with external data sources
- Export results in various formats (JSON, CSV, CoNLL)

### Development and Extension
- Modify UI components in `app/components/`
- Add new preprocessing utilities in `app/utils/`
- Extend data models in `app/models/`

## Contributing

This is a research/educational project. Feel free to:
- Fork the repository
- Submit bug reports
- Suggest new features
- Contribute improvements

## Resources and References

- **SpERT Paper**: [Span-based Joint Entity and Relation Extraction with Transformer Pre-training](https://arxiv.org/abs/1909.07755)
- **Textual Framework**: [Official Documentation](https://textual.textualize.io/)
- **Transformers Library**: [Hugging Face Documentation](https://huggingface.co/docs/transformers/)
- **SpERT Repository**: [Original SpERT Implementation](https://github.com/lavis-nlp/spert)

---

**🚀 You're now ready to start using the Relations and NER NLP Application!**

For questions or issues, please check the troubleshooting section above or refer to the application's built-in help documentation.
