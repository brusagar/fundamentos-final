from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Markdown, Footer
from textual.screen import Screen
from textual.binding import Binding
from pathlib import Path
from models.entity_processor import EntityProcessor


class EntitySearchScreen(Screen):
    """Screen for searching entities in prediction files"""

    BINDINGS = [
        Binding(key="b,B", action="back", description="Back to Menu"),
        Binding(key="escape", action="blur_input", description="Exit Input/Back", show=False),
        Binding(key="tab", action="focus_next", description="Next Field", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Create entity search interface"""
        with Vertical(id="entity-search-container"):
            # Scrollable main content area
            with VerticalScroll(id="main-content"):
                yield Label("Entity Search", id="entity-search-title")

                # File selection
                yield Label("Predictions File:", id="file-label")
                yield Select(
                    self.get_prediction_files(),
                    id="file-select"
                )

                # Search input (initially hidden) - right above results
                yield Input(placeholder="Search for an entity...", id="entity-input", classes="hidden")
                    
                # Results area (initially hidden)
                with VerticalScroll(id="results-container", classes="hidden"):
                    yield Markdown(id="entity-results")

            # Footer with keyboard shortcuts (always visible at bottom)
            yield Footer()

    def on_mount(self) -> None:
        """Initialize entity processor when screen starts"""
        # Don't initialize until file is selected
        self.entity_processor = None

    def action_back(self):
        """Back to menu action"""
        self.app.pop_screen()

    def action_blur_input(self):
        """Exit input editing mode or go back"""
        focused = self.app.focused
        if focused and isinstance(focused, Input):
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
        
        if event.key.lower() == 'b':
            event.prevent_default()
            self.action_back()

    def get_prediction_files(self):
        """Get list of prediction JSON files"""
        # Check only spert/data/model_predictions directory
        spert_model_predictions_dir = Path(__file__).parent.parent.parent / "spert" / "data" / "model_predictions"
        
        prediction_files = []
        
        # Add files from spert/data/model_predictions
        if spert_model_predictions_dir.exists():
            for json_file in spert_model_predictions_dir.glob("*.json"):
                prediction_files.append((json_file.name, str(json_file)))
        
        if not prediction_files:
            return [("No prediction files found", "")]
        
        return prediction_files

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses"""
        # No buttons in this screen anymore
        pass

    async def on_input_changed(self, message: Input.Changed) -> None:
        """Handle search input changes"""
        if message.input.id == "entity-input" and self.entity_processor:
            if message.value:
                results = self.entity_processor.search(message.value)
                await self.display_entity_results(results)
            else:
                await self.query_one("#entity-results", Markdown).update("")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle file selection changes"""
        if event.select.id == "file-select":
            if event.value:
                # Initialize entity processor with selected file
                self.entity_processor = EntityProcessor(Path(event.value))
                
                # Hide file selection components
                self.query_one("#file-label").add_class("hidden")
                self.query_one("#file-select").add_class("hidden")
                
                # Show search components
                self.query_one("#entity-input").remove_class("hidden")
                self.query_one("#results-container").remove_class("hidden")
                
                # Clear any existing results and search input
                self.query_one("#entity-results", Markdown).update("")
                self.query_one("#entity-input", Input).value = ""

    async def display_entity_results(self, results: list) -> None:
        """Display pre-processed entity results"""
        if not results:
            await self.query_one("#entity-results", Markdown).update("No results found")
            return

        markdown_lines = []
        for entity in results:
            markdown_lines.extend([
                f"# {entity.text}",
                f"**Type:** {entity.type}",
                ""
            ])

            for context in entity.contexts:
                markdown_lines.extend([
                    "## Context",
                    f"_{context.sentence}_",
                    "",
                ])

                if context.other_entities:
                    markdown_lines.extend([
                        "### Other Entities in this Context",
                        *[f"- **{e['text']}** ({e['type']})" for e in context.other_entities],
                        ""
                    ])

                if context.relations:
                    markdown_lines.extend([
                        "### Relationships",
                        *[f"- **{entity.text}** → {r.type} → **{r.target}** ({r.target_type})" 
                          for r in context.relations],
                        ""
                    ])

                markdown_lines.append("---\n")

        await self.query_one("#entity-results", Markdown).update("\n".join(markdown_lines))
