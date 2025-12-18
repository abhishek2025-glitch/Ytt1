#!/bin/bash

echo "================================"
echo "VIRALOS PRIME v2.0 Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "ERROR: Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check FFmpeg
echo ""
echo "Checking for FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✓ FFmpeg found"
    ffmpeg -version | head -1
else
    echo "✗ FFmpeg not found"
    echo ""
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/"
fi

# Check ImageMagick
echo ""
echo "Checking for ImageMagick..."
if command -v convert &> /dev/null; then
    echo "✓ ImageMagick found"
else
    echo "✗ ImageMagick not found (optional)"
    echo "  Install: sudo apt-get install imagemagick"
fi

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/cache data/assets data/queue data/metrics data/logs
mkdir -p memory/learned_rules
touch data/cache/.gitkeep data/assets/.gitkeep data/queue/.gitkeep data/metrics/.gitkeep data/logs/.gitkeep

# Copy environment template
echo ""
echo "Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from template"
    echo ""
    echo "IMPORTANT: Edit .env file and add your API keys:"
    echo "  - OPENROUTER_API_KEY (optional, has fallback)"
    echo "  - YOUTUBE_CLIENT_ID"
    echo "  - YOUTUBE_CLIENT_SECRET"
    echo "  - YOUTUBE_REFRESH_TOKEN"
else
    echo "✓ .env file already exists"
fi

# Run tests
echo ""
echo "Running tests..."
pytest --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All tests passed"
else
    echo ""
    echo "✗ Some tests failed (this is OK for initial setup)"
fi

# Summary
echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Test locally: cd src && python main.py daily"
echo "3. Set up GitHub secrets for automated runs"
echo ""
echo "Documentation:"
echo "  - README.md - Quick start guide"
echo "  - docs/ARCHITECTURE.md - System design"
echo "  - docs/CONFIG_REFERENCE.md - Configuration options"
echo "  - docs/TROUBLESHOOTING.md - Common issues"
echo "  - docs/RUNBOOK.md - Operations guide"
echo ""
echo "Mobile triggering:"
echo "  - GitHub UI: https://github.com/Ytt1/8n7t2vh7/actions"
echo "  - GitHub Mobile app: Actions → Manual Trigger"
echo ""
