
from .decorators import licensed

__all__ = ["licensed", "LicenseClient", "init_flask"]


def __getattr__(name):
    if name in {"LicenseClient", "init_flask"}:
        from .licensing_client import LicenseClient, init_flask

        return {
            "LicenseClient": LicenseClient,
            "init_flask": init_flask,
        }[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
