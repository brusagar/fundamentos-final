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
        """Create predictor interface"""
        with Vertical(id="predictor-container"):
            yield Label("SpERT Prediction", id="predictor-title")

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
        """Handle button presses"""
        if event.button.id == "predict-button":
            self.start_prediction()
        elif event.button.id == "stop-button":
            self.stop_prediction()
        elif event.button.id == "back-button":
            self.app.pop_screen()

    @work(thread=True)
    def start_prediction(self) -> None:
        """Start SpERT prediction using the SpERT virtual environment"""
        # Get paths
        spert_dir = Path(__file__).parent.parent.parent / "spert"
        venv_path = spert_dir / ".spert_env"
        python_path = venv_path / "bin" / "python"
        
        log = self.query_one("#output-log")
        
        try:
            if not python_path.exists():
                log.write(f"Error: SpERT virtual environment not found at {venv_path}\n")
                return
            
            # Get selected config
            config_file = self.query_one("#config-select", Select).value
            if not config_file or config_file == Select.BLANK:
                log.write("Error: Please select a config file\n")
                return
            
            # Prepare the command
            cmd = [
                str(python_path),
                "spert.py",
                "predict",
                "--config", f"configs/{config_file}"
            ]
            
            log.write("Starting SpERT prediction...\n")
            log.write(f"Using Python from: {python_path}\n")
            log.write(f"Working directory: {spert_dir}\n")
            log.write(f"Config file: {config_file}\n\n")
            
            # Update UI state
            self.query_one("#predict-button", Button).disabled = True
            self.stop_button.disabled = False
            
            # Execute prediction
            self.prediction_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(spert_dir)
            )
            
            # Stream output
            while True:
                output = self.prediction_process.stdout.readline()
                if output == '' and self.prediction_process.poll() is not None:
                    break
                if output:
                    log.write(output.strip() + "\n")
            
            # Check for errors
            returncode = self.prediction_process.poll()
            if returncode != 0:
                error = self.prediction_process.stderr.read()
                log.write(f"Error: {error}\n")
            else:
                log.write("Prediction completed successfully!\n")
                log.write("Results saved to: spert/data/predictions.json\n")
                
                # Copy predictions to app/data/predictions/ for easy access
                predictions_dir = Path(__file__).parent.parent / "data" / "predictions"
                predictions_dir.mkdir(exist_ok=True)
                
                import shutil
                src_path = spert_dir / "data" / "predictions.json"
                dst_path = predictions_dir / "predictions.json"
                if src_path.exists():
                    shutil.copy2(src_path, dst_path)
                    log.write(f"Predictions also copied to: {dst_path}\n")
            
            # Reset UI state
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")
            # Reset UI state on error
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True

    def stop_prediction(self) -> None:
        """Stop prediction process"""
        if self.prediction_process:
            self.prediction_process.terminate()
            self.prediction_process = None
            
            # Update UI state
            self.query_one("#predict-button", Button).disabled = False
            self.stop_button.disabled = True
            
            log = self.query_one("#output-log")
            log.write("Prediction stopped by user\n")
