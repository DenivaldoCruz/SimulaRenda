DEV setup
=============

This project includes a small helper script to create local development `.env` files and generate a secure `SECRET_KEY`:

- Script: `./scripts/setup_dev_env.sh`

Quick start
-----------

1. Run the script (idempotent):

```bash
./scripts/setup_dev_env.sh
```

This copies `.env.example` to `./.env` and `./backend/.env` if they don't exist, and writes a cryptographically secure 32-byte hex `SECRET_KEY` into both files.

2. Start the dev server:

```bash
make dev
```

Notes and best practices
------------------------

- `.env` and `backend/.env` are deliberately ignored by `.gitignore` to avoid committing secrets. The script is committed (it contains no secrets) so other developers can reproduce the same steps.
- `NICEGUI_STORAGE_SECRET` defaults to `SECRET_KEY` at application startup if left blank.
- For production, do NOT use `.env` files in the repository. Provide environment variables through your deployment system or a dedicated secrets manager (Vault, AWS Secrets Manager, etc.).
- If you suspect a secret was exposed (committed or pushed), rotate it immediately and consider purging it from Git history.

Security checklist for new contributors
-------------------------------------

1. Run `./scripts/setup_dev_env.sh` once after cloning.
2. Verify `git status` shows no `.env` files staged.
3. Never paste secrets into public issues or chats.

Questions or changes
--------------------
If you want a different setup (e.g., single-source `.env` only at repo root, or usage of direnv) open a small PR or request changes in the README.

