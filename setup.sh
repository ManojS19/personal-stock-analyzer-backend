#!/bin/bash

echo "Setting up Stock Analyzer Backend..."

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Create models directory
mkdir -p models

echo "Setup complete!"
echo "To start the server, run: python main.py"
