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
    """Screen for executing the NER script with custom parameters"""
    
    BINDINGS = [
        Binding(key="e,E", action="execute", description="Execute Script"),
        Binding(key="b,B", action="back", description="Back to Menu"),
        Binding(key="escape", action="blur_input", description="Exit Input/Back", show=False),
        Binding(key="tab", action="focus_next", description="Next Field", show=False),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_files = set()  # Track selected files
    
    def get_input_files(self):
        """Get list of available input text files from app/data/preprocessed/"""
        script_dir = Path(__file__).parent.parent.parent
        input_files = []
        
        # Check for text files in app/data/preprocessed/
        preprocessed_dir = script_dir / "app" / "data" / "preprocessed"
        if preprocessed_dir.exists():
            # Look for .txt files in the main directory
            for txt_file in preprocessed_dir.glob("*.txt"):
                relative_path = f"app/data/preprocessed/{txt_file.name}"
                input_files.append((txt_file.name, relative_path))
            
            # Also look for .json files in the main directory
            for json_file in preprocessed_dir.glob("*.json"):
                relative_path = f"app/data/preprocessed/{json_file.name}"
                input_files.append((json_file.name, relative_path))
            
            # Look for files in subdirectories (like book_chunks/)
            for subdir in preprocessed_dir.iterdir():
                if subdir.is_dir():
                    # Look for .txt files in subdirectory
                    for txt_file in subdir.glob("*.txt"):
                        relative_path = f"app/data/preprocessed/{subdir.name}/{txt_file.name}"
                        display_name = f"{subdir.name}/{txt_file.name}"
                        input_files.append((display_name, relative_path))
                    
                    # Look for .json files in subdirectory
                    for json_file in subdir.glob("*.json"):
                        relative_path = f"app/data/preprocessed/{subdir.name}/{json_file.name}"
                        display_name = f"{subdir.name}/{json_file.name}"
                        input_files.append((display_name, relative_path))
        
        if not input_files:
            return [("No preprocessed files found", "")]
        
        return input_files
    
    def get_gazeteer_files(self):
        """Get list of available gazeteer/pattern files from app/data/gazeteer/"""
        script_dir = Path(__file__).parent.parent.parent
        gazeteer_files = [("None (skip gazeteer)", "")]  # Option for no gazeteer
        
        # Check for JSON files in app/data/gazeteer/
        gazeteer_dir = script_dir / "app" / "data" / "gazeteer"
        if gazeteer_dir.exists():
            for json_file in gazeteer_dir.glob("*.json"):
                relative_path = f"app/data/gazeteer/{json_file.name}"
                gazeteer_files.append((json_file.name, relative_path))
        
        return gazeteer_files
    
    def compose(self):
        with Vertical():
            # Scrollable main content area
            with VerticalScroll(id="main-content"):
                yield Label("NER Script Executor", id="executor-title")
                
                with Vertical(id="input-container"):
                    yield Label("Input Files (select multiple):")
                    
                    # Create a SelectionList for file selection
                    file_options = self.get_input_files()
                    
                    # Check if we have actual files or just the "no files found" message
                    if len(file_options) == 1 and file_options[0][1] == "":
                        yield Label("No preprocessed files found in app/data/preprocessed/", id="no-files-message")
                    else:
                        # Create SelectionList with file options
                        selection_items = []
                        for i, (display_name, file_path) in enumerate(file_options):
                            # Create selection items: (label, value, initially_selected)
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
        """Set up the SelectionList border title after mounting"""
        try:
            file_list = self.query_one("#file-list", SelectionList)
            file_list.border_title = "Select files to process"
        except:
            # SelectionList might not exist if no files found
            pass

    def action_execute(self):
        """Execute script action"""
        self.run_script()

    def action_back(self):
        """Back to menu action"""
        self.app.pop_screen()

    def action_blur_input(self):
        """Exit input editing mode or go back"""
        focused = self.app.focused
        if focused and isinstance(focused, (Input,)):
            # If an input is focused, blur it to exit editing mode
            focused.blur()
        else:
            # If no input is focused, go back to previous screen
            self.app.pop_screen()

    def action_focus_next(self):
        """Move to next focusable widget"""
        self.focus_next()

    def on_key(self, event) -> None:
        """Handle key presses globally"""
        # Handle shortcuts even when widgets are focused
        focused = self.app.focused
        if focused and isinstance(focused, Input):
            # Don't interfere with text input
            return
        
        if event.key.lower() == 'e':
            event.prevent_default()
            self.action_execute()
        elif event.key.lower() == 'b':
            event.prevent_default()
            self.action_back()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses (legacy support)"""
        if event.button.id == "execute":
            self.run_script()
        elif event.button.id == "back":
            self.app.pop_screen()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Handle selection changes in the file list"""
        # Get the selected file paths from the SelectionList
        file_list = self.query_one("#file-list", SelectionList)
        self.selected_files = set(file_list.selected)

    def join_files(self, file_paths):
        """Join multiple files into a single temporary file and return the path"""
        script_dir = Path(__file__).parent.parent.parent
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_path = temp_file.name
        
        try:
            with open(temp_path, 'w', encoding='utf-8') as outfile:
                for i, file_path in enumerate(file_paths):
                    full_path = script_dir / file_path
                    if full_path.exists():
                        # Add separator between files
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
        """Execute the preprocessing script using the local virtual environment"""
        # Get paths - look for preprocessing script in current directory
        script_dir = Path(__file__).parent.parent.parent
        script_path = script_dir / "app/utils/preprocessing_script.py"

        # For now, use the main venv - but could be changed to a separate one
        venv_path = script_dir / ".venv"
        python_path = venv_path / "bin" / "python"

        temp_file_path = None
        try:
            log = self.query_one("#output-log")
            log.clear()  # Clear previous output
            log.write("Starting preprocessing script execution...\n")
            
            # Get selected files
            if not self.selected_files:
                log.write("Error: Please select at least one input file\n")
                return
            
            # Get other input values
            output_file = self.query_one("#output-file").value.strip()
            patterns_file = self.query_one("#patterns-file", Select).value
            coref_option = self.query_one("#coref-option", Select).value
            
            # Ensure output goes to app/data/csv_data directory
            # Extract just the filename if user provided a path
            if output_file:
                output_filename = Path(output_file).name  # Extract just the filename
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