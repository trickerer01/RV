from .main import main_async, main_sync


def main(argv=None):
    exit(main_sync(argv))


__all__ = (
    'main',
    'main_async',
    'main_sync',
)
