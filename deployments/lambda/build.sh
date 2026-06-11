#!/bin/bash
#
# Build script for AWS Lambda deployment package
#
# This script copies shared code from core/ and packages everything for Lambda
#

set -e

# colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

echo "=========================================="
echo "Building Lambda Deployment Package"
echo "=========================================="
echo ""

# get the path to core/ (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$(cd "$SCRIPT_DIR/../../core" && pwd)"

# verify core directory exists
if [ ! -d "$CORE_DIR" ]; then
    echo "This script must be run from deployments/lambda/"
    print_error "Core directory not found at: $CORE_DIR"
fi

print_success "Found core directory at: $CORE_DIR"

# check for existing builds and ask to clean
if [ -d "package" ] || [ -f "lambda-deployment.zip" ]; then
    echo ""
    print_warning "Found existing build artifacts:"
    [ -d "package" ] && echo "  - package/ directory"
    [ -f "lambda-deployment.zip" ] && echo "  - lambda-deployment.zip"
    echo ""
    read -p "Clean previous builds (this will delete the package/ directory and lambda-deployment.zip file) and continue? (y/n): " clean_builds
    
    if [[ $clean_builds =~ ^[Yy]$ ]]; then
        echo ""
        echo "Cleaning previous builds..."
        if rm -rf package 2>/dev/null && rm -f lambda-deployment.zip 2>/dev/null; then
            print_success "Previous builds cleaned"
        else
            print_error "Failed to clean previous builds"
        fi
    else
        echo "Build cancelled."
        exit 0
    fi
else
    print_success "No previous builds found"
fi

# create package directory
echo ""
echo "Creating package directory..."
if mkdir -p package; then
    print_success "Package directory created"
else
    print_error "Failed to create package directory"
fi

# copy shared code from core/
echo ""
echo "Copying shared strategies from core/..."
if [ ! -d "$CORE_DIR/strategies" ]; then
    print_error "Strategies directory not found at: $CORE_DIR/strategies"
fi
if cp -r "$CORE_DIR/strategies" package/strategies 2>/dev/null; then
    print_success "Strategies copied"
else
    print_error "Failed to copy strategies"
fi

echo "Copying shared clients from core/..."
if [ ! -d "$CORE_DIR/clients" ]; then
    print_error "Clients directory not found at: $CORE_DIR/clients"
fi
if cp -r "$CORE_DIR/clients" package/clients 2>/dev/null; then
    print_success "Clients copied"
else
    print_error "Failed to copy clients"
fi

echo "Copying shared engine from core/..."
if [ ! -f "$CORE_DIR/engine.py" ]; then
    print_error "Engine module not found at: $CORE_DIR/engine.py"
fi
if cp "$CORE_DIR/engine.py" package/engine.py 2>/dev/null; then
    print_success "Engine copied"
else
    print_error "Failed to copy engine"
fi

# copy lambda-specific utils
echo "Copying Lambda-specific utils..."
if [ ! -d "utils" ]; then
    print_error "Lambda utils directory not found"
fi
if cp -r utils package/utils 2>/dev/null; then
    print_success "Lambda utils copied"
else
    print_error "Failed to copy Lambda utils"
fi

# copy lambda function
echo "Copying Lambda handler..."
if [ ! -f "lambda_function.py" ]; then
    print_error "lambda_function.py not found"
fi
if cp lambda_function.py package/ 2>/dev/null; then
    print_success "Lambda handler copied"
else
    print_error "Failed to copy Lambda handler"
fi

# install dependencies
echo ""
echo "Installing dependencies..."
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
fi

if pip install -r requirements.txt -t package/ --upgrade --no-warn-conflicts --quiet 2>&1; then
    print_success "Dependencies installed"
else
    echo "Try running manually: pip install -r requirements.txt -t package/"
    print_error "Failed to install dependencies"
fi

# create deployment package
echo ""
echo "Creating deployment package..."
cd package || print_error "Failed to enter package directory"
if zip -r ../lambda-deployment.zip . -q 2>/dev/null; then
    cd ..
    print_success "Deployment package created"
else
    cd ..
    print_error "Failed to create deployment package"
fi

# get package size
if [ -f "lambda-deployment.zip" ]; then
    SIZE=$(du -h lambda-deployment.zip | cut -f1)
    print_success "Package size: $SIZE"
else
    print_error "lambda-deployment.zip not found"
fi

# print success message only if everything worked
echo ""
echo "=========================================="
print_success "Build Complete!"
echo "=========================================="
echo ""
echo "Deployment package: lambda-deployment.zip"
echo "Package size: $SIZE"
echo ""
echo "Package contents:"
echo "  ✓ Core strategies (from core/strategies/)"
echo "  ✓ Core clients (from core/clients/)"
echo "  ✓ Core engine (from core/engine.py)"
echo "  ✓ Lambda utilities"
echo "  ✓ Python dependencies (requests, boto3)"
echo ""
echo "Next steps:"
echo "1. Upload lambda-deployment.zip to AWS Lambda"
echo ""
echo "2. Configure environment variables:"
echo "   - ALPACA_API_KEY"
echo "   - ALPACA_SECRET_KEY"
echo "   - THECARDCADDIE_API_KEY (optional)"
echo ""
echo "3. Set up EventBridge or API Gateway trigger"
echo ""
echo "4. See deployments/lambda/README.md for detailed AWS setup"
echo ""