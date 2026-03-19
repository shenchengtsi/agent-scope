#!/bin/bash
# AgentScope 一键安装脚本
# Usage: ./install.sh [nanobot|backend|all]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python version: $PYTHON_VERSION"
}

# Install SDK
install_sdk() {
    print_info "Installing AgentScope SDK..."
    
    cd "$SCRIPT_DIR/sdk"
    
    if [ -f "setup.py" ]; then
        pip3 install -e . --quiet
        print_success "SDK installed"
    else
        print_error "setup.py not found in $SCRIPT_DIR/sdk"
        exit 1
    fi
}

# Install backend dependencies
install_backend() {
    print_info "Installing backend dependencies..."
    
    cd "$SCRIPT_DIR/backend"
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt --quiet
        print_success "Backend dependencies installed"
    else
        print_warning "requirements.txt not found, skipping backend deps"
    fi
}

# Install frontend dependencies
install_frontend() {
    print_info "Installing frontend dependencies..."
    
    if ! command -v npm &> /dev/null; then
        print_warning "npm not found, skipping frontend installation"
        return
    fi
    
    cd "$SCRIPT_DIR/frontend"
    
    if [ -f "package.json" ]; then
        npm install --silent
        print_success "Frontend dependencies installed"
    else
        print_warning "package.json not found, skipping frontend deps"
    fi
}

# Setup nanobot integration
setup_nanobot() {
    print_info "Setting up nanobot integration..."
    
    if ! command -v agentscope &> /dev/null; then
        print_error "agentscope CLI not found. Please install SDK first."
        return
    fi
    
    # Check for common nanobot locations
    NANOBOT_DIRS=(
        "$HOME/.nanobot"
        "$HOME/.nanobot-zhangjuzheng"
        "$HOME/.nanobot-lvfang"
        "$HOME/nanobot"
    )
    
    FOUND=0
    for dir in "${NANOBOT_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            print_info "Found nanobot workspace: $dir"
            read -p "Setup AgentScope for this workspace? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                agentscope setup nanobot --workspace "$dir"
                FOUND=$((FOUND + 1))
            fi
        fi
    done
    
    if [ $FOUND -eq 0 ]; then
        print_warning "No nanobot workspaces found in common locations"
        print_info "You can manually setup later with: agentscope setup nanobot --workspace /path/to/nanobot"
    fi
}

# Create startup scripts
create_scripts() {
    print_info "Creating startup scripts..."
    
    # Start backend script
    cat > "$SCRIPT_DIR/start-backend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/backend"
python3 main.py
EOF
    chmod +x "$SCRIPT_DIR/start-backend.sh"
    
    # Start frontend script
    cat > "$SCRIPT_DIR/start-frontend.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/frontend"
npm start
EOF
    chmod +x "$SCRIPT_DIR/start-frontend.sh"
    
    # Start all script
    cat > "$SCRIPT_DIR/start-all.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting AgentScope Backend..."
cd "$SCRIPT_DIR/backend"
python3 main.py &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 3

echo "Starting AgentScope Frontend..."
cd "$SCRIPT_DIR/frontend"
npm start &
FRONTEND_PID=$!

echo ""
echo "AgentScope is starting..."
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

wait
EOF
    chmod +x "$SCRIPT_DIR/start-all.sh"
    
    print_success "Startup scripts created"
}

# Print final instructions
print_instructions() {
    echo ""
    echo "=========================================="
    print_success "AgentScope installation complete!"
    echo "=========================================="
    echo ""
    echo "Quick Start:"
    echo "  1. Start backend:  ./start-backend.sh"
    echo "  2. Start frontend: ./start-frontend.sh"
    echo "  3. Or start both:  ./start-all.sh"
    echo ""
    echo "Access:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend:  http://localhost:8000"
    echo ""
    echo "CLI Commands:"
    echo "  agentscope status              # Check status"
    echo "  agentscope setup nanobot -w ~/.nanobot  # Setup nanobot"
    echo ""
    echo "Documentation:"
    echo "  - Install guide: ./INSTALL.md"
    echo "  - README:        ./README.md"
    echo ""
}

# Main installation
main() {
    echo "=========================================="
    echo "  AgentScope Installation"
    echo "=========================================="
    echo ""
    
    check_python
    
    # Parse arguments
    MODE=${1:-all}
    
    case $MODE in
        sdk)
            install_sdk
            ;;
        backend)
            install_backend
            ;;
        frontend)
            install_frontend
            ;;
        nanobot)
            setup_nanobot
            ;;
        all)
            install_sdk
            install_backend
            install_frontend
            setup_nanobot
            create_scripts
            print_instructions
            ;;
        *)
            echo "Usage: $0 [sdk|backend|frontend|nanobot|all]"
            exit 1
            ;;
    esac
    
    print_success "Done!"
}

main "$@"
