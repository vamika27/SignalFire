"""SEC pipeline entrypoint for module execution.

This module preserves the documented command:

    python3 -m signalfire.src.sec_pipeline --max-filings 2
"""

from signalfire.src.pipeline import main, run_pipeline


__all__ = ["main", "run_pipeline"]


if __name__ == "__main__":
    main()
