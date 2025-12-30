#!/bin/bash
#
# create-airgapped-package.sh
#
# Creates a complete airgapped deployment package for Scoring Engine
# This script must be run on a system with internet access
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_DIR="scoringengine-airgapped"
IMAGES_DIR="${PACKAGE_DIR}/docker-images"
OUTPUT_ARCHIVE="scoringengine-airgapped.tar.gz"

echo -e "${GREEN}=== Scoring Engine Airgapped Package Creator ===${NC}"
echo ""
echo "This script will create a complete airgapped deployment package."
echo "It will:"
echo "  1. Build all Docker images"
echo "  2. Export images to tar files"
echo "  3. Package with source code"
echo "  4. Create deployment scripts"
echo "  5. Generate compressed archive"
echo ""
echo -e "${YELLOW}WARNING: This requires internet access and will take several minutes.${NC}"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}ERROR: Docker Compose is not installed or not in PATH${NC}"
    exit 1
fi

# Clean up any previous package
if [ -d "${PACKAGE_DIR}" ]; then
    echo -e "${YELLOW}Removing existing package directory...${NC}"
    rm -rf "${PACKAGE_DIR}"
fi

if [ -f "${OUTPUT_ARCHIVE}" ]; then
    echo -e "${YELLOW}Removing existing package archive...${NC}"
    rm -f "${OUTPUT_ARCHIVE}"
fi

# Step 1: Build all images
echo ""
echo -e "${GREEN}Step 1: Building all Docker images...${NC}"
echo "This may take several minutes..."
docker-compose build --no-cache

# Step 2: Create directories
echo ""
echo -e "${GREEN}Step 2: Creating package structure...${NC}"
mkdir -p "${IMAGES_DIR}"

# Step 3: Export base images
echo ""
echo -e "${GREEN}Step 3: Exporting base Docker images...${NC}"

echo "  - Exporting python:3.14.1-slim-bookworm..."
docker save python:3.14.1-slim-bookworm -o "${IMAGES_DIR}/python-base.tar"

echo "  - Exporting redis:7.0.4..."
docker save redis:7.0.4 -o "${IMAGES_DIR}/redis.tar"

echo "  - Exporting mariadb:10..."
docker save mariadb:10 -o "${IMAGES_DIR}/mariadb.tar"

echo "  - Exporting nginx:1.23.1..."
docker save nginx:1.23.1 -o "${IMAGES_DIR}/nginx.tar"

# Step 4: Export application images
echo ""
echo -e "${GREEN}Step 4: Exporting Scoring Engine images...${NC}"

echo "  - Exporting scoringengine/base..."
docker save scoringengine/base -o "${IMAGES_DIR}/scoringengine-base.tar"

echo "  - Exporting scoringengine/bootstrap..."
docker save scoringengine/bootstrap -o "${IMAGES_DIR}/scoringengine-bootstrap.tar"

echo "  - Exporting scoringengine/engine..."
docker save scoringengine/engine -o "${IMAGES_DIR}/scoringengine-engine.tar"

echo "  - Exporting scoringengine/worker..."
docker save scoringengine/worker -o "${IMAGES_DIR}/scoringengine-worker.tar"

echo "  - Exporting scoringengine/web..."
docker save scoringengine/web -o "${IMAGES_DIR}/scoringengine-web.tar"

# Step 5: Copy source code
echo ""
echo -e "${GREEN}Step 5: Copying source code...${NC}"
mkdir -p "${PACKAGE_DIR}/scoringengine"

# Copy essential files and directories
cp -r scoring_engine "${PACKAGE_DIR}/scoringengine/"
cp -r docker "${PACKAGE_DIR}/scoringengine/"
cp -r bin "${PACKAGE_DIR}/scoringengine/"
cp -r configs "${PACKAGE_DIR}/scoringengine/"
cp -r docs "${PACKAGE_DIR}/scoringengine/"
cp docker-compose.yml "${PACKAGE_DIR}/scoringengine/"
cp pyproject.toml "${PACKAGE_DIR}/scoringengine/"
cp README.md "${PACKAGE_DIR}/scoringengine/"
cp LICENSE "${PACKAGE_DIR}/scoringengine/"
[ -f Makefile ] && cp Makefile "${PACKAGE_DIR}/scoringengine/"

# Step 6: Create load script
echo ""
echo -e "${GREEN}Step 6: Creating deployment scripts...${NC}"

cat > "${PACKAGE_DIR}/load-images.sh" << 'EOF'
#!/bin/bash
set -e

echo "=== Loading Docker Images for Airgapped Deployment ==="
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH"
    exit 1
fi

# Load base images
echo "Loading base images..."
docker load -i docker-images/python-base.tar
docker load -i docker-images/redis.tar
docker load -i docker-images/mariadb.tar
docker load -i docker-images/nginx.tar

# Load application images
echo ""
echo "Loading Scoring Engine images..."
docker load -i docker-images/scoringengine-base.tar
docker load -i docker-images/scoringengine-bootstrap.tar
docker load -i docker-images/scoringengine-engine.tar
docker load -i docker-images/scoringengine-worker.tar
docker load -i docker-images/scoringengine-web.tar

echo ""
echo "All images loaded successfully!"
echo ""
echo "Loaded images:"
docker images | grep -E "(scoringengine|redis|mariadb|nginx|python)" | grep -E "(3.14.1-slim-bookworm|7.0.4|10|1.23.1|latest)"

echo ""
echo "Next steps:"
echo "  1. cd scoringengine"
echo "  2. Edit bin/competition.yaml with your competition setup"
echo "  3. docker-compose up -d"
echo ""
EOF

