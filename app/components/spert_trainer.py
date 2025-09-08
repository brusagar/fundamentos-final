from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Input, Label, Select, RichLog
from textual.screen import Screen
from textual import work
import re
from pathlib import Path
import subprocess
from typing import Dict, Any

class SpertTrainerScreen(Screen):
    """Screen for configuring and running SpERT training"""

    def compose(self) -> ComposeResult:
        """Create trainer interface"""
        with Vertical(id="trainer-container"):
            yield Label("SpERT Training Configuration", id="trainer-title")

            # Data Preparation Section
            yield Label("Data Preparation", id="data-prep-title")
            with Horizontal(id="data-prep-row"):
                yield Label("CSV File:", id="csv-label")
                yield Select(
                    self.get_csv_files(),
                    id="csv-select"
                )
                yield Button("Prepare Data", id="prepare-button", variant="success")

            # Training Configuration Section
            yield Label("Training Configuration", id="training-config-title")
            with Horizontal(id="params-row"):
                yield Label("Config:", id="config-label")
                yield Select(
                    self.get_config_files(),
                    id="config-select"
                )

            with Horizontal(id="control-row"):
                yield Button("Start Training", id="train-button", variant="primary")
                yield Button("Stop", id="stop-button", variant="error")
                yield Button("Back", id="back-button", variant="warning")
                
            yield RichLog(id="output-log", wrap=True)

    def on_mount(self) -> None:
        """Initialize screen"""
        self.training_process = None
        self.stop_button = self.query_one("#stop-button", Button)
        self.stop_button.disabled = True

    def get_csv_files(self):
        """Get list of CSV files from app/data/annotated_csv_data/"""
        csv_data_dir = Path(__file__).parent.parent / "data" / "annotated_csv_data"
        if not csv_data_dir.exists():
            return [("No CSV files found", "")]
        
        csv_files = list(csv_data_dir.glob("*.csv"))
        if not csv_files:
            return [("No CSV files found", "")]
        
        return [(f.name, f.name) for f in csv_files]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "prepare-button":
            self.prepare_data()
        elif event.button.id == "train-button":
            self.start_training()
        elif event.button.id == "stop-button":
            self.stop_training()
        elif event.button.id == "back-button":
            self.app.pop_screen()

    @work(thread=True)
    def prepare_data(self) -> None:
        """Prepare SpERT training data from CSV using csv_to_spert script"""
        # Get paths
        root_dir = Path(__file__).parent.parent.parent
        csv_to_spert_path = root_dir / "app" / "utils" / "csv_to_spert.py"
        venv_path = root_dir / ".venv"
        python_path = venv_path / "bin" / "python"
        
        log = self.query_one("#output-log")
        
        try:
            # Get CSV file from select dropdown
            csv_file = self.query_one("#csv-select", Select).value
            if not csv_file or csv_file == Select.BLANK:
                log.write("Error: Please select a CSV file\n")
                return

            # Build full path to CSV file in app/data/annotated_csv_data/
            csv_path = root_dir / "app" / "data" / "annotated_csv_data" / csv_file
            if not csv_path.exists():
                log.write(f"Error: CSV file not found: {csv_path}\n")
                return
            
            if not csv_to_spert_path.exists():
                log.write(f"Error: csv_to_spert.py not found at {csv_to_spert_path}\n")
                return
            
            if not python_path.exists():
                log.write(f"Error: Virtual environment not found at {venv_path}\n")
                return
            
            log.write("Starting data preparation...\n")
            log.write(f"Using CSV file: {csv_file}\n")
            log.write(f"Using Python from: {python_path}\n")
            log.write(f"Working directory: {root_dir}\n\n")
            
            # Disable button during processing
            self.query_one("#prepare-button", Button).disabled = True
            
            # Read the original csv_to_spert.py script and modify it to use the specified CSV file
            with open(csv_to_spert_path, 'r', encoding='utf-8') as f:
                original_script = f.read()
            
            # Replace the hardcoded CSV filename with the user-specified one
            # Also update the data directory to be inside spert/
            modified_script = original_script.replace(
                'df = pd.read_csv("first_annotations.csv")',
                f'df = pd.read_csv("{csv_path}")'
            ).replace(
                'os.makedirs("data", exist_ok=True)',
                'os.makedirs("spert/data", exist_ok=True)'
            ).replace(
                'path = os.path.join("data", filename)',
                'path = os.path.join("spert/data", filename)'
            ).replace(
                'with open("data/types.json", "w", encoding="utf-8") as f:',
                'with open("spert/data/types.json", "w", encoding="utf-8") as f:'
            )
            
            # Create temporary script
            temp_script_path = root_dir / "temp_csv_to_spert.py"
            with open(temp_script_path, 'w', encoding='utf-8') as f:
                f.write(modified_script)
            
            # Execute the data preparation script
            cmd = [str(python_path), str(temp_script_path)]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(root_dir)
            )
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    log.write(output.strip() + "\n")
            
            # Check for errors
            returncode = process.poll()
            if returncode != 0:
                error = process.stderr.read()
                log.write(f"Error: {error}\n")
            else:
                log.write("\nData preparation completed successfully!\n")
                log.write("Generated files:\n")
                log.write("- spert/data/train.json\n")
                log.write("- spert/data/dev.json\n")
                log.write("- spert/data/test.json\n")
                log.write("- spert/data/types.json\n")
            
            # Clean up temporary script
            if temp_script_path.exists():
                temp_script_path.unlink()
            
            # Re-enable button
            self.query_one("#prepare-button", Button).disabled = False
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")
            # Re-enable button on error
            self.query_one("#prepare-button", Button).disabled = False

    @work(thread=True)
    def start_training(self) -> None:
        """Start SpERT training using the SpERT virtual environment"""
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
            config_file = self.query_one("#config-select").value
            
            # Prepare the command
            cmd = [
                str(python_path),
                "spert.py",
                "train",
                "--config", f"configs/{config_file}"
            ]
            
            log.write("Starting SpERT training...\n")
            log.write(f"Using Python from: {python_path}\n")
            log.write(f"Working directory: {spert_dir}\n")
            log.write(f"Config file: {config_file}\n\n")
            
            # Update UI state
            self.query_one("#train-button", Button).disabled = True
            self.stop_button.disabled = False
            
            # Execute training
            self.training_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(spert_dir)
            )
            
            # Stream output
            while True:
                output = self.training_process.stdout.readline()
                if output == '' and self.training_process.poll() is not None:
                    break
                if output:
                    log.write(output.strip() + "\n")
            
            # Check for errors
            returncode = self.training_process.poll()
            if returncode != 0:
                error = self.training_process.stderr.read()
                log.write(f"Error: {error}\n")
            else:
                log.write("Training completed successfully!\n")
            
            # Reset UI state
            self.query_one("#train-button", Button).disabled = False
            self.stop_button.disabled = True
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")
            # Reset UI state on error
            self.query_one("#train-button", Button).disabled = False
            self.stop_button.disabled = True

    def get_config(self) -> Dict[str, Any]:
        """Get training configuration from inputs"""
        return {
            "config": self.query_one("#config-select").value
        }

    def get_config_files(self):
        """Return list of training config files"""
        spert_dir = Path(__file__).parent.parent.parent / "spert"
        config_dir = spert_dir / "configs"
        if not config_dir.exists():
            return [("No configs found", "")]
        
        # Filter for training configs
        train_configs = [f for f in config_dir.glob("*train*.conf")]
        if not train_configs:
            return [("No training configs found", "")]
        
        return [(f.name, f.name) for f in train_configs]

    def stop_training(self) -> None:
        """Stop training process"""
        if self.training_process:
            self.training_process.terminate()
            self.training_process = None
            
            # Update UI state
            self.query_one("#train-button", Button).disabled = False
            self.stop_button.disabled = True
            
            log = self.query_one("#output-log")
            log.write("Training stopped by user\n")