#!/usr/bin/env bash
# ONE-TIME setup on a fresh Ubuntu 24.04 EC2 instance.
# Usage (on the EC2 box):
#   git clone https://github.com/<you>/<repo>.git ~/PROITBRIDGE-HR-CREW
#   cd ~/PROITBRIDGE-HR-CREW && bash deploy/setup_ec2.sh
set -euo pipefail
APP_DIR="$HOME/PROITBRIDGE-HR-CREW"
cd "$APP_DIR"

echo "==> 1/6 System packages (git, nginx)"
sudo apt-get update -y
sudo apt-get install -y git nginx curl

echo "==> 2/6 Install uv"
if ! command -v uv >/dev/null 2>&1 && [ ! -x "$HOME/.local/bin/uv" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

echo "==> 3/6 Python 3.12 + libraries from uv.lock"
uv python install 3.12
uv sync --frozen --no-dev

echo "==> 4/6 .env and database folder"
sudo mkdir -p /var/lib/hr-crew && sudo chown "$USER":"$USER" /var/lib/hr-crew
if [ ! -f .env ]; then
  cp .env.example .env
  sed -i 's|^DB_FILE=.*|DB_FILE=/var/lib/hr-crew/hr_app.db|' .env
  chmod 600 .env
  echo "!! Edit $APP_DIR/.env and paste your OPENAI_API_KEY, then re-run this script."
  exit 1
fi

echo "==> 5/6 systemd service"
sudo cp deploy/hr-crew.service /etc/systemd/system/hr-crew.service
sudo systemctl daemon-reload
sudo systemctl enable --now hr-crew
sudo systemctl restart hr-crew

echo "==> 6/6 Nginx"
sudo cp deploy/nginx-hr-crew.conf /etc/nginx/sites-available/hr-crew
sudo ln -sf /etc/nginx/sites-available/hr-crew /etc/nginx/sites-enabled/hr-crew
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

sleep 3
curl -fsS http://127.0.0.1/health && echo
echo "✅ Done. Open http://<EC2-public-IP>/ in your browser."
