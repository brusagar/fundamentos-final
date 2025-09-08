from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Markdown, Label
from textual.screen import Screen
from typing import List


class ProcessingPreviewScreen(Screen):
    """Screen for displaying text processing preview"""

    def __init__(self, preview_data: dict, chunks: List[str]):
        super().__init__()
        self.preview_data = preview_data
        self.chunks = chunks

    def compose(self) -> ComposeResult:
        """Create processing preview interface"""
        with Vertical(id="preview-screen-container"):
            yield Label("Processing Preview", id="preview-screen-title")

            # Scrollable preview results
            with VerticalScroll(id="preview-results-container"):
                yield Markdown("", id="preview-results")

            # Back button
            yield Button("Back", id="back-button", variant="warning")

    def on_mount(self) -> None:
        """Initialize preview when screen loads"""
        self.show_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        if event.button.id == "back-button":
            self.app.pop_screen()

    def show_preview(self) -> None:
        """Display the processing preview"""
        preview_lines = [
            f"# Processing Preview",
            f"**Gutenberg Cleaning:** {self.preview_data['cleaned_status']}",
            f"**Split Method:** {self.preview_data['split_method']}" + (f" (using '{self.preview_data['chapter_word']}')" if self.preview_data['split_method'] == "chapters" else ""),
            f"**Output Format:** {self.preview_data['output_format']}",
            f"**Total chunks:** {len(self.chunks)}",
            f"**Average chunk size:** {sum(len(chunk) for chunk in self.chunks) // len(self.chunks) if self.chunks else 0} characters",
            f"**Total characters:** {sum(len(chunk) for chunk in self.chunks)}",
            "",
            "## Sample Chunks:",
            ""
        ]
        
        # Show first 3 chunks as examples
        for i, chunk in enumerate(self.chunks[:3]):
            preview_lines.extend([
                f"### Chunk {i+1} ({len(chunk)} chars)",
                f"```",
                chunk[:200] + "..." if len(chunk) > 200 else chunk,
                f"```",
                ""
            ])
        
        if len(self.chunks) > 3:
            preview_lines.append(f"... and {len(self.chunks) - 3} more chunks")

        self.query_one("#preview-results", Markdown).update("\n".join(preview_lines))
