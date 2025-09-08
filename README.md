# kula-nlp-app
 
# Main app environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For development (Needed to run the app in the browser)
pip install -r requirements-dev.txt

# For advanced coreference (optional)
pip install -r requirements-coref.txt

# SpERT training environment
cd spert
python -m venv .spert_env
source .spert_env/bin/activate
pip install -r requirements.txt  # or requirements-spert.txt for exact versions