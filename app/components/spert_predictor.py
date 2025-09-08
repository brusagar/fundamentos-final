from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Input, Label, Select, RichLog
from textual.screen import Screen
from textual import work
import re
from pathlib import Path
import subprocess
import json
from typing import Dict, Any

class SpertPredictorScreen(Screen):
    """Screen for configuring and running SpERT prediction"""

    def compose(self) -> ComposeResult:
        with Vertical(id="predictor-container"):
            yield Label("SpERT Prediction", id="predictor-title")

            # Data Preparation Section
            yield Label("Data Preparation", id="data-prep-title")
            with Horizontal(id="data-prep-row"):
                yield Label("Input File:", id="input-label")
                yield Select(
                    self.get_preprocessed_files(),
                    id="input-select"
                )
                yield Button("Prepare Data", id="prepare-button", variant="success")

            # Configuration Section
            yield Label("Prediction Configuration", id="prediction-config-title")
            with Horizontal(id="config-row"):
                yield Label("Config:", id="config-label")
                yield Select(
                    self.get_predict_configs(),
                    id="config-select"
                )

            with Horizontal(id="control-row"):
                yield Button("Start Prediction", id="predict-button", variant="primary")
                yield Button("Stop", id="stop-button", variant="error")
                yield Button("Back", id="back-button", variant="warning")
                
            yield RichLog(id="output-log", wrap=True)

    def on_mount(self) -> None:
        """Initialize screen"""
        self.prediction_process = None
        self.stop_button = self.query_one("#stop-button", Button)
        self.stop_button.disabled = True

    def get_preprocessed_files(self):
        """Get list of files from app/data/preprocessed/ directory"""
        app_dir = Path(__file__).parent.parent
        preprocessed_dir = app_dir / "data" / "preprocessed"
        
        files = []
        
        if preprocessed_dir.exists():
            # Look for .txt files in the main directory
            for txt_file in preprocessed_dir.glob("*.txt"):
                files.append((txt_file.name, str(txt_file)))
            
            # Look for files in subdirectories
            for subdir in preprocessed_dir.iterdir():
                if subdir.is_dir():
                    for txt_file in subdir.glob("*.txt"):
                        relative_path = f"{subdir.name}/{txt_file.name}"
                        files.append((relative_path, str(txt_file)))
        
        if not files:
            return [("No text files found", "")]
        
        return files

    def get_predict_configs(self):
        """Return list of prediction config files"""
        spert_dir = Path(__file__).parent.parent.parent / "spert"
        config_dir = spert_dir / "configs"
        if not config_dir.exists():
            return [("No configs found", "")]
        
        # Filter for prediction configs
        predict_configs = [f for f in config_dir.glob("*predict*.conf")]
        if not predict_configs:
            return [("No prediction configs found", "")]
        
        return [(f.name, f.name) for f in predict_configs]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prepare-button":
            self.prepare_data()
        elif event.button.id == "predict-button":
            self.start_prediction()
        elif event.button.id == "stop-button":
            self.stop_prediction()
        elif event.button.id == "back-button":
            self.app.pop_screen()

    @work(thread=True)
    def prepare_data(self) -> None:
        """Prepare data for prediction by tokenizing selected text file"""
        root_dir = Path(__file__).parent.parent.parent
        tokenizer_script = root_dir / "app" / "utils" / "tokenize_samples.py"
        venv_path = root_dir / ".venv"
        python_path = venv_path / "bin" / "python"
        
        log = self.query_one("#output-log")
        
        try:
            # Get selected input file
            input_file = self.query_one("#input-select", Select).value
            if not input_file or input_file == Select.BLANK:
                log.write("Error: Please select an input file\n")
                return
            
            if input_file == "":
                log.write("Error: No preprocessed files found\n")
                return
            
            log.write("Preparing data for prediction...\n")
            log.write(f"Input file: {input_file}\n")
            log.write(f"Tokenizing with: {tokenizer_script}\n\n")
            
            # Prepare the command to run tokenize_samples.py - save to sentences_to_predict directory
            sentences_dir = root_dir / "spert" / "data" / "sentences_to_predict"
            sentences_dir.mkdir(exist_ok=True, parents=True)
            output_path = sentences_dir / "raw_text.json"
            cmd = [
                str(python_path),
                str(tokenizer_script),
                "--input", input_file,
                "--output", str(output_path)
            ]
            
            # Run the tokenizer
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(root_dir)
            )
            
            if result.returncode == 0:
                log.write("Data preparation completed successfully!\n")
                log.write(result.stdout + "\n")
                log.write(f"Output saved to: {output_path}\n\n")
                log.write("You can now start prediction.\n")
            else:
                log.write("Error during data preparation:\n")
                log.write(result.stderr + "\n")
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")

    @work(thread=True)
    def start_prediction(self) -> None:
        spert_dir = Path(__file__).parent.parent.parent / "spert"
        venv_path = spert_dir / ".spert_env"
        python_path = venv_path / "bin" / "python"
        
        log = self.query_one("#output-log")
        
        try:
            if not python_path.exists():
                log.write(f"Error: SpERT virtual environment not found at {venv_path}\n")
                return
            
            # Check if raw_text.json exists in sentences_to_predict directory
            raw_text_path = spert_dir / "data" / "sentences_to_predict" / "raw_text.json"
            if not raw_text_path.exists():
                log.write("Error: No prepared data found!\n")
                log.write("Please use 'Prepare Data' first to select and tokenize a text file.\n")
                return
            
            config_file = self.query_one("#config-select", Select).value
            if not config_file or config_file == Select.BLANK:
                log.write("Error: Please select a config file\n")
                return
            
            # Create custom config with model_predictions output path
            model_predictions_dir = spert_dir / "data" / "model_predictions"
            model_predictions_dir.mkdir(exist_ok=True, parents=True)
            
            # Read the original config
            original_config_path = spert_dir / "configs" / config_file
            with open(original_config_path, 'r') as f:
                config_content = f.read()
            
            # Modify the dataset path to point to sentences_to_predict/raw_text.json
            dataset_path = "data/sentences_to_predict/raw_text.json"
            config_content = re.sub(
                r'dataset_path\s*=\s*.*',
                f'dataset_path = {dataset_path}',
                config_content
            )
            
            # Modify the predictions path to point to model_predictions/predictions.json
            predictions_path = "data/model_predictions/predictions.json"
            config_content = re.sub(
                r'predictions_path\s*=\s*.*',
                f'predictions_path = {predictions_path}',
                config_content
            )
            
            # Create temporary config file
            temp_config_path = spert_dir / f"temp_{config_file}"
            with open(temp_config_path, 'w') as f:
                f.write(config_content)
            
            cmd = [
                str(python_path),
                "spert.py",
                "predict",
                "--config", str(temp_config_path.name)
            ]
            
            log.write("Starting SpERT prediction...\n")
            log.write(f"Using Python from: {python_path}\n")
            log.write(f"Working directory: {spert_dir}\n")
            log.write(f"Config file: {config_file}\n")
            log.write(f"Input data: {raw_text_path}\n")
            log.write(f"Output will be saved to: spert/data/model_predictions/predictions.json\n\n")
            
            self.query_one("#predict-button", Button).disabled = True
            self.stop_button.disabled = False
            
            self.prediction_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(spert_dir)
            )
            
            while True:
                output = self.prediction_process.stdout.readline()
                if output == '' and self.prediction_process.poll() is not None:
                    break
                if output:
                    log.write(output.strip() + "\n")
            
            returncode = self.prediction_process.poll()
            if returncode != 0:
                error = self.prediction_process.stderr.read()
                log.write(f"Error: {error}\n")
            else:
                log.write("Prediction completed successfully!\n")
                log.write(f"Results saved to: spert/data/model_predictions/predictions.json\n")
                log.write("Entity search can now access the predictions.\n")
            
            # Cleanup temporary config file
            if temp_config_path.exists():
                temp_config_path.unlink()
            
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True

    def stop_prediction(self) -> None:
        if self.prediction_process:
            self.prediction_process.terminate()
            self.prediction_process = None
            
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True
            
            log = self.query_one("#output-log")
            log.write("Prediction stopped by user\n")
