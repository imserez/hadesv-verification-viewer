import readchar
import yaml
from rich.prompt import IntPrompt

from data_loader import (
    load_raw_trace,
    fix_json_string,
    parse_pipeline_trace,
    find_mismatch_cycles,
    find_error_cycles
)
from navigation import (
    register_jump,
    get_next_mismatch,
    get_previous_mismatch,
)
from ui import show_cycle, show_status_line, console


def handle_jump(idx, max_cycle):
    new_cycle = IntPrompt.ask(
        f"\n[bold yellow]Enter cycle number to jump: (0 - {max_cycle})[/bold yellow]",
        default=idx,
    )

    if 0 <= new_cycle <= max_cycle:
        return new_cycle

    console.print("[bold red]Out of range.[/bold red]")
    readchar.readkey()
    return idx


def handle_history_mode(data, idx, mismatch_indexs, jump_history, max_cycle, show_deltas):
    if not jump_history:
        console.print("\n[orange3]Jump log is empty.[/orange3]")
        readchar.readkey()
        return idx, None

    selection = 0
    previous_idx = None

    while True:
        show_cycle(
            data,
            idx,
            mismatch_indexs=mismatch_indexs,
            jump_history=jump_history,
            history_selection_idx=selection,
            max_cycle=max_cycle,
            show_deltas=show_deltas,
        )

        console.print(
            "\n[bold black on white] HISTORY MODE [/bold black on white]"
            "[dim] | ↑/↓: Seleccionar | ENTER: Jump | 'q' o 'r': Cancel[/dim]"
        )

        cmd_r = readchar.readkey()

        if cmd_r.lower() in ["q", "r"] or cmd_r == readchar.key.ESC:
            return idx, None
        elif cmd_r == readchar.key.UP and selection > 0:
            selection -= 1
        elif cmd_r == readchar.key.DOWN and selection < len(jump_history) - 1:
            selection += 1
        elif cmd_r == readchar.key.ENTER:
            destino = jump_history[selection]
            if destino != idx:
                previous_idx = idx
                idx = destino
            return idx, previous_idx


def main():
    console.print("[dim]Loading and cleaning log...[/dim]")

    raw_data = load_raw_trace("pipeline_trace.json")
    clean_data = fix_json_string(raw_data)

    try:
        data = parse_pipeline_trace(clean_data)
    except Exception as e:
        console.print(f"\n[bold red]Error parsing JSON:[/bold red] {e}")
        raise SystemExit(1)

    mismatch_indexs = find_mismatch_cycles(data)
    error_indexs = find_error_cycles(data)

    max_cycle = len(data) - 2
    idx = 0
    previous_idx = None
    show_deltas = True
    jump_history = []

    while idx <= max_cycle:
        show_cycle(
            data,
            idx,
            mismatch_indexs=mismatch_indexs,
            error_indexs=error_indexs,
            jump_history=jump_history,
            max_cycle=max_cycle,
            show_deltas=show_deltas,
        )

        show_status_line(idx, max_cycle, mismatch_indexs, previous_idx, error_indexs)

        command = readchar.readkey()

        if command.lower() == "q":
            break

        elif command == readchar.key.LEFT:
            if idx > 0:
                idx -= 1

        elif command in (readchar.key.RIGHT, readchar.key.ENTER):
            if idx < max_cycle:
                idx += 1

        elif command.lower() == "s":
            show_deltas = not show_deltas

        elif command.lower() == "j":
            new_idx = handle_jump(idx, max_cycle)
            if new_idx != idx:
                previous_idx = idx
                idx = new_idx
                register_jump(idx, jump_history)

        elif command.lower() == "r":
            if previous_idx is not None:
                idx, previous_idx = previous_idx, idx
                register_jump(idx, jump_history)

        elif command == readchar.key.UP:
            next_err = get_next_mismatch(idx, error_indexs)
            if next_err is not None:
                previous_idx = idx
                idx = next_err
                register_jump(idx, jump_history)

        elif command == readchar.key.DOWN:
            prev_err = get_previous_mismatch(idx, error_indexs)
            if prev_err is not None:
                previous_idx = idx
                idx = prev_err
                register_jump(idx, jump_history)

        elif command.lower() == "h":
            new_idx, hist_previous = handle_history_mode(
                data,
                idx,
                mismatch_indexs,
                jump_history,
                max_cycle,
                show_deltas,
            )

            if hist_previous is not None and new_idx != idx:
                previous_idx = hist_previous
                idx = new_idx
                register_jump(idx, jump_history)
        elif command.lower() == "b":
            if idx != 0:
                previous_idx = idx
                idx = 0
                register_jump(idx, jump_history)

        elif command.lower() == "e":
            if idx != max_cycle:
                previous_idx = idx
                idx = max_cycle
                register_jump(idx, jump_history)

    try:
        with open("monitoring_signals.yaml", "r") as stream:
            yaml.safe_load(stream)
    except Exception:
        pass


if __name__ == "__main__":
    main()