"""Run data profiling against raw synthetic datasets."""

from __future__ import annotations

from src.profiling.profiler import profile_all
from src.validation.run_checks import load_datasets


def main() -> None:
    datasets = load_datasets(stage="raw")
    profile = profile_all(
        {
            "patients": datasets["patients"],
            "providers": datasets["providers"],
            "facilities": datasets["facilities"],
            "encounters": datasets["encounters"],
        }
    )
    print(profile.to_string(index=False))


if __name__ == "__main__":
    main()
