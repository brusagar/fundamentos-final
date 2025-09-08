from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll, Grid, Horizontal, Vertical
from textual.widgets import Button, Input, Markdown, Label, Static, Select, Footer
from textual.binding import Binding
from textual_autocomplete import AutoComplete as BaseAutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState
from utils.custom_autocomplete import CustomAutoComplete
from utils.error_handler import SimpleProgressTracker, BasicErrorHandler
from textual import log, work

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import time

class RowEditor(Static):
    DEFAULT_CSS = """
    .row-editor {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }
    
    .sentence-label {
        column-span: 2;
        text-wrap: wrap;
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    """

    def __init__(self, row, index, labels, relations):
        super().__init__()
        self.row = row
        self.index = index
        self.labels = labels
        self.relations = relations
        self.classes = "row-editor"

    def compose(self) -> ComposeResult:
        yield Label(f"Sentence: {self.row['sentence']}", classes="sentence-label")
        
        e1 = Input(value=self.row['entity1'], placeholder="Entity 1", id="entity1-0")
        yield e1
        e1_label = Input(value=self.row['entity1_label'], placeholder="Entity 1 Label", id="entity1_label-0")
        yield e1_label
        try:
            yield CustomAutoComplete(e1_label, candidates=lambda _: [DropdownItem(l) for l in self.labels])
        except:
            pass  # Skip autocomplete if it fails
        
        e2 = Input(value=self.row['entity2'], placeholder="Entity 2", id="entity2-0")
        yield e2
        e2_label = Input(value=self.row['entity2_label'], placeholder="Entity 2 Label", id="entity2_label-0")
        yield e2_label
        try:
            yield CustomAutoComplete(e2_label, candidates=lambda _: [DropdownItem(l) for l in self.labels])
        except:
            pass  # Skip autocomplete if it fails
        
        rel = Input(value=self.row['relation'], placeholder="Relation", id="relation-0")
        yield rel
        try:
            yield CustomAutoComplete(rel, candidates=lambda _: [DropdownItem(r) for r in self.relations])
        except:
            pass  # Skip autocomplete if it fails

