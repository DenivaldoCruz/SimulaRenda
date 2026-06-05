#!/usr/bin/env bash
set -euo pipefail

# setup_dev_env.sh
# Creates local .env files for development from .env.example and generates a SECRET_KEY.
# Usage: ./scripts/setup_dev_env.sh

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT_DIR/.env.example"
ROOT_ENV="$ROOT_DIR/.env"
BACKEND_ENV="$ROOT_DIR/backend/.env"

if [ ! -f "$EXAMPLE" ]; then
  echo ".env.example not found in project root ($EXAMPLE)" >&2
  exit 1
fi

echo "Creating $ROOT_ENV from $EXAMPLE (if not exists)"
cp -n "$EXAMPLE" "$ROOT_ENV"

echo "Creating $BACKEND_ENV from $EXAMPLE (if not exists)"
cp -n "$EXAMPLE" "$BACKEND_ENV"

# Generate a cryptographically secure 32-byte hex secret
SK=$(python3 - <<'PY'
import secrets
print(secrets.token_hex(32))
PY
)

echo "Setting SECRET_KEY in $ROOT_ENV and $BACKEND_ENV"
if grep -q '^SECRET_KEY=' "$ROOT_ENV"; then
  perl -0777 -pe "s/^SECRET_KEY=.*$/SECRET_KEY=$SK/m" -i "$ROOT_ENV"
else
  echo "SECRET_KEY=$SK" >> "$ROOT_ENV"
fi

if grep -q '^SECRET_KEY=' "$BACKEND_ENV"; then
  perl -0777 -pe "s/^SECRET_KEY=.*$/SECRET_KEY=$SK/m" -i "$BACKEND_ENV"
else
  echo "SECRET_KEY=$SK" >> "$BACKEND_ENV"
fi

echo "Done. Remember: do NOT commit these .env files to git. They are ignored by .gitignore."
echo "Generated SECRET_KEY: ${SK}"

exit 0

