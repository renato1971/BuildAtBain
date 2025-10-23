#!/bin/bash

# Color codes for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AIS Masterclass Newsletter Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print step with formatting
print_step() {
    echo -e "${GREEN}➜${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Create output directories if they don't exist
print_step "Creating required directories..."
if mkdir -p output logs data 2>/dev/null; then
    print_success "Directories created: output/, logs/, data/"
else
    print_error "Failed to create directories"
    exit 1
fi

# Set proper permissions (777 for development)
print_step "Setting directory permissions (777 for development)..."
if chmod -R 777 output logs data 2>/dev/null; then
    print_success "Permissions set successfully"
else
    print_warning "Could not set all permissions (might need sudo)"
fi

echo ""
print_step "Stopping existing containers..."
if docker compose down 2>&1; then
    print_success "Containers stopped"
else
    print_error "Failed to stop containers"
    exit 1
fi

echo ""
print_step "Removing old containers..."
if docker compose rm -f 2>&1; then
    print_success "Old containers removed"
else
    print_warning "No old containers to remove"
fi

echo ""
print_step "Removing old images..."
docker rmi ais-masterclass-newsletter-api 2>/dev/null && print_success "Removed API image" || print_warning "No API image to remove"
docker rmi ais-masterclass-newsletter-newsletter_app 2>/dev/null && print_success "Removed newsletter_app image" || print_warning "No newsletter_app image to remove"
docker rmi ais-masterclass-newsletter-frontend 2>/dev/null && print_success "Removed frontend image" || print_warning "No frontend image to remove"

echo ""
echo -e "${BLUE}========================================${NC}"
print_step "Building containers (this may take a few minutes)..."
echo -e "${BLUE}========================================${NC}"
if docker compose build --no-cache 2>&1; then
    echo ""
    print_success "All containers built successfully"
else
    echo ""
    print_error "Build failed! Check the error messages above"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
print_step "Starting containers..."
echo -e "${BLUE}========================================${NC}"
if docker compose up -d 2>&1; then
    echo ""
    print_success "All containers started successfully"
else
    echo ""
    print_error "Failed to start containers"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Services available at:"
echo "  • API:      http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Frontend: http://localhost:5173"
echo "  • PgAdmin:  http://localhost:5050 (admin@bain.com / admin)"
echo "  • Weaviate: http://localhost:8080"
echo ""
print_step "Showing container status..."
docker compose ps
echo ""
print_step "Following logs (Ctrl+C to exit)..."
echo ""
docker compose logs -f
