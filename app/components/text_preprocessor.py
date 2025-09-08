from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Markdown, TextArea, Checkbox, Footer
from textual.screen import Screen
from textual.binding import Binding
from textual import events
from pathlib import Path
import re
import json
from typing import List, Tuple
from utils.clean_text import preprocess_stream
from components.processing_preview_screen import ProcessingPreviewScreen
import tempfile


class TextPreprocessorScreen(Screen):
    """Text preprocessing interface for preparing raw text files"""

    BINDINGS = [
        Binding(key="p,P", action="preview", description="Preview Processing"),
        Binding(key="s,S", action="save", description="Process & Save"),
        Binding(key="b,B", action="back", description="Back to Menu"),
        Binding(key="escape", action="blur_input", description="Exit Input/Back", show=False),
        Binding(key="tab", action="focus_next", description="Next Field", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="preprocessor-container"):
            with VerticalScroll(id="main-content"):
                yield Label("Text Preprocessor", id="preprocessor-title")

                yield Label("Select Text File:", id="file-label")
                yield Select(
                    self.get_text_files(),
                    id="file-select"
                )

                yield Label("Text Preview:", id="preview-label")
                with VerticalScroll(id="preview-container"):
                    yield TextArea("Select a file to see preview...", id="text-preview", read_only=True)

                with Vertical(id="options-container"):
                    yield Label("Processing Options:", id="options-title")
                    
                    yield Checkbox("Clean Gutenberg text (remove headers/footers)", id="clean-gutenberg", value=False)
                    
                    with Horizontal(id="options-grid"):
                        with Vertical(id="boundaries-column"):
                            with Horizontal(id="start-row"):
                                yield Label("Start Line:", id="start-label")
                                yield Input(placeholder="1", value="1", id="start-input")
                            with Horizontal(id="end-row"):
                                yield Label("End Line:", id="end-label")
                                yield Input(placeholder="auto", value="auto", id="end-input")
                        
                        # Middle column - Split method and size
                        with Vertical(id="split-column"):
                            with Horizontal(id="split-row"):
                                yield Label("Split Method:", id="split-label")
                                yield Select([
                                    ("Sentences", "sentences"),
                                    ("Paragraphs", "paragraphs"),
                                    ("Chapters/Books", "chapters"),
                                    ("Custom Size", "custom")
                                ], id="split-select", value="paragraphs")
                            with Horizontal(id="size-row"):
                                yield Label("Max Chunk Size:", id="size-label")
                                yield Input(placeholder="500", value="500", id="size-input")
                            with Horizontal(id="chapter-row", classes="hidden"):
                                yield Label("Chapter/Book Word:", id="chapter-label")
                                yield Input(placeholder="CHAPTER", value="CHAPTER", id="chapter-input")
                        
                        # Right column - Output format
                        with Vertical(id="format-column"):
                            with Horizontal(id="format-row"):
                                yield Label("Output Format:", id="format-label")
                                yield Select([
                                    ("Plain Text with Separators", "plain"),
                                    ("JSON Array", "json"),
                                    ("One File Per Chunk", "separate")
                                ], id="format-select", value="plain")

            # Footer with keyboard shortcuts (always visible at bottom)
            yield Footer()

    def on_mount(self) -> None:
        """Initialize screen"""
        self.current_text = ""
        self.processed_chunks = []
        self._mounted = True
        # Add debug timing to see layout after everything is rendered
        self.set_timer(0.1, self.debug_layout)

    def debug_layout(self) -> None:
        """Debug function to print actual widget positions and identify spacing issues"""
        try:
            elements = [
                "#preprocessor-title", 
                "#file-label",
                "#file-select",
                "#preview-label"
            ]
            
            print("\n=== LAYOUT DEBUG ===")
            for elem_id in elements:
                try:
                    widget = self.query_one(elem_id)
                    region = widget.region
                    print(f"{elem_id:20} | pos: ({region.x:3}, {region.y:3}) | size: {region.width:3}x{region.height:3}")
                except Exception as e:
                    print(f"{elem_id:20} | ERROR: {e}")
            
            # Calculate gap between top-section and file-label
            try:
                top_section = self.query_one("#top-section")
                file_label = self.query_one("#file-label")
                gap = file_label.region.y - (top_section.region.y + top_section.region.height)
                print(f"{'GAP':20} | {gap} units between top-section and file-label")
            except Exception as e:
                print(f"Gap calculation failed: {e}")
            
            print("==================\n")
        except Exception as e:
            print(f"Debug failed: {e}")

    def get_text_files(self):
        """Get list of text files from app/data/raw_data/"""
        raw_data_dir = Path(__file__).parent.parent / "data" / "raw_data"
        if not raw_data_dir.exists():
            return [("No text files found", "")]
        
        text_files = list(raw_data_dir.glob("*.txt"))
        if not text_files:
            return [("No text files found", "")]
        
        return [(f.name, str(f)) for f in text_files]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back-button":
            self.action_back()
        elif event.button.id == "preview-button":
            self.action_preview()
        elif event.button.id == "process-button":
            self.action_save()

    def action_preview(self):
        """Preview processing action"""
        self.preview_processing()

    def action_save(self):
        """Process and save action"""
        self.process_and_save()

    def action_back(self):
        """Back to menu action"""
        self.app.pop_screen()

    def action_blur_input(self):
        """Exit input editing mode or go back"""
        focused = self.app.focused
        if focused and isinstance(focused, (Input, TextArea)):
            # If an input is focused, blur it to exit editing mode
            focused.blur()
            # Don't pop screen when just blurring inputs
        else:
            # If no input is focused, go back to previous screen
            self.app.pop_screen()

    def action_focus_next(self):
        """Move to next focusable widget - only if not editing"""
        focused = self.app.focused
        if not focused or not isinstance(focused, (Input, TextArea)):
            # Only allow focus changes when not actively editing
            self.focus_next()

    def on_key(self, event: events.Key) -> None:
        focused = self.app.focused
        if event.key == "escape":
            if focused and isinstance(focused, (Input, TextArea)):
                focused.blur()
            else:
                self.app.pop_screen()
            return
        
        if focused and isinstance(focused, (Input, TextArea)):
            return
        
        if event.key.lower() == 'p':
            event.prevent_default()
            self.action_preview()
        elif event.key.lower() == 's':
            event.prevent_default()
            self.action_save()
        elif event.key.lower() == 'b':
            event.prevent_default()
            self.action_back()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle file selection changes"""
        if event.select.id == "file-select":
            if event.value and event.value != "":
                # Valid file selected
                self.load_text_file(Path(event.value))
            else:
                # No file selected or back to placeholder - clear preview
                self.current_text = ""
                self.query_one("#text-preview", TextArea).text = "Select a file to see preview..."
                self.query_one("#end-input", Input).value = "auto"
        elif event.select.id == "split-select":
            # Show/hide chapter word input based on split method
            chapter_row = self.query_one("#chapter-row")
            if event.value == "chapters":
                chapter_row.remove_class("hidden")
            else:
                chapter_row.add_class("hidden")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes"""
        if event.checkbox.id == "clean-gutenberg":
            # Reload file when cleaning option changes
            file_select = self.query_one("#file-select", Select)
            if file_select.value:
                self.load_text_file(Path(file_select.value))

    def load_text_file(self, file_path: Path) -> None:
        """Load and preview selected text file"""
        try:
            # Validate file path
            if not file_path or not file_path.exists():
                self.query_one("#text-preview", TextArea).text = "Error: File not found"
                return
                
            # Check if Gutenberg cleaning should be applied
            should_clean = self.query_one("#clean-gutenberg", Checkbox).value if hasattr(self, '_mounted') else True
            
            if should_clean and self.is_gutenberg_file(file_path):
                # Apply Gutenberg cleaning to a temporary file
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
                    temp_path = temp_file.name
                
                try:
                    preprocess_stream(str(file_path), temp_path)
                    with open(temp_path, 'r', encoding='utf-8') as f:
                        self.current_text = f.read()
                finally:
                    # Clean up temp file
                    Path(temp_path).unlink(missing_ok=True)
            else:
                # Load file as-is
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.current_text = f.read()
            
            # Show preview (first 2000 characters)
            preview_text = self.current_text[:2000]
            if len(self.current_text) > 2000:
                preview_text += "\n\n... [File continues] ..."
            
            self.query_one("#text-preview", TextArea).text = preview_text
            
            # Show text info
            lines = self.current_text.split('\n')
            self.query_one("#end-input", Input).value = str(len(lines))
            
        except Exception as e:
            self.current_text = ""
            self.query_one("#text-preview", TextArea).text = f"Error loading file: {str(e)}"
            self.query_one("#end-input", Input).value = "auto"

    def is_gutenberg_file(self, file_path: Path) -> bool:
        """Check if file appears to be a Project Gutenberg ebook"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Check first few lines for Gutenberg markers
                first_lines = ''.join(f.readlines()[:50])
                return "PROJECT GUTENBERG" in first_lines.upper()
        except:
            return False

    def preview_processing(self) -> None:
        """Preview how the text will be processed"""
        if not self.current_text:
            # Show a message if no file is selected
            preview_data = {
                "cleaned_status": "No file selected",
                "split_method": "None",
                "chapter_word": "N/A",
                "output_format": "N/A"
            }
            self.app.push_screen(ProcessingPreviewScreen(preview_data, ["Please select a file first"]))
            return
        
        chunks = self.process_text(preview_only=True)
        
        # Prepare preview data
        cleaned_status = "✓ Applied" if self.query_one("#clean-gutenberg", Checkbox).value else "✗ Skipped"
        split_method = self.query_one("#split-select", Select).value
        chapter_word = self.query_one("#chapter-input", Input).value or "CHAPTER"
        output_format = self.query_one("#format-select", Select).value
        
        preview_data = {
            "cleaned_status": cleaned_status,
            "split_method": split_method,
            "chapter_word": chapter_word,
            "output_format": output_format
        }
        
        # Open preview in new screen
        self.app.push_screen(ProcessingPreviewScreen(preview_data, chunks))

    def process_text(self, preview_only: bool = False) -> List[str]:
        """Process text according to user settings"""
        if not self.current_text:
            return []
        
        # Get boundaries
        start_line = int(self.query_one("#start-input", Input).value or "1")
        end_input = self.query_one("#end-input", Input).value
        
        lines = self.current_text.split('\n')
        end_line = len(lines) if end_input == "auto" or not end_input else int(end_input)
        
        # Extract selected portion
        selected_lines = lines[start_line-1:end_line]
        text_portion = '\n'.join(selected_lines)
        
        # Get split method
        split_method = self.query_one("#split-select", Select).value
        max_size = int(self.query_one("#size-input", Input).value or "500")
        chapter_word = self.query_one("#chapter-input", Input).value or "CHAPTER"
        
        # Split text
        if split_method == "sentences":
            chunks = self.split_by_sentences(text_portion, max_size)
        elif split_method == "paragraphs":
            chunks = self.split_by_paragraphs(text_portion, max_size)
        elif split_method == "chapters":
            chunks = self.split_by_chapters(text_portion, max_size, chapter_word)
        else:  # custom
            chunks = self.split_by_size(text_portion, max_size)
        
        return chunks

    def split_by_sentences(self, text: str, max_size: int) -> List[str]:
        """Split text by sentences, respecting max size"""
        sentences = re.split(r'[.!?]+\s+', text)
        return self.group_by_size(sentences, max_size)

    def split_by_paragraphs(self, text: str, max_size: int) -> List[str]:
        """Split text by paragraphs, respecting max size"""
        # Try double newlines first, then fall back to single newlines for better paragraph detection
        if '\n\n' in text:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        else:
            # For texts with single newlines, split on single newlines but filter out very short lines
            paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 10]
        return self.group_by_size(paragraphs, max_size)

    def split_by_chapters(self, text: str, max_size: int, chapter_word: str = "CHAPTER") -> List[str]:
        """Split text by chapters/books using custom chapter word"""
        # Create flexible pattern that matches various formats:
        # CHAPTER I, Chapter 1, BOOK I, Book II, etc.
        chapter_pattern = rf'\n\s*({re.escape(chapter_word)}|{re.escape(chapter_word.lower())}|{re.escape(chapter_word.capitalize())})\s+[IVXLC\d]+.*?\n'
        chapters = re.split(chapter_pattern, text)
        chapters = [c.strip() for c in chapters if c.strip() and not re.match(rf'^({re.escape(chapter_word)}|{re.escape(chapter_word.lower())}|{re.escape(chapter_word.capitalize())})$', c.strip(), re.IGNORECASE)]
        return self.group_by_size(chapters, max_size)

    def split_by_size(self, text: str, max_size: int) -> List[str]:
        """Split text by character count"""
        chunks = []
        for i in range(0, len(text), max_size):
            chunks.append(text[i:i+max_size])
        return chunks

    def group_by_size(self, items: List[str], max_size: int) -> List[str]:
        """Group items together until reaching max_size"""
        chunks = []
        current_chunk = ""
        
        for item in items:
            if len(current_chunk) + len(item) + 1 <= max_size:
                current_chunk += " " + item if current_chunk else item
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = item
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def process_and_save(self) -> None:
        """Process text and save to preprocessed data folder"""
        chunks = self.process_text()
        if not chunks:
            return
        
        # Save processed chunks
        output_dir = Path(__file__).parent.parent / "data" / "preprocessed"
        output_dir.mkdir(exist_ok=True)
        
        # Generate filename based on original file
        file_select = self.query_one("#file-select", Select)
        if not file_select.value:
            return
            
        original_name = Path(file_select.value).stem
        output_format = self.query_one("#format-select", Select).value
        
        if output_format == "json":
            self.save_as_json(chunks, output_dir, original_name)
        elif output_format == "separate":
            self.save_as_separate_files(chunks, output_dir, original_name)
        else:  # plain
            self.save_as_plain_text(chunks, output_dir, original_name)

    def save_as_plain_text(self, chunks: List[str], output_dir: Path, original_name: str) -> None:
        """Save chunks as plain text with separators"""
        output_file = output_dir / f"{original_name}_preprocessed.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"=== CHUNK {i+1} ===\n")
                f.write(chunk)
                f.write(f"\n\n")
        
        self.show_success_message(output_file.name, len(chunks), f"Single file: {output_file}")

    def save_as_json(self, chunks: List[str], output_dir: Path, original_name: str) -> None:
        """Save chunks as JSON array"""
        output_file = output_dir / f"{original_name}_preprocessed.json"
        
        chunk_data = {
            "metadata": {
                "original_file": original_name,
                "total_chunks": len(chunks),
                "processing_options": self.get_processing_metadata()
            },
            "chunks": [
                {
                    "id": i + 1,
                    "content": chunk,
                    "length": len(chunk)
                } for i, chunk in enumerate(chunks)
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunk_data, f, indent=2, ensure_ascii=False)
        
        self.show_success_message(output_file.name, len(chunks), f"JSON file: {output_file}")

    def save_as_separate_files(self, chunks: List[str], output_dir: Path, original_name: str) -> None:
        """Save each chunk as a separate file"""
        chunk_dir = output_dir / f"{original_name}_chunks"
        chunk_dir.mkdir(exist_ok=True)
        
        for i, chunk in enumerate(chunks):
            chunk_file = chunk_dir / f"chunk_{i+1:03d}.txt"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk)
        
        # Also create a metadata file
        metadata_file = chunk_dir / "metadata.txt"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write(f"Original file: {original_name}\n")
            f.write(f"Total chunks: {len(chunks)}\n")
            f.write(f"Processing options:\n")
            for key, value in self.get_processing_metadata().items():
                f.write(f"  {key}: {value}\n")
        
        self.show_success_message(f"{len(chunks)} files", len(chunks), f"Directory: {chunk_dir}")

    def get_processing_metadata(self) -> dict:
        """Get current processing options as metadata"""
        return {
            "gutenberg_cleaning": self.query_one("#clean-gutenberg", Checkbox).value,
            "split_method": self.query_one("#split-select", Select).value,
            "max_chunk_size": self.query_one("#size-input", Input).value,
            "chapter_word": self.query_one("#chapter-input", Input).value,
            "start_line": self.query_one("#start-input", Input).value,
            "end_line": self.query_one("#end-input", Input).value
        }

    def show_success_message(self, file_info: str, chunk_count: int, location: str) -> None:
        """Show processing success message using notifications"""
        cleaned_status = "with Gutenberg cleaning" if self.query_one("#clean-gutenberg", Checkbox).value else "without cleaning"
        
        # Show success notification with key info
        self.notify(
            f"✅ Processing Complete! {file_info} - {chunk_count} chunks created {cleaned_status}",
            title="Text Processing Success",
            severity="information",
            timeout=5.0
        )
        
        # Show location info in a separate notification
        self.notify(
            f"📁 Saved to: {location}",
            title="Output Location", 
            severity="information",
            timeout=8.0
        )
