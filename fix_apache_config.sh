#!/usr/bin/env bash
set -euo pipefail

# ==============================
# Fix Apache Configuration Script
# ==============================
# Fixes the incorrect path to httpd-vhosts.conf in Apache configuration
# ==============================

APACHE_CONF="/Applications/MAMP/conf/apache/httpd.conf"
VHOST_CONF="/Applications/MAMP/conf/apache/extra/httpd-vhosts.conf"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing Apache Configuration...${NC}"
echo ""

# Check if Apache config exists
if [ ! -f "$APACHE_CONF" ]; then
    echo -e "${RED}❌ Apache config not found: $APACHE_CONF${NC}"
    exit 1
fi

# Check if vhost config exists
if [ ! -f "$VHOST_CONF" ]; then
    echo -e "${RED}❌ Virtual host config not found: $VHOST_CONF${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Current configuration:${NC}"
echo "  Apache Config: $APACHE_CONF"
echo "  VHost Config: $VHOST_CONF"
echo ""

# Check current include statement
echo -e "${BLUE}🔍 Checking current include statement...${NC}"

# Check for commented out absolute path (disabled)
if grep -q "#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" "$APACHE_CONF"; then
    echo -e "${YELLOW}⚠️ Found commented out virtual host configuration${NC}"
    echo -e "${CYAN}Found: #Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf${NC}"
    
    # Create backup
    echo -e "${BLUE}💾 Creating backup...${NC}"
    sudo cp "$APACHE_CONF" "$APACHE_CONF.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Enable the configuration
    echo -e "${BLUE}🔧 Enabling virtual host configuration...${NC}"
    sudo sed -i '' 's|#Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf|Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf|' "$APACHE_CONF"
    
    echo -e "${GREEN}✅ Virtual host configuration enabled${NC}"
    
# Check for commented out relative path (disabled)
elif grep -q "#Include conf/extra/httpd-vhosts.conf" "$APACHE_CONF"; then
    echo -e "${YELLOW}⚠️ Found commented out virtual host configuration with relative path${NC}"
    echo -e "${CYAN}Found: #Include conf/extra/httpd-vhosts.conf${NC}"
    
    # Create backup
    echo -e "${BLUE}💾 Creating backup...${NC}"
    sudo cp "$APACHE_CONF" "$APACHE_CONF.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Enable and fix the path
    echo -e "${BLUE}🔧 Enabling and fixing virtual host configuration...${NC}"
    sudo sed -i '' 's|#Include conf/extra/httpd-vhosts.conf|Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf|' "$APACHE_CONF"
    
    echo -e "${GREEN}✅ Virtual host configuration enabled with correct path${NC}"
    
# Check for incorrect relative path (enabled but wrong)
elif grep -q "Include conf/extra/httpd-vhosts.conf" "$APACHE_CONF"; then
    echo -e "${YELLOW}⚠️ Found incorrect relative path: Include conf/extra/httpd-vhosts.conf${NC}"
    
    # Create backup
    echo -e "${BLUE}💾 Creating backup...${NC}"
    sudo cp "$APACHE_CONF" "$APACHE_CONF.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Fix the path
    echo -e "${BLUE}🔧 Fixing include path...${NC}"
    sudo sed -i '' 's|Include conf/extra/httpd-vhosts.conf|Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf|' "$APACHE_CONF"
    
    echo -e "${GREEN}✅ Fixed include path to absolute path${NC}"
    
# Check for correct absolute path (enabled and correct)
elif grep -q "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" "$APACHE_CONF"; then
    echo -e "${GREEN}✅ Virtual host configuration is already enabled and correct${NC}"
    
# No include statement found
else
    echo -e "${YELLOW}⚠️ No include statement found for httpd-vhosts.conf${NC}"
    echo -e "${BLUE}💡 Adding include statement...${NC}"
    
    # Create backup
    echo -e "${BLUE}💾 Creating backup...${NC}"
    sudo cp "$APACHE_CONF" "$APACHE_CONF.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Add include statement
    echo "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" | sudo tee -a "$APACHE_CONF"
    echo -e "${GREEN}✅ Added include statement${NC}"
fi

# Verify the final configuration
echo -e "${BLUE}🔍 Verifying final configuration...${NC}"
if grep -q "Include /Applications/MAMP/conf/apache/extra/httpd-vhosts.conf" "$APACHE_CONF"; then
    echo -e "${GREEN}✅ Virtual host configuration is now correct${NC}"
else
    echo -e "${RED}❌ Configuration verification failed${NC}"
    exit 1
fi

# Test Apache configuration
echo -e "${BLUE}🧪 Testing Apache configuration...${NC}"
if sudo /Applications/MAMP/bin/apache2/bin/apachectl configtest; then
    echo -e "${GREEN}✅ Apache configuration is valid${NC}"
else
    echo -e "${RED}❌ Apache configuration has errors${NC}"
    echo -e "${YELLOW}💡 Please check the configuration manually${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Apache configuration fixed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo "  • Fixed include path for httpd-vhosts.conf"
echo "  • Created backup of original configuration"
echo "  • Verified Apache configuration is valid"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  1. Restart MAMP to apply changes"
echo "  2. Test virtual host operations"
echo "  3. If issues persist, check MAMP logs"
echo ""
echo -e "${YELLOW}⚠️ Note: If you encounter issues, you can restore from backup:${NC}"
echo "  sudo cp $APACHE_CONF.backup.* $APACHE_CONF"
