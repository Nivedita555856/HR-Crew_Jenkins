#!/usr/bin/env bash
# Pull the latest code from GitHub and restart. Run on EC2 (GitHub Actions also runs this).
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd "$HOME/PROITBRIDGE-HR-CREW"
git fetch origin main
git reset --hard origin/main
uv sync --frozen --no-dev
sudo cp deploy/hr-crew.service /etc/systemd/system/hr-crew.service
sudo systemctl daemon-reload
sudo systemctl restart hr-crew
sleep 5
curl -fsS http://127.0.0.1:8000/health && echo " ✅ deployed $(git rev-parse --short HEAD)"
