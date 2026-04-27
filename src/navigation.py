MAX_HISTORY = 10


def register_jump(target_cycle: int, jump_history: list[int], max_size: int = MAX_HISTORY) -> None:
    if target_cycle in jump_history:
        jump_history.remove(target_cycle)

    jump_history.insert(0, target_cycle)

    if len(jump_history) > max_size:
        jump_history.pop()


def get_next_mismatch(current_idx: int, error_indexs: list[int]):
    next_errs = [m for m in error_indexs if m > current_idx]
    return min(next_errs) if next_errs else None


def get_previous_mismatch(current_idx: int, error_indexs: list[int]):
    prev_errs = [m for m in error_indexs if m < current_idx]
    return max(prev_errs) if prev_errs else None