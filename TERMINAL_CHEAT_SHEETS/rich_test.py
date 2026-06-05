# --- Rich ---

from rich.console import Console

from rich.panel import Panel

from rich.text import Text

console = Console()

console.print("[bold red]text[/bold red]")  # markup

console.print(Panel("content", title="hi"))  # panel

console.rule("[dim]divider[/dim]")  # horizontal rule

t = Text()

t.append("hello", style="bold blue")  # programmatic text

console.print("[bold bright_yellow on dark_red] ⚠ HIGH BLOOD ALCOHOL ⚠ [/bold bright_yellow on dark_red]")


input()
