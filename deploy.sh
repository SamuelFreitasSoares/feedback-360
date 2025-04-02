#!/bin/bash

# Exit on error
set -e

echo "Activating virtual environment..."
source /path/to/your/venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate

echo "Restarting Gunicorn..."
sudo systemctl restart feedback360

echo "Deployment completed successfully!"
