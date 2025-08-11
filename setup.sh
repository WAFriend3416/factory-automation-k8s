#!/bin/bash

# Setup script for Smart Factory Alpha Prototype

echo "🚀 Smart Factory Alpha Prototype Setup"
echo "======================================"

# 1. Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# 2. Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 3. Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Open Terminal 1 and run: source venv/bin/activate && python aas_mock_server/server.py"
echo "2. Open Terminal 2 and run: source venv/bin/activate && uvicorn api.main:app --reload"
echo "3. Open Terminal 3 and test with: ./test_goal1.sh"