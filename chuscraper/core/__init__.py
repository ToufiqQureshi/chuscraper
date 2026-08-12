"""chuscraper.core — browser, tab and element primitives."""

from typing import Any

# Logger/FailureDumper are deprecated (removed in 0.22). Expose them lazily so
# that merely importing chuscraper.core does not emit the warning.
_DEPRECATED = {"Logger", "FailureDumper"}

__all__ = sorted(_DEPRECATED)


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED:
        import warnings

        warnings.warn(
            f"chuscraper.core.{name} is deprecated and will be removed in "
            "chuscraper 0.22. Use the standard library `logging` module and "
            "handle failure artefacts in your own error path.",
            DeprecationWarning,
            stacklevel=2,
        )
        from . import observability

        return getattr(observability, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
