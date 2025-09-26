#!/bin/bash
# LaTeX Package Installation Script for AI Scientist
# Run this script to install essential packages for scientific paper generation

echo "🚀 Installing essential LaTeX packages for AI Scientist..."

# Check if tlmgr is available
if ! command -v tlmgr &> /dev/null; then
    echo "❌ tlmgr not found. Please install TinyTeX first:"
    echo "   R: tinytex::install_tinytex()"
    echo "   Or visit: https://yihui.org/tinytex/"
    exit 1
fi

# Essential packages for scientific papers
PACKAGES=(
    "siunitx" "multirow" "algorithm2e" "algorithms"
    "amsmath" "amsfonts" "amssymb" "amsthm" "mathtools"
    "graphicx" "subfigure" "booktabs" "array"
    "hyperref" "url" "natbib" "cite"
    "xcolor" "tikz" "pgfplots" "listings"
    "geometry" "fancyhdr" "setspace" "enumitem"
    "caption" "float" "placeins"
)

success_count=0
total_count=${#PACKAGES[@]}

for package in "${PACKAGES[@]}"; do
    echo "📦 Installing $package..."
    if tlmgr install "$package" 2>/dev/null; then
        echo "✅ $package installed successfully"
        ((success_count++))
    else
        echo "⚠️  $package installation failed (may already be installed)"
    fi
done

echo "🎉 Installation complete: $success_count/$total_count packages processed"
echo "✅ LaTeX environment ready for AI Scientist!"
