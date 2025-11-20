#!/bin/bash
# Format all Python files using Black and isort

set -e

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🔧 Formatting code with Black..."
black .

echo "📦 Sorting imports with isort..."
isort .

echo "✅ Formatting complete!"
