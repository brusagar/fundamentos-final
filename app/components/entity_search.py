from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Input, Label, Select, Markdown, Footer
from textual.screen import Screen
from textual.binding import Binding
from pathlib import Path
from models.entity_processor import EntityProcessor


class EntitySearchScreen(Screen):
    """Entity search and exploration interface"""

    BINDINGS = [
        Binding(key="b,B", action="back", description="Back to Menu"),
        Binding(key="escape", action="blur_input", description="Exit Input/Back", show=False),
        Binding(key="tab", action="focus_next", description="Next Field", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="entity-search-container"):
            with VerticalScroll(id="main-content"):
                yield Label("Entity Search", id="entity-search-title")

                yield Label("Predictions File:", id="file-label")
                yield Select(
                    self.get_prediction_files(),
                    id="file-select"
                )

                yield Input(placeholder="Search for an entity...", id="entity-input", classes="hidden")
                    
                with VerticalScroll(id="results-container", classes="hidden"):
                    yield Markdown(id="entity-results")

            yield Footer()

    def on_mount(self) -> None:
        self.entity_processor = None

    def action_back(self):
        self.app.pop_screen()

    def action_blur_input(self):
        focused = self.app.focused
        if focused and isinstance(focused, Input):
            focused.blur()
        else:
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
        spert_model_predictions_dir = Path(__file__).parent.parent.parent / "spert" / "data" / "model_predictions"
        
        prediction_files = []
        
        if spert_model_predictions_dir.exists():
            for json_file in spert_model_predictions_dir.glob("*.json"):
                prediction_files.append((json_file.name, str(json_file)))
        
        if not prediction_files:
            return [("No prediction files found", "")]
        
        return prediction_files

    def on_button_pressed(self, event: Button.Pressed) -> None:
        pass

    async def on_input_changed(self, message: Input.Changed) -> None:
        if message.input.id == "entity-input" and self.entity_processor:
            if message.value:
                results = self.entity_processor.search(message.value)
                await self.display_entity_results(results)
            else:
                await self.query_one("#entity-results", Markdown).update("")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "file-select":
            if event.value:
                self.entity_processor = EntityProcessor(Path(event.value))
                
                self.query_one("#file-label").add_class("hidden")
                self.query_one("#file-select").add_class("hidden")
                
                self.query_one("#entity-input").remove_class("hidden")
                self.query_one("#results-container").remove_class("hidden")
                
                self.query_one("#entity-results", Markdown).update("")
                self.query_one("#entity-input", Input).value = ""

    async def display_entity_results(self, results: list) -> None:
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
