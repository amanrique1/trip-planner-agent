"""
Generate a bcrypt hash for use in .env / config.

Usage:
    uv run scripts/hash_password.py
    uv run scripts/hash_password.py --password 'my_secret_password'
    uv run scripts/hash_password.py --verify 'my_secret_password' --hash '$2b$12$...'
"""
import argparse
import getpass
import sys

import bcrypt


def hash_password(plain: str, rounds: int = 12) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=rounds),
    ).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plain-text password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate / verify bcrypt hashes")
    parser.add_argument("--password", "-p", help="Password (omit for interactive prompt)")
    parser.add_argument("--verify", "-v", help="Plain password to verify")
    parser.add_argument("--hash", help="Existing hash to verify against")
    parser.add_argument("--rounds", "-r", type=int, default=12, help="Bcrypt cost factor (default: 12)")
    args = parser.parse_args()

    # ── Verify mode ──
    if args.verify:
        if not args.hash:
            print("ERROR: --hash is required with --verify", file=sys.stderr)
            sys.exit(1)
        ok = verify_password(args.verify, args.hash)
        print(f"Match: {ok}")
        sys.exit(0 if ok else 1)

    # ── Generate mode ──
    if args.password:
        plain = args.password
    else:
        plain = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if plain != confirm:
            print("ERROR: passwords do not match", file=sys.stderr)
            sys.exit(1)

    if not plain:
        print("ERROR: password cannot be empty", file=sys.stderr)
        sys.exit(1)

    if len(plain.encode("utf-8")) > 72:
        print("WARNING: bcrypt truncates passwords to 72 bytes", file=sys.stderr)

    hashed = hash_password(plain, rounds=args.rounds)

    print()
    print("# ── Add this to your .env ──")
    print(f'ADMIN_PASSWORD_HASH="{hashed}"')
    print()
    print("# ── Raw hash ──")
    print(hashed)
    print()

    # Self-test
    assert verify_password(plain, hashed), "Self-test failed!"
    print("✓ Self-test passed")


if __name__ == "__main__":
    main()