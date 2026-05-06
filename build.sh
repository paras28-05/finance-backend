#!/bin/bash
# Render build script for finance-backend
# Installs dependencies and runs migrations if available

set -e

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check if Alembic is being used and run migrations
if grep -q "alembic" requirements.txt 2>/dev/null; then
    echo "🔄 Running Alembic migrations..."
    alembic upgrade head
fi

echo "✅ Build script completed successfully!"
