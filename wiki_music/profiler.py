"""Profiling module of wiki_music."""
from contextlib import contextmanager

__all__ = ["finish_yappi", "ContextProfiler", "init_yappi"]


def finish_yappi():
    """Stop profiler, collect stats and write them to disc."""
    import yappi
    from pathlib import Path

    # define directory for stats save and ensure it exists
    OUT_FILE = Path("./../profile_data/wiki_music")
    OUT_FILE.parent.mkdir(exist_ok=True, parents=True)

    # stop yappi profiler
    print('[YAPPI STOP]')
    yappi.stop()

    # get yappi function stats
    print('[YAPPI WRITE]')
    stats = yappi.get_func_stats()

    # write different formats of functions statistics
    for stat_type in ['pstat', 'callgrind', 'ystat']:
        path = OUT_FILE.with_suffix(f".{stat_type}")
        print(f'writing {path}')
        stats.save(path, type=stat_type)

    # write summary function statistics
    path = OUT_FILE.with_suffix(".func_stats")

    print('\n[YAPPI FUNC_STATS]')
    print(f"writing {path}")

    with path.open("w") as fh:
        stats.print_all(out=fh)

    # write thread based statistics
    path = OUT_FILE.with_suffix(".thread_stats")

    print('\n[YAPPI THREAD_STATS]')
    print(f"writing {path}")

    with path.open("w") as fh:
        yappi.get_thread_stats().print_all(out=fh)

    print('[YAPPI OUT]')


@contextmanager
def ContextProfiler():
    """Context profiler using yappi."""
    import yappi

    print('[YAPPI START]')
    yappi.set_clock_type('wall')
    yappi.start()

    try:
        yield None
    finally:
        finish_yappi()


def init_yappi(write_at_exit: bool = True):
    """Initialize yappi profiler and register atexit handler.

    Stats are written automatically on application exit.
    """
    import yappi
    import atexit

    print('[YAPPI START]')
    yappi.set_clock_type("cpu")  # 'wall')
    yappi.start()

    if write_at_exit:
        atexit.register(finish_yappi)