class NEREditorScreen(Screen):
    
    BINDINGS = [
        Binding(key="escape", action="quit", description="Back"),
        Binding(key="ctrl+z", action="undo", description="Undo"),
        Binding(key="ctrl+s", action="save_current", description="Save"),
        Binding(key="ctrl+n", action="skip_current", description="Skip"),
    ]
    
    def __init__(self, input_csv=None, output_filename="edited_output.csv"):
        super().__init__()
        self.input_csv = Path(input_csv) if input_csv else None
        
        self.error_handler = BasicErrorHandler()
        self.progress_tracker = SimpleProgressTracker("Sentence Editor")
        
        self.undo_stack = []
        self.max_undo_steps = 50
        
        self.auto_save_enabled = True
        self.last_save_index = 0
        
        annotated_data_dir = Path(__file__).parent.parent / "data" / "annotated_csv_data"
        annotated_data_dir.mkdir(parents=True, exist_ok=True)
        
        if not output_filename.endswith('.csv'):
            output_filename += '.csv'
        
        self.output_csv = annotated_data_dir / output_filename
        self.output_filename = output_filename
        
        self.current_index = 0
        self.saved_rows = []
        self.skipped_indices = set()
        self.processed_indices = set()
        self.data = pd.DataFrame()
        self.original_data = pd.DataFrame()
        self.total_sentences = 0
        self.file_selected = False
        
        if self.input_csv:
            self._load_csv_file(self.input_csv)
            self.file_selected = True

    def get_csv_files(self):
        """Get list of CSV files from app/data/csv_data/"""
        csv_data_dir = Path(__file__).parent.parent / "data" / "csv_data"
        if not csv_data_dir.exists():
            return [("No CSV files found", "")]
        
        csv_files = list(csv_data_dir.glob("*.csv"))
        if not csv_files:
            return [("No CSV files found", "")]
        
        return [(f.name, f.name) for f in csv_files]

    def _load_csv_file(self, csv_path):
        try:
            if not Path(csv_path).exists():
                self._show_message(f"File not found: {csv_path}", "error")
                return
            
            self._show_message(f"Loading file: {csv_path}", "info")
            
            self.data = pd.read_csv(
                csv_path,
                dtype=str,
                na_values=['nan', 'NaN', ''],
                keep_default_na=False
            )
            self.data = self.data.fillna('')
            
            self.original_data = self.data.copy()
            
            if 'text' in self.data.columns and 'sentence' not in self.data.columns:
                self.data['sentence'] = self.data['text']
            
            required_columns = ['sentence', 'entity1', 'entity1_label', 'entity2', 'entity2_label', 'relation']
            for col in required_columns:
                if col not in self.data.columns:
                    self.data[col] = ''
            
            self.total_sentences = len(self.data)
            self.current_index = 0
            self.saved_rows = []
            self.skipped_indices = set()
            self.processed_indices = set()
            self.undo_stack.clear()
            
            self._show_message(f"Successfully loaded {self.total_sentences} sentences", "success")
            
        except Exception as e:
            self.error_handler.log_error(e, "Loading CSV file")
            self._show_message(f"Error loading file: {str(e)}", "error")
            self.data = pd.DataFrame()
            self.original_data = pd.DataFrame()
            self.total_sentences = 0

    def compose(self) -> ComposeResult:
        """Show file selection or sentence editing interface"""
        try:
            # If no file is selected, show file selection interface
            if not self.file_selected:
                yield Label("Select CSV File to Edit", id="file-selection-title")
                with Horizontal():
                    yield Label("CSV File:")
                    yield Select(
                        self.get_csv_files(),
                        id="csv-file-select"
                    )
                with Horizontal():
                    yield Label("Output File:")
                    yield Input(
                        placeholder="Enter output filename (e.g., my_annotations.csv)",
                        value="edited_output.csv",
                        id="output-file-input"
                    )
                yield Button("Load File", id="load-file", variant="primary")
                yield Button("Back", id="back", variant="warning")
                yield Footer()
                return
            
            # Show editing interface if file is loaded
            self._show_message(f"Loaded {self.total_sentences} sentences for editing", "info")
            if not self.data.empty and self.current_index < self.total_sentences:
                row = self.data.iloc[self.current_index]
                yield Label(f"Editing: {self.input_csv.name}")
                yield Label(f"Sentence {self.current_index + 1} of {self.total_sentences}")
                yield RowEditor(row, self.current_index, 
                              ["PERSON", "ORG", "LOC", "EVENT", "DATE", "PRODUCT"], 
                              ["works_for", "lives_in", "part_of"])
                
                # Navigation buttons container
                with Horizontal():
                    yield Button("Skip", id="skip", variant="primary")
                    yield Button("Save & Next", id="save-next", variant="success")
                    yield Button("Finish", id="finish", variant="warning")
            else:
                yield Label("No more sentences to edit")
                yield Button("Finish", id="finish", variant="warning")
            
            yield Footer()
            
        except Exception as e:
            self._show_message(f"Error in compose: {str(e)}", "error")
            yield Label("Error loading content")
            yield Button("Finish", id="finish", variant="error")
            yield Footer()

    def _save_state_for_undo(self):
        """Save current state for undo functionality"""
        if self.data is not None and not self.data.empty:
            state = {
                'index': self.current_index,
                'dataframe': self.data.copy(),
                'saved_rows': self.saved_rows.copy(),
                'skipped_indices': self.skipped_indices.copy(),
                'processed_indices': self.processed_indices.copy(),
                'timestamp': datetime.now()
            }
            
            self.undo_stack.append(state)
            
            # Limit undo stack size
            if len(self.undo_stack) > self.max_undo_steps:
                self.undo_stack.pop(0)
    
    def action_undo(self):
        """Undo last change"""
        if not self.undo_stack:
            self._show_message("No actions to undo", "warning")
            return
        
        try:
            last_state = self.undo_stack.pop()
            
            self.data = last_state['dataframe']
            self.current_index = last_state['index']
            self.saved_rows = last_state['saved_rows']
            self.skipped_indices = last_state['skipped_indices']
            self.processed_indices = last_state['processed_indices']
            
            # Refresh display
            self._refresh_current_sentence()
            self._show_message("Undid last action", "info")
            
        except Exception as e:
            self._show_message(f"Undo failed: {str(e)}", "error")
    
    def action_quit(self):
        """Quit the screen"""
        self.app.pop_screen()
    
    def action_save_current(self):
        """Save current sentence"""
        self._save_current()
    
    def action_skip_current(self):
        """Skip current sentence"""
        self._skip_current()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        button_id = event.button.id
        
        if button_id == "load-file":
            self._load_selected_file()
        elif button_id == "back":
            self.app.pop_screen()
        elif button_id == "skip":
            self._skip_current()
        elif button_id == "save-next":
            self._save_current()
        elif button_id == "finish":
            self._finish_editing()

    def _load_selected_file(self) -> None:
        """Load the selected CSV file and switch to editing interface"""
        try:
            csv_file = self.query_one("#csv-file-select", Select).value
            if not csv_file or csv_file == Select.BLANK:
                self._show_message("Please select a CSV file", "warning")
                return
            
            output_filename = self.query_one("#output-file-input", Input).value.strip()
            if not output_filename:
                self._show_message("Please enter an output filename", "warning")
                return
            
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            
            csv_data_dir = Path(__file__).parent.parent / "data" / "csv_data"
            self.input_csv = csv_data_dir / csv_file
            
            if not self.input_csv.exists():
                self._show_message(f"File not found: {csv_file}", "error")
                return
            
            annotated_data_dir = Path(__file__).parent.parent / "data" / "annotated_csv_data"
            annotated_data_dir.mkdir(parents=True, exist_ok=True)
            self.output_csv = annotated_data_dir / output_filename
            
            # Load the file
            self._load_csv_file(self.input_csv)
            self.file_selected = True
            
            # Force a complete refresh by switching to the main screen and back
            self.app.pop_screen()
            self.app.push_screen(NEREditorScreen(self.input_csv, output_filename))
            
        except Exception as e:
            self.error_handler.log_error(e, "Loading file")
            self._show_message(f"Error loading file: {str(e)}", "error")

    def _skip_current(self) -> None:
        """Skip the current sentence (mark it as skipped and move to next)"""
        # Save state for undo
        self._save_state_for_undo()
        
        self.skipped_indices.add(self.current_index)
        self.processed_indices.add(self.current_index)
        self._show_message(f"Sentence {self.current_index + 1} skipped", "info")
        
        # Small delay to prevent too-fast transitions that cause crashes
        time.sleep(0.1)
        
        self._next_sentence()

    def _next_sentence(self) -> None:
        """Move to next sentence and refresh the screen"""
        self.current_index += 1
        
        if self.current_index < self.total_sentences:
            # Instead of creating a new screen, just refresh the current content
            self._refresh_current_sentence()
        else:
            self.current_index = self.total_sentences - 1  # Stay at last sentence
            self._show_message("No more sentences to edit", "warning")

    def _refresh_current_sentence(self) -> None:
        """Refresh the current sentence display without creating a new screen"""
        try:
            # Clear any existing AutoComplete widgets to prevent conflicts
            autocompletes = self.query(CustomAutoComplete)
            for ac in autocompletes:
                try:
                    ac.remove()
                except:
                    pass
            
            # Remove the old row editor if it exists
            try:
                old_editor = self.query_one(RowEditor)
                old_editor.remove()
            except:
                pass
            
            # Update the sentence counter label
            try:
                counter_label = self.query("Label")[1]  # Second label should be the counter
                counter_label.update(f"Sentence {self.current_index + 1} of {self.total_sentences}")
            except:
                pass
            
            # Create new row editor for current sentence
            if self.current_index < self.total_sentences:
                row = self.data.iloc[self.current_index]
                new_editor = RowEditor(row, self.current_index, 
                                     ["PERSON", "ORG", "LOC", "EVENT", "DATE", "PRODUCT"], 
                                     ["works_for", "lives_in", "part_of"])
                
                # Find the button container and mount the new editor before it
                try:
                    button_container = self.query_one(Horizontal)
                    self.mount(new_editor, before=button_container)
                except:
                    # If button container not found, mount at the end
                    self.mount(new_editor)
                    
        except Exception as e:
            self.notify(f"Error refreshing sentence: {str(e)}", severity="error")


    def _save_current(self) -> None:
        """Save the current sentence edits and move to next"""
        try:
            # Save state for undo
            self._save_state_for_undo()
            
            editor = self.query_one(RowEditor)
            current_row = self.data.iloc[self.current_index]
            
            # Get input values directly from the editor's children
            row_data = {
                'sentence': current_row['sentence'],
                'entity1': editor.query_one("Input#entity1-0").value,
                'entity1_label': editor.query_one("Input#entity1_label-0").value,
                'entity2': editor.query_one("Input#entity2-0").value,
                'entity2_label': editor.query_one("Input#entity2_label-0").value,
                'relation': editor.query_one("Input#relation-0").value,
                'edited_at': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                'original_index': self.current_index  # Keep track of original position
            }
            
            # Add to saved rows
            self.saved_rows.append(row_data)
            self.processed_indices.add(self.current_index)
            
            # Save immediately to output CSV after each edit (if auto-save enabled)
            if self.auto_save_enabled:
                df = pd.DataFrame(self.saved_rows)
                # Remove the original_index column before saving
                df_to_save = df.drop('original_index', axis=1, errors='ignore')
                df_to_save.to_csv(self.output_csv, index=False)
                
                self._show_message(f"Auto-saved to {self.output_csv.name}", "info")
            else:
                self._show_message("Sentence saved (will write on finish)", "info")
            
            # Small delay to prevent too-fast transitions that cause crashes
            time.sleep(0.1)
            
            self._next_sentence()
        except Exception as e:
            self._show_message(f"Error saving sentence: {str(e)}", "error")

    def _finish_editing(self) -> None:
        """Save final edits and update input file by removing processed sentences"""
        try:
            # Save final output file with all saved sentences
            if self.saved_rows:
                df = pd.DataFrame(self.saved_rows)
                # Remove the original_index column before saving
                df_to_save = df.drop('original_index', axis=1, errors='ignore')
                df_to_save.to_csv(self.output_csv, index=False)
                self._show_message(f"Saved {len(self.saved_rows)} sentences to {self.output_csv.name}", "success")
            
            # Update input file by removing all processed sentences (saved + skipped)
            if self.processed_indices and not self.original_data.empty:
                # Keep only unprocessed sentences in the input file
                remaining_indices = [i for i in range(len(self.original_data)) if i not in self.processed_indices]
                remaining_data = self.original_data.iloc[remaining_indices]
                
                if not remaining_data.empty:
                    remaining_data.to_csv(self.input_csv, index=False)
                    self._show_message(f"Updated {self.input_csv.name}: {len(remaining_data)} sentences remaining", "info")
                else:
                    # If no sentences remain, create empty file or remove it
                    remaining_data.to_csv(self.input_csv, index=False)
                    self._show_message(f"All sentences processed. {self.input_csv.name} is now empty.", "info")
            
            # Show summary
            total_processed = len(self.processed_indices)
            saved_count = len(self.saved_rows)
            skipped_count = len(self.skipped_indices)
            remaining_count = self.total_sentences - total_processed
            
            self._show_message(f"Summary: {saved_count} saved, {skipped_count} skipped, {remaining_count} remaining", "success")
            self.app.pop_screen()
            
        except Exception as e:
            self._show_message(f"Error finishing editing: {e}", "error")
    
    def _show_message(self, message: str, msg_type: str = "info"):
        """Show message to user with appropriate styling"""
        severity_map = {
            "info": "information",
            "success": "information", 
            "warning": "warning",
            "error": "error"
        }
        
        severity = severity_map.get(msg_type, "information")
        self.notify(message, severity=severity)
