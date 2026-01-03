#!/bin/bash
# Fitness Tracker AI - Quick Setup Script
# Run this to quickly set up the project

echo "🏋️ Fitness Tracker AI - Setup Script"
echo "======================================"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your GEMINI_API_KEY"
    echo "   Get your API key at: https://ai.google.dev/"
    echo ""
fi

# Create data directory
echo "📂 Creating data directory for storage..."
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "📖 Next steps:"
echo "   1. Edit .env and add your GEMINI_API_KEY"
echo "   2. Run: python main.py"
echo "   3. Open: http://localhost:8000"
echo ""
echo "Happy training! 💪"