chmod +x "${PACKAGE_DIR}/load-images.sh"

# Step 7: Create README
cat > "${PACKAGE_DIR}/README.txt" << 'EOF'
SCORING ENGINE - AIRGAPPED DEPLOYMENT PACKAGE
==============================================

This package contains everything needed to deploy Scoring Engine
in an airgapped environment with no internet access.

PREREQUISITES:
--------------
- Docker installed on target system
- Docker Compose installed on target system
- Sufficient disk space (approximately 3-4 GB)

DEPLOYMENT STEPS:
-----------------

1. Transfer this entire directory to the airgapped system

2. Load Docker images:
   ./load-images.sh

   This will load all required Docker images into the local Docker registry.

3. Navigate to the application directory:
   cd scoringengine

4. Configure your competition:
   Edit bin/competition.yaml with your competition setup.
   Edit docker-compose.yml to change default passwords (REQUIRED for production).

5. Start the scoring engine:
   SCORINGENGINE_OVERWRITE_DB=true docker-compose up -d

   (Use SCORINGENGINE_OVERWRITE_DB=true only on first deployment to initialize the database)

6. Access the web interface:
   http://localhost (or http://SERVER_IP)

   Default credentials (if using example mode):
   - whiteteamuser:testpass
   - team1user1:testpass
   - team2user1:testpass

MANAGEMENT COMMANDS:
--------------------

View status:
  docker-compose ps

View logs:
  docker-compose logs -f

Stop engine (pause competition):
  docker-compose stop engine

Start engine (resume competition):
  docker-compose start engine

Stop all services:
  docker-compose down

Restart all services:
  docker-compose restart

IMPORTANT SECURITY NOTES:
-------------------------

1. Change default passwords in docker-compose.yml before deployment:
   - MYSQL_ROOT_PASSWORD
   - MYSQL_PASSWORD

2. Update user passwords in bin/competition.yaml

3. Configure firewall rules as needed for your competition environment

TROUBLESHOOTING:
----------------

If containers fail to start:
- Check logs: docker-compose logs -f
- Verify all images loaded: docker images
- Ensure database has initialized (takes 30-60 seconds on first start)

If you encounter "image not found" errors:
- Re-run: ./load-images.sh
- Verify image names match docker-compose.yml

DOCUMENTATION:
--------------

For detailed documentation, see:
  scoringengine/docs/source/installation/airgapped.rst

Or visit: https://scoringengine.readthedocs.io/

PACKAGE CONTENTS:
-----------------

- docker-images/     : All Docker images as tar files
- scoringengine/     : Complete source code and configuration
- load-images.sh     : Script to load Docker images
- README.txt         : This file

SUPPORT:
--------

For issues or questions:
- GitHub: https://github.com/scoringengine/scoringengine/issues
- Documentation: https://scoringengine.readthedocs.io/

Created with: bin/create-airgapped-package.sh
EOF

# Step 8: Create manifest file
echo ""
echo -e "${GREEN}Step 7: Creating package manifest...${NC}"

cat > "${PACKAGE_DIR}/MANIFEST.txt" << EOF
SCORING ENGINE AIRGAPPED PACKAGE MANIFEST
==========================================

Created: $(date)
Hostname: $(hostname)
User: $(whoami)

DOCKER IMAGES:
--------------

Base Images:
  - python:3.14.1-slim-bookworm
  - redis:7.0.4
  - mariadb:10
  - nginx:1.23.1

Application Images:
  - scoringengine/base
  - scoringengine/bootstrap
  - scoringengine/engine
  - scoringengine/worker
  - scoringengine/web

IMAGE SIZES:
------------

EOF

du -sh "${IMAGES_DIR}"/*.tar | sed 's/^/  /' >> "${PACKAGE_DIR}/MANIFEST.txt"

cat >> "${PACKAGE_DIR}/MANIFEST.txt" << EOF

TOTAL SIZE:
-----------

EOF

du -sh "${IMAGES_DIR}" >> "${PACKAGE_DIR}/MANIFEST.txt"

echo "" >> "${PACKAGE_DIR}/MANIFEST.txt"
echo "CHECKSUMS (SHA256):" >> "${PACKAGE_DIR}/MANIFEST.txt"
echo "-------------------" >> "${PACKAGE_DIR}/MANIFEST.txt"
echo "" >> "${PACKAGE_DIR}/MANIFEST.txt"

cd "${IMAGES_DIR}"
sha256sum *.tar >> ../MANIFEST.txt
cd ../..

# Step 8: Create compressed archive
echo ""
echo -e "${GREEN}Step 8: Creating compressed archive...${NC}"
echo "This may take several minutes..."

tar czf "${OUTPUT_ARCHIVE}" "${PACKAGE_DIR}/"

# Summary
echo ""
echo -e "${GREEN}=== Package Creation Complete ===${NC}"
echo ""
echo "Package created: ${OUTPUT_ARCHIVE}"
echo "Package size: $(du -sh ${OUTPUT_ARCHIVE} | cut -f1)"
echo ""
echo "Package contents:"
echo "  - Docker images: $(ls ${IMAGES_DIR}/*.tar | wc -l) files"
echo "  - Total image size: $(du -sh ${IMAGES_DIR} | cut -f1)"
echo ""
echo "Next steps:"
echo "  1. Transfer ${OUTPUT_ARCHIVE} to the airgapped system"
echo "  2. Extract: tar xzf ${OUTPUT_ARCHIVE}"
echo "  3. Follow instructions in ${PACKAGE_DIR}/README.txt"
echo ""
echo -e "${GREEN}Package ready for airgapped deployment!${NC}"
