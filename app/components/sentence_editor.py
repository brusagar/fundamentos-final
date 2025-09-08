from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.containers import VerticalScroll, Grid, Horizontal, Vertical
from textual.widgets import Button, Input, Markdown, Label, Static, Select
from textual_autocomplete import AutoComplete as BaseAutoComplete
from textual_autocomplete._autocomplete import DropdownItem, TargetState
from utils.custom_autocomplete import CustomAutoComplete
from textual import log, work

import json
import pandas as pd
from pathlib import Path

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
    def __init__(self, input_csv=None, output_filename="edited_output.csv"):
        super().__init__()
        self.input_csv = Path(input_csv) if input_csv else None
        
        # Set output path to app/data/annotated_csv_data/
        annotated_data_dir = Path(__file__).parent.parent / "data" / "annotated_csv_data"
        annotated_data_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        
        # Ensure the filename ends with .csv
        if not output_filename.endswith('.csv'):
            output_filename += '.csv'
        
        self.output_csv = annotated_data_dir / output_filename
        self.output_filename = output_filename  # Store just the filename for passing to new instances
        
        self.current_index = 0
        self.saved_rows = []  # Rows that were saved (will be in output)
        self.skipped_indices = set()  # Indices of rows that were skipped
        self.processed_indices = set()  # All indices that have been processed
        self.data = pd.DataFrame()
        self.original_data = pd.DataFrame()  # Keep original for restoration
        self.total_sentences = 0
        self.file_selected = False
        
        # If input_csv is provided, load it immediately
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
        """Load the selected CSV file"""
        try:
            # Read CSV with string type for all columns
            self.data = pd.read_csv(
                csv_path,
                dtype=str,  # Force all columns to be strings
                na_values=['nan', 'NaN', ''],  # Handle various null values
                keep_default_na=False  # Don't interpret additional strings as NA
            )
            # Replace NaN with empty strings
            self.data = self.data.fillna('')
            
            # Keep a copy of original data
            self.original_data = self.data.copy()
            
            # Handle different CSV formats
            if 'text' in self.data.columns and 'sentence' not in self.data.columns:
                # Convert simple text format to sentence format
                self.data['sentence'] = self.data['text']
            
            # Add missing columns if they don't exist
            required_columns = ['sentence', 'entity1', 'entity1_label', 'entity2', 'entity2_label', 'relation']
            for col in required_columns:
                if col not in self.data.columns:
                    self.data[col] = ''
            
            self.total_sentences = len(self.data)
            self.current_index = 0
            self.saved_rows = []
            self.skipped_indices = set()
            self.processed_indices = set()
        except FileNotFoundError:
            self.notify("Input CSV file not found", severity="error")
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
                return
            
            # Show editing interface if file is loaded
            self.notify(f"Loaded {self.total_sentences} sentences for editing", severity="information")
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
        except Exception as e:
            self.notify(f"Error in compose: {str(e)}", severity="error")
            yield Label("Error loading content")
            yield Button("Finish", id="finish", variant="error")

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
                self.notify("Please select a CSV file", severity="warning")
                return
            
            # Get the output filename from user input
            output_filename = self.query_one("#output-file-input", Input).value.strip()
            if not output_filename:
                self.notify("Please enter an output filename", severity="warning")
                return
            
            # Ensure the filename ends with .csv
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            
            # Build path to selected file
            csv_data_dir = Path(__file__).parent.parent / "data" / "csv_data"
            self.input_csv = csv_data_dir / csv_file
            
            if not self.input_csv.exists():
                self.notify(f"File not found: {csv_file}", severity="error")
                return
            
            # Set output path with user-specified filename
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
            self.notify(f"Error loading file: {str(e)}", severity="error")

    def _skip_current(self) -> None:
        """Skip the current sentence (mark it as skipped and move to next)"""
        self.skipped_indices.add(self.current_index)
        self.processed_indices.add(self.current_index)
        self.notify(f"Sentence {self.current_index + 1} skipped", severity="information")
        
        # Small delay to prevent too-fast transitions that cause crashes
        import time
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
            self.notify("No more sentences to edit", severity="warning")

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
            
            # Save immediately to output CSV after each edit
            df = pd.DataFrame(self.saved_rows)
            # Remove the original_index column before saving
            df_to_save = df.drop('original_index', axis=1, errors='ignore')
            df_to_save.to_csv(self.output_csv, index=False)
            
            self.notify(f"Sentence saved to {self.output_csv}", severity="information")
            
            # Small delay to prevent too-fast transitions that cause crashes
            import time
            time.sleep(0.1)
            
            self._next_sentence()
        except Exception as e:
            self.notify(f"Error saving sentence: {str(e)}", severity="error")

    def _finish_editing(self) -> None:
        """Save final edits and update input file by removing processed sentences"""
        try:
            # Save final output file with all saved sentences
            if self.saved_rows:
                df = pd.DataFrame(self.saved_rows)
                # Remove the original_index column before saving
                df_to_save = df.drop('original_index', axis=1, errors='ignore')
                df_to_save.to_csv(self.output_csv, index=False)
                self.notify(f"Saved {len(self.saved_rows)} sentences to {self.output_csv}")
            
            # Update input file by removing all processed sentences (saved + skipped)
            if self.processed_indices and not self.original_data.empty:
                # Keep only unprocessed sentences in the input file
                remaining_indices = [i for i in range(len(self.original_data)) if i not in self.processed_indices]
                remaining_data = self.original_data.iloc[remaining_indices]
                
                if not remaining_data.empty:
                    remaining_data.to_csv(self.input_csv, index=False)
                    self.notify(f"Updated {self.input_csv.name}: {len(remaining_data)} sentences remaining")
                else:
                    # If no sentences remain, create empty file or remove it
                    remaining_data.to_csv(self.input_csv, index=False)
                    self.notify(f"All sentences processed. {self.input_csv.name} is now empty.")
            
            # Show summary
            total_processed = len(self.processed_indices)
            saved_count = len(self.saved_rows)
            skipped_count = len(self.skipped_indices)
            remaining_count = self.total_sentences - total_processed
            
            self.notify(f"Summary: {saved_count} saved, {skipped_count} skipped, {remaining_count} remaining")
            self.app.pop_screen()
            
        except Exception as e:
            self.notify(f"Error finishing editing: {e}", severity="error")
