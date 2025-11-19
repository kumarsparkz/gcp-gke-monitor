#!/bin/bash

# GCP/GKE Monitor - macOS Quick Start Script
# This script automates the setup and launch of the monitoring dashboard

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}GCP/GKE Monitor - Quick Start Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to print colored messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Homebrew is installed
check_homebrew() {
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew is not installed."
        print_status "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add Homebrew to PATH for Apple Silicon Macs
        if [[ $(uname -m) == 'arm64' ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi

        print_success "Homebrew installed successfully"
    else
        print_success "Homebrew is already installed"
    fi
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed."
        print_status "Installing Node.js via Homebrew..."
        brew install node
        print_success "Node.js installed successfully"
    else
        NODE_VERSION=$(node --version)
        print_success "Node.js is already installed (version: $NODE_VERSION)"
    fi
}

# Check if Python 3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed."
        print_status "Installing Python 3 via Homebrew..."
        brew install python@3
        print_success "Python 3 installed successfully"
    else
        PYTHON_VERSION=$(python3 --version)
        print_success "Python 3 is already installed ($PYTHON_VERSION)"
    fi
}

# Check if gcloud CLI is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_warning "gcloud CLI is not installed."
        print_status "Installing gcloud CLI via Homebrew..."
        brew install --cask google-cloud-sdk

        # Source gcloud path
        if [ -f "/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc" ]; then
            source "/opt/homebrew/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc"
        elif [ -f "/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc" ]; then
            source "/usr/local/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/path.bash.inc"
        fi

        print_success "gcloud CLI installed successfully"
    else
        GCLOUD_VERSION=$(gcloud --version | head -n 1)
        print_success "gcloud CLI is already installed ($GCLOUD_VERSION)"
    fi
}

# Authenticate with GCP
authenticate_gcp() {
    print_status "Setting up GCP authentication..."
    print_status "This will open your browser for Google Cloud authentication"

    # Standard gcloud auth login
    print_status "Running: gcloud auth login"
    gcloud auth login

    # Application default credentials for API access
    print_status "Running: gcloud auth application-default login"
    gcloud auth application-default login

    print_success "GCP authentication completed"
}

# Setup backend
setup_backend() {
    print_status "Setting up backend..."

    cd backend

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi

    # Activate virtual environment and install dependencies
    print_status "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    deactivate
    print_success "Backend dependencies installed"

    cd ..
}

# Setup frontend
setup_frontend() {
    print_status "Setting up frontend..."

    cd frontend

    # Install npm dependencies
    print_status "Installing npm dependencies (this may take a few minutes)..."
    npm install
    print_success "Frontend dependencies installed"

    cd ..
}

# Start the application
start_application() {
    print_status "Starting the application..."

    # Create a temporary directory for log files
    LOG_DIR="$(pwd)/logs"
    mkdir -p "$LOG_DIR"

    BACKEND_LOG="$LOG_DIR/backend.log"
    FRONTEND_LOG="$LOG_DIR/frontend.log"

    # Start backend
    print_status "Starting backend on port 8000..."
    cd backend
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"
    deactivate
    cd ..
    print_success "Backend started (PID: $BACKEND_PID)"

    # Wait a bit for backend to start
    sleep 3

    # Start frontend
    print_status "Starting frontend on port 3000..."
    cd frontend
    nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    cd ..
    print_success "Frontend started (PID: $FRONTEND_PID)"

    # Wait for frontend to be ready
    print_status "Waiting for application to be ready..."
    sleep 8
}

# Open browser
open_browser() {
    print_status "Opening browser to http://localhost:3000..."
    sleep 2
    open http://localhost:3000
    print_success "Browser opened"
}

# Display final instructions
display_instructions() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}Your GCP/GKE Monitoring Dashboard is now running!${NC}"
    echo ""
    echo -e "Frontend: ${GREEN}http://localhost:3000${NC}"
    echo -e "Backend:  ${GREEN}http://localhost:8000${NC}"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo -e "  • Toggle 'Pull Metrics' to ON in the dashboard to start monitoring"
    echo -e "  • Logs are stored in: ${BLUE}logs/${NC}"
    echo -e "    - Backend log: ${BLUE}logs/backend.log${NC}"
    echo -e "    - Frontend log: ${BLUE}logs/frontend.log${NC}"
    echo ""
    echo -e "${YELLOW}To stop the application:${NC}"
    echo -e "  kill \$(cat logs/backend.pid) \$(cat logs/frontend.pid)"
    echo ""
    echo -e "${YELLOW}To view logs:${NC}"
    echo -e "  tail -f logs/backend.log    # Backend logs"
    echo -e "  tail -f logs/frontend.log   # Frontend logs"
    echo ""
}

# Main execution
main() {
    # Check and install dependencies
    print_status "Checking system dependencies..."
    check_homebrew
    check_node
    check_python
    check_gcloud

    echo ""
    print_status "All dependencies are installed!"
    echo ""

    # Authenticate with GCP
    authenticate_gcp

    echo ""

    # Setup backend and frontend
    setup_backend
    setup_frontend

    echo ""

    # Start the application
    start_application

    # Open browser
    open_browser

    # Display final instructions
    display_instructions
}

# Run main function
main
