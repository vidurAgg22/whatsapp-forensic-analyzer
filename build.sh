#!/bin/bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Downloading NLTK vader_lexicon..."
python -c "
import nltk
import os
from pathlib import Path

# Download to project-local folder so it survives deployment
nltk_path = Path('nltk_data')
nltk_path.mkdir(exist_ok=True)
nltk.download('vader_lexicon', download_dir=str(nltk_path), quiet=False)
print('NLTK vader_lexicon downloaded successfully.')
"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput

echo "Build complete."