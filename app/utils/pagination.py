from typing import Tuple

MAX_PAGE_SIZE = 100


def page_range(page: int, page_size: int) -> Tuple[int, int]:
    """Translate a 1-based page number into an inclusive Supabase `.range()`.

    Always clamps inputs so a client cannot request unbounded rows.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    start = (page - 1) * page_size
    end = start + page_size - 1
    return start, end
