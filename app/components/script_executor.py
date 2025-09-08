from textual.screen import Screen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, RichLog, Select, SelectionList, Footer, Checkbox
from textual.binding import Binding
from textual import work
from pathlib import Path
import subprocess
import sys
import os
import tempfile

class ScriptExecutorScreen(Screen):
    """Data preprocessing pipeline interface"""

    BINDINGS = [
        Binding(key="r,R", action="run_script", description="Run Script"),
        Binding(key="b,B", action="back", description="Back to Menu"),
        Binding(key="escape", action="blur_input", description="Exit Input/Back", show=False),
        Binding(key="tab", action="focus_next", description="Next Field", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.selected_files = set()

    def get_text_files(self):
        script_dir = Path(__file__).parent.parent.parent
        preprocessed_dir = script_dir / "app" / "data" / "preprocessed"
        
        text_files = []
        
        if preprocessed_dir.exists():
            for txt_file in preprocessed_dir.glob("*.txt"):
                text_files.append((txt_file.name, str(txt_file)))
            
            for json_file in preprocessed_dir.glob("*.json"):
                text_files.append((json_file.name, str(json_file)))
            
            for subdir in preprocessed_dir.iterdir():
                if subdir.is_dir():
                    for txt_file in subdir.glob("*.txt"):
                        relative_path = f"{subdir.name}/{txt_file.name}"
                        text_files.append((relative_path, str(txt_file)))
                    
                    for json_file in subdir.glob("*.json"):
                        relative_path = f"{subdir.name}/{json_file.name}"
                        text_files.append((relative_path, str(json_file)))
        
        if not text_files:
            return [("No text files found", "")]
        
        return text_files

    def get_gazeteer_files(self):
        script_dir = Path(__file__).parent.parent.parent
        gazeteer_files = [("None (skip gazeteer)", "")]
        
        gazeteer_dir = script_dir / "app" / "data" / "gazeteer"
        if gazeteer_dir.exists():
            for json_file in gazeteer_dir.glob("*.json"):
                gazeteer_files.append((json_file.name, str(json_file)))
        
        return gazeteer_files

    def compose(self):
        with Vertical():
            with VerticalScroll(id="main-content"):
                yield Label("NER Script Executor", id="executor-title")
                
                with Vertical(id="input-container"):
                    yield Label("Input Files (select multiple):")
                    
                    file_options = self.get_input_files()
                    
                    if len(file_options) == 1 and file_options[0][1] == "":
                        yield Label("No preprocessed files found in app/data/preprocessed/", id="no-files-message")
                    else:
                        selection_items = []
                        for i, (display_name, file_path) in enumerate(file_options):
                            selection_items.append((display_name, file_path, False))
                        
                        yield SelectionList[str](*selection_items, id="file-list")
                    
                    yield Label("Output File:")
                    yield Input(
                        placeholder="Filename for output CSV (e.g., relation_candidates_good.csv)",
                        value="relation_candidates_good.csv",
                        id="output-file"
                    )
                    
                    yield Label("Gazeteer File:")
                    yield Select(
                        self.get_gazeteer_files(),
                        id="patterns-file"
                    )
                    
                    yield Label("Coreference Resolution:")
                    yield Select(
                        [
                            ("No coreference resolution", "none"),
                            ("spaCy experimental coreference (recommended)", "spacy_experimental"),
                            ("Stanza coreference (might crash!)", "stanza"),
                            ("Transformers-based coreference (experimental)", "transformers")
                        ],
                        value="none",
                        id="coref-option"
                    )
                
                yield RichLog(id="output-log", wrap=True)
            
            # Footer with keyboard shortcuts (always visible at bottom)
            yield Footer()

    def on_mount(self) -> None:
        try:
            file_list = self.query_one("#file-list", SelectionList)
            file_list.border_title = "Select files to process"
        except:
            pass

    def action_execute(self):
        self.run_script()

    def action_back(self):
        self.app.pop_screen()

    def action_blur_input(self):
        focused = self.app.focused
        if focused and isinstance(focused, (Input,)):
            focused.blur()
        else:
            self.app.pop_screen()

    def action_focus_next(self):
        """Move to next focusable widget"""
        self.focus_next()

    def on_key(self, event) -> None:
        """Handle key presses globally"""
        focused = self.app.focused
        if focused and isinstance(focused, Input):
            return
        
        if event.key.lower() == 'e':
            event.prevent_default()
            self.action_execute()
        elif event.key.lower() == 'b':
            event.prevent_default()
            self.action_back()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "execute":
            self.run_script()
        elif event.button.id == "back":
            self.app.pop_screen()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        file_list = self.query_one("#file-list", SelectionList)
        self.selected_files = set(file_list.selected)

    def join_files(self, file_paths):
        script_dir = Path(__file__).parent.parent.parent
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_path = temp_file.name
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as outfile:
                for i, file_path in enumerate(file_paths):
                    full_path = script_dir / file_path
                    if full_path.exists():
                        if i > 0:
                            outfile.write("\n" + "="*50 + f" FILE: {full_path.name} " + "="*50 + "\n")
                        
                        with open(full_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n")
            
            return temp_path
        except Exception as e:
            # Clean up on error
            Path(temp_path).unlink(missing_ok=True)
            raise e

    @work(thread=True)
    def run_script(self):
        script_dir = Path(__file__).parent.parent.parent
        script_path = script_dir / "app/utils/preprocessing_script.py"

        venv_path = script_dir / ".venv"
        python_path = venv_path / "bin" / "python"

        temp_file_path = None
        try:
            log = self.query_one("#output-log")
            log.clear()
            log.write("Starting preprocessing script execution...\n")
            
            if not self.selected_files:
                log.write("Error: Please select at least one input file\n")
                return
            
            output_file = self.query_one("#output-file").value.strip()
            patterns_file = self.query_one("#patterns-file", Select).value
            coref_option = self.query_one("#coref-option", Select).value
            
            if output_file:
                output_filename = Path(output_file).name
                output_file = f"app/data/csv_data/{output_filename}"
                
                # Create the output directory if it doesn't exist
                output_dir = script_dir / "app" / "data" / "csv_data"
                output_dir.mkdir(parents=True, exist_ok=True)
            
            if patterns_file == Select.BLANK:
                patterns_file = ""  # Empty string means no gazeteer
            
            # Verify script and venv exist
            if not script_path.exists():
                log.write(f"Error: Script not found at {script_path}\n")
                return
                
            if not python_path.exists():
                log.write(f"Error: Virtual environment not found at {venv_path}\n")
                return
            
            # Verify all selected files exist
            for file_path in self.selected_files:
                full_path = script_dir / file_path
                if not full_path.exists():
                    log.write(f"Error: Input file not found: {file_path}\n")
                    return
            
            # Verify patterns file exists (if specified)
            if patterns_file and not (script_dir / patterns_file).exists():
                log.write(f"Error: Patterns file not found: {patterns_file}\n")
                return
            
            # Handle multiple files - join them if more than one
            if len(self.selected_files) == 1:
                input_file = list(self.selected_files)[0]
                log.write(f"Processing single file: {input_file}\n")
            else:
                log.write(f"Joining {len(self.selected_files)} files...\n")
                temp_file_path = self.join_files(self.selected_files)
                input_file = temp_file_path
                log.write(f"Files joined into temporary file: {temp_file_path}\n")
            
            # Build command with user-specified arguments
            cmd = [
                str(python_path),
                str(script_path)
            ]
            
            # Add command line arguments based on user input
            cmd.extend(["--input", input_file])
            if output_file:
                cmd.extend(["--output", output_file])
            if patterns_file:
                cmd.extend(["--patterns", patterns_file])
            
            # Add coreference resolution option
            if coref_option == "stanza":
                cmd.append("--stanza-coref")
            elif coref_option == "spacy_experimental":
                cmd.append("--spacy-experimental")
            elif coref_option == "transformers":
                cmd.append("--transformers-coref")
            elif coref_option == "none":
                cmd.append("--no-coref")
            # If neither, we use the default behavior (no coref)
            
            log.write(f"Running preprocessing script from: {script_path}\n")
            log.write(f"Using Python from: {python_path}\n")
            log.write(f"Working directory: {script_dir}\n")
            log.write(f"Selected files: {', '.join(self.selected_files)}\n")
            log.write(f"Output file: {output_file or 'default'}\n")
            log.write(f"Patterns file: {patterns_file or 'default'}\n")
            
            # Log coreference option
            coref_descriptions = {
                "stanza": "Stanza coreference resolution (advanced but can crash)",
                "spacy_experimental": "spaCy experimental coreference (modern & stable)",
                "transformers": "Transformers-based coreference (experimental)",
                "none": "No coreference resolution"
            }
            log.write(f"Coreference: {coref_descriptions.get(coref_option, 'Unknown option')}\n")
            
            log.write(f"Command: {' '.join(cmd)}\n\n")
            log.write("=" * 60 + "\n")
            log.write("SCRIPT OUTPUT:\n")
            log.write("=" * 60 + "\n")
            
            # Execute script
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True,
                cwd=str(script_dir),
                bufsize=1,  # Line buffered
                universal_newlines=True
            )

            # Stream output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Remove newline and write to log immediately
                    log.write(output.rstrip() + "\n")
                    # Auto-scroll to bottom to show latest output
                    log.scroll_end()
                    # Force refresh the display
                    self.app.refresh()
            
            # Wait for process to complete and get return code
            process.wait()
            returncode = process.returncode
            
            if returncode != 0:
                log.write("=" * 60 + "\n")
                log.write(f"ERROR: Script exited with code {returncode}\n")
                log.write("=" * 60 + "\n")
                return
            
            log.write("=" * 60 + "\n")
            log.write("SUCCESS: Script execution completed!\n")
            log.write("=" * 60 + "\n")
            
        except Exception as e:
            log.write(f"Error: {str(e)}\n")
        finally:
            # Clean up temporary file if it was created
            if temp_file_path and Path(temp_file_path).exists():
                Path(temp_file_path).unlink(missing_ok=True)
                log.write("Temporary joined file cleaned up.\n")