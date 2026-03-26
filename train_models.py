from __future__ import annotations

import argparse

from dogmatch.pipeline import train_and_save_models


def main() -> None:
    parser = argparse.ArgumentParser(description="Train AVDS Dog Matching + Risk models")
    parser.add_argument("--out-dir", default="artifacts", help="Directory to write model artifacts")
    parser.add_argument("--n-users", type=int, default=2000)
    parser.add_argument("--n-dogs", type=int, default=300)
    parser.add_argument("--pairs-per-user", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-feedback", action="store_true", help="Disable inclusion of feedback_log.csv")
    args = parser.parse_args()

    meta = train_and_save_models(
        out_dir=args.out_dir,
        n_users=args.n_users,
        n_dogs=args.n_dogs,
        pairs_per_user=args.pairs_per_user,
        seed=args.seed,
        include_feedback=not args.no_feedback,
    )

    print("Training complete.")
    print(meta.get("metrics"))


if __name__ == "__main__":
    main()

