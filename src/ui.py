import bisect

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


console = Console()


def show_status_line(current_cycle, max_cycle, mismatch_indexs, previous_idx, error_indexs):
    errors_total = len(error_indexs)

    if current_cycle in error_indexs:
        text_error = f"Error: {error_indexs.index(current_cycle) + 1}/{errors_total}"
    else:
        text_error = f"Errors: {errors_total}"

    text_t = (
        f" | [bold magenta]'t': Return to {previous_idx}[/bold magenta]"
        if previous_idx is not None
        else ""
    )

    console.print(
        f"\n[dim]cycle: {current_cycle}/{max_cycle} | "
        f"[bold red]{text_error}[/bold red] | "
        f"ENTER: Forward | ←/→: Move | "
        f"[bold cyan]'j': Jump | 'r': History[/bold cyan] | "
        f"[bold green]'b': Start | 'e': End[/bold green]"
        f"{text_t} | "
        f"[bold yellow]'s': Deltas[/bold yellow] | "
        f"[bold red]↑/↓: Errors[/bold red] | "
        f"'q': Exit[/dim]"
    )


def show_cycle(
    data,
    cycle_idx,
    mismatch_indexs=None,
    error_indexs=None,
    jump_history=None,
    history_selection_idx=None,
    max_cycle=0,
    show_deltas=True,
):
    if mismatch_indexs is None:
        mismatch_indexs = []

    if error_indexs is None:
        error_indexs = []

    if jump_history is None:
        jump_history = []

    status = data[cycle_idx]
    prev_status = data[cycle_idx - 1] if cycle_idx > 0 else {}

    d_vals = status.get("dut_values", {})
    r_vals = status.get("ref_values", {})
    inputs = status.get("inputs", {})
    error  = status.get("error", {})

    prev_d_vals = prev_status.get("dut_values", {})
    prev_r_vals = prev_status.get("ref_values", {})
    prev_inputs = prev_status.get("inputs", {})

    title = Text(
        f"HADES-V VISUALIZER | CLK Cycle {status['cycle']}",
        style="bold cyan",
        justify="center",
    )

    table_comparison = Table(show_header=True, header_style="bold magenta", expand=True)
    table_comparison.add_column("Signal", style="dim")
    table_comparison.add_column("DUT Value", justify="right")
    table_comparison.add_column("REF Value", justify="right")

    for key in d_vals.keys():
        dut = str(d_vals.get(key, "N/A"))
        ref = str(r_vals.get(key, "N/A"))

        prev_dut = str(prev_d_vals.get(key, dut)) if prev_status else dut
        prev_ref = str(prev_r_vals.get(key, ref)) if prev_status else ref

        dut_changed = dut != prev_dut
        ref_changed = ref != prev_ref

        ind_dut = " [bold yellow]●[/bold yellow]" if (dut_changed and show_deltas) else "  "
        ind_ref = " [bold yellow]●[/bold yellow]" if (ref_changed and show_deltas) else "  "

        if (dut != ref):
            if (error == 1):
                color = "bold red"
            else:
                color = "orange3"
        else:
            color = "green"

        table_comparison.add_row(
            key,
            f"[{color}]{dut}[/{color}]{ind_dut}",
            f"[{color}]{ref}[/{color}]{ind_ref}",
        )

    table_ctx = Table(show_header=True, header_style="bold yellow", expand=True)
    table_ctx.add_column("Input Signal", style="dim")
    table_ctx.add_column("Value", justify="right")

    for key, val in inputs.items():
        formatted_key = key.replace("_", " ").title()
        str_val = str(val)

        prev_val = str(prev_inputs.get(key, str_val)) if prev_status else str_val
        changed = str_val != prev_val

        ind_ctx = " [bold cyan]●[/bold cyan]" if (changed and show_deltas) else "  "
        table_ctx.add_row(formatted_key, f"{str_val}{ind_ctx}")

    table_hist = Table(show_header=True, header_style="bold green", expand=True)
    table_hist.add_column("Near Errors", justify="center")
    table_hist.add_column("Jump Log", justify="center")

    pos = bisect.bisect_left(error_indexs, cycle_idx)
    start_pos = max(0, pos - 2)
    end_pos = min(len(error_indexs), pos + 3)
    error_window = error_indexs[start_pos:end_pos]

    max_rows = max(len(error_window), len(jump_history), 7)

    for i in range(max_rows):
        if i < len(error_window):
            err_c = error_window[i]
            err_str = f"[bold red]> {err_c} <[/bold red]" if err_c == cycle_idx else str(err_c)
        else:
            err_str = ""

        if i < len(jump_history):
            jmp_c = jump_history[i]
            if history_selection_idx == i:
                jmp_str = f"[black on white] {jmp_c} [/black on white]"
            elif jmp_c == cycle_idx:
                jmp_str = f"[bold cyan]> {jmp_c} <[/bold cyan]"
            else:
                jmp_str = str(jmp_c)
        else:
            jmp_str = ""

        table_hist.add_row(err_str, jmp_str)

    console.clear()
    console.print(Panel(title, border_style="cyan"))

    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=5)
    grid.add_column(ratio=3)
    grid.add_column(ratio=2)

    grid.add_row(
        Panel(table_comparison, title="[bold blue]EXECUTE STAGE[/bold blue]", border_style="blue"),
        Panel(table_ctx, title="[bold yellow]SYSTEM CONTEXT[/bold yellow]", border_style="yellow"),
        Panel(table_hist, title="[bold green]HISTORY LOG[/bold green]", border_style="green"),
    )

    console.print(grid)

    window_size = 40
    timeline_text = Text()

    start_c = cycle_idx - window_size
    end_c = cycle_idx + window_size

    timeline_text.append(f"{max(0, start_c):<6} ", style="bold white")

    for c in range(start_c, end_c + 1):
        if c < 0 or c > max_cycle:
            timeline_text.append(" ", style="dim")
        elif c == cycle_idx:
            if c in error_indexs:
                timeline_text.append("█", style="bold red")
            else:
                timeline_text.append("█", style="bold cyan")
        elif c in error_indexs:
            timeline_text.append("●", style="bold red")
        else:
            timeline_text.append("━", style="dim")

    timeline_text.append(f" {min(max_cycle, end_c):>6}", style="bold white")
    console.print(
        Panel(
            timeline_text,
            title="[bold white]TIMELINE ERRORS[/bold white]",
            border_style="white",
            expand=True,
        )
    )

    timeline_mismatch = Text()

    start_c = cycle_idx - window_size
    end_c = cycle_idx + window_size

    timeline_mismatch.append(f"{max(0, start_c):<6} ", style="bold white")

    for c in range(start_c, end_c + 1):
        if c < 0 or c > max_cycle:
            timeline_mismatch.append(" ", style="dim")
        elif c == cycle_idx:
            if c in mismatch_indexs:
                timeline_mismatch.append("█", style="bold dark_orange")
            else:
                timeline_mismatch.append("█", style="bold cyan")
        elif c in mismatch_indexs:
            timeline_mismatch.append("●", style="bold orange1")
        else:
            timeline_mismatch.append("━", style="dim")

    timeline_mismatch.append(f" {min(max_cycle, end_c):>6}", style="bold white")
    console.print(
        Panel(
            timeline_mismatch,
            title="[bold white]TIMELINE MISMATCH[/bold white]",
            border_style="white",
            expand=True,
        )
    )