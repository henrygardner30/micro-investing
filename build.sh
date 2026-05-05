#!/bin/bash
# Micro-Investing Engine - Main Build Script
# Guides users through setup for either local or Lambda deployment

set -e

# colors for better ux
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' 

print_header() {
    echo ""
    echo "=========================================="
    echo "  MICRO-INVESTING ENGINE"
    echo "  Build & Setup Script"
    echo "=========================================="
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "-------------------------------------------"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Please install Python 3.8 or higher"
        print_error "Python 3 is not installed"
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    print_success "Python ${PYTHON_VERSION} detected"
}

show_deployment_menu() {
    print_section "Select Deployment Type"
    echo ""
    echo "  1) Local Deployment (Recommended for Getting Started)"
    echo "     - Run on your computer"
    echo "     - Full control and customization"
    echo "     - Manual execution or cron automation"
    echo "     - Easy testing and debugging"
    echo ""
    echo "  2) AWS Lambda Deployment"
    echo "     - Serverless deployment on AWS"
    echo "     - Lightweight and nearly free"
    echo "     - Automatic scheduled execution"
    echo "     - Requires AWS account"
    echo "     - Production-ready scaling"
    echo ""
    echo "  3) Exit"
    echo ""
}

run_local_setup() {
    print_section "Starting Local Deployment Setup"
    
    cd deployments/local
    
    # ask if user wants to use virtual environment
    echo ""
    echo "A Python virtual environment keeps dependencies isolated from your system."
    echo "This is recommended to avoid conflicts with other Python projects."
    echo ""
    read -p "Do you want to use a virtual environment? (y/n): " use_venv
    
    if [[ $use_venv =~ ^[Yy]$ ]]; then
        # check if venv exists
        if [ ! -d "venv" ]; then
            echo ""
            print_warning "No virtual environment found at: $(pwd)/venv"
            echo ""
            read -p "Create virtual environment in this location? (y/n): " create_venv
            
        if [[ $create_venv =~ ^[Yy]$ ]]; then
            echo ""
            echo "Creating virtual environment..."
            if python3 -m venv venv 2>/dev/null; then
                print_success "Virtual environment created at: $(pwd)/venv"
                VENV_CREATED=true
            else
                print_error "Failed to create virtual environment"
            fi
            else
                echo ""
                print_warning "Virtual environment creation cancelled"
                echo "You'll need to manage dependencies yourself."
                echo ""
            read -p "Continue without virtual environment? (y/n): " continue_no_venv
            if [[ ! $continue_no_venv =~ ^[Yy]$ ]]; then
                echo ""
                echo "Setup cancelled."
                exit 0
            fi
            VENV_CREATED=false
            fi
        else
            print_success "Found existing virtual environment at: $(pwd)/venv"
            VENV_CREATED=false
        fi
        
        # ask to activate venv if it exists
        if [ -d "venv" ]; then
            echo ""
            if [ "$VENV_CREATED" = true ]; then
                read -p "Activate the newly created virtual environment? (y/n): " activate_venv
            else
                read -p "Activate existing virtual environment? (y/n): " activate_venv
            fi
            
        if [[ $activate_venv =~ ^[Yy]$ ]]; then
            if source venv/bin/activate 2>/dev/null; then
                print_success "Virtual environment activated"
            else
                print_error "Failed to activate virtual environment"
            fi
            else
                print_warning "Virtual environment not activated"
                echo "To activate it later, run:"
                echo "  source venv/bin/activate"
            fi
        fi
    else
        echo ""
        print_warning "Skipping virtual environment setup"
        echo "Dependencies will be installed to your system Python."
        echo ""
        read -p "Continue without virtual environment? (y/n): " continue_no_venv
        if [[ ! $continue_no_venv =~ ^[Yy]$ ]]; then
            echo ""
            echo "Setup cancelled."
            exit 0
        fi
    fi
    
    # show dependencies and confirm installation
    print_section "Dependencies Required"
    echo ""
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
    fi
    
    echo "The following packages will be installed:"
    cat requirements.txt | grep -v "^#" | grep -v "^$"
    echo ""
    read -p "Install dependencies? (y/n): " install_deps
    
    if [[ $install_deps =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing dependencies..."
        if pip install --upgrade pip -q 2>/dev/null && pip install -r requirements.txt 2>&1; then
            print_success "Dependencies installed"
        else
            echo "Try running manually: pip install -r requirements.txt"
            print_error "Failed to install dependencies"
        fi
    else
        print_warning "Skipping dependency installation"
        echo "You'll need to install dependencies manually with:"
        echo "  pip install -r requirements.txt"
        echo ""
        read -p "Continue to setup anyway? (y/n): " continue_anyway
        if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
            echo ""
            echo "Setup cancelled."
            exit 0
        fi
    fi
    
    # setup transaction template
    echo ""
    print_section "Transaction Data Setup"
    echo ""
    TEMPLATE_FILE="data/transactions/transactions_template.csv"
    DATA_FILE="data/transactions/transactions.csv"
    
    if [ -f "$TEMPLATE_FILE" ]; then
        if [ -f "$DATA_FILE" ]; then
            print_success "Found existing transactions.csv"
        else
            echo "Creating transactions.csv from template..."
            if cp "$TEMPLATE_FILE" "$DATA_FILE" 2>/dev/null; then
                print_success "Copied transactions_template.csv → transactions.csv"
                echo ""
                echo "You can now edit data/transactions/transactions.csv with your own data."
            else
                print_warning "Could not copy template file"
                echo "You can manually copy it later:"
                echo "  cp $TEMPLATE_FILE $DATA_FILE"
            fi
        fi
    else
        print_warning "Template file not found at: $TEMPLATE_FILE"
    fi
    
    # run setup
    echo ""
    read -p "Run interactive setup wizard? (y/n): " run_setup
    
    if [[ $run_setup =~ ^[Yy]$ ]]; then
        print_section "Running Interactive Setup"
        echo ""
        if [ ! -f "setup.py" ]; then
            print_error "setup.py not found"
        fi
        
        if python setup.py; then
            echo ""
            print_success "Setup completed successfully"
        else
            echo ""
            print_error "Setup failed"
        fi
    else
        echo ""
        print_success "Setup wizard skipped"
        echo ""
        echo "To run setup later:"
        echo "  cd deployments/local"
        echo "  python setup.py"
    fi
}

run_lambda_build() {
    print_section "Starting AWS Lambda Build"
    
    cd deployments/lambda
    
    # check if build.sh exists and is executable
    if [ ! -f "build.sh" ]; then
        print_error "build.sh not found in deployments/lambda"
    fi
    
    if [ ! -x "build.sh" ]; then
        if chmod +x build.sh 2>/dev/null; then
            print_success "Made build.sh executable"
        else
            print_error "Failed to make build.sh executable"
        fi
    fi
    
    echo ""
    echo "The Lambda build script will:"
    echo "  1. Create a package/ directory"
    echo "  2. Install Python dependencies to package/"
    echo "  3. Create a deployment package (lambda.zip)"
    echo "  4. Provide instructions for AWS deployment"
    echo ""
    read -p "Proceed with Lambda build? (y/n): " proceed_build
    
    if [[ $proceed_build =~ ^[Yy]$ ]]; then
        print_section "Running Lambda Build Script"
        echo ""
        if ./build.sh; then
            echo ""
            print_success "Lambda build completed successfully"
            echo ""
            echo "Note: Lambda strategies are configured via AWS environment variables"
            echo "      See deployments/lambda/README.md for STRATEGY_CONFIG examples"
        else
            echo ""
            print_error "Lambda build failed"
        fi
    else
        echo ""
        print_warning "Build cancelled"
        echo ""
        echo "To run the build manually:"
        echo "  cd deployments/lambda"
        echo "  ./build.sh"
    fi
}

main() {
    print_header
    
    # check Python
    check_python
    
    # show menu and get choice
    while true; do
        show_deployment_menu
        read -p "Enter your choice (1-3): " choice
        
        case $choice in
            1)
                echo ""
                print_success "Local Deployment Selected"
                run_local_setup
                break
                ;;
            2)
                echo ""
                print_success "AWS Lambda Deployment Selected"
                run_lambda_build
                break
                ;;
            3)
                echo ""
                echo "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid choice. Please enter 1, 2, or 3."
                sleep 1
                ;;
        esac
    done
    
    # print success message only if everything worked
    echo ""
    echo "=========================================="
    print_success "Build Complete!"
    echo "=========================================="
    echo ""
}

main