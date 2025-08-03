#!/bin/bash

# Simple Cricket RAG Azure Deployment (No Container Registry)
set -e

# Configuration
RESOURCE_GROUP="cricket-rag-rg"
LOCATION="eastus"
CONTAINER_NAME="cricket-rag-api"
DNS_NAME="cricket-rag-api-$(date +%s)"

echo "🏏 Simple Cricket RAG Azure Deployment"
echo "======================================"

# Build Docker image locally
echo "🔨 Building Docker image locally..."
cd ..
docker build -f docker/Dockerfile -t cricket-rag:latest .

# Save image to tar file
echo "📦 Saving Docker image..."
docker save cricket-rag:latest > cricket-rag.tar

# Upload to temporary storage (we'll use a different approach)
echo "🚀 Creating container instance with local image..."

# Create container instance using Docker Hub or direct deployment
# First, let's try with a public registry approach

# Tag and push to Docker Hub (you'll need to login)
echo "Please login to Docker Hub:"
docker login

# Tag for Docker Hub (replace with your username)
read -p "Enter your Docker Hub username: " DOCKER_USERNAME
docker tag cricket-rag:latest $DOCKER_USERNAME/cricket-rag:latest
docker push $DOCKER_USERNAME/cricket-rag:latest

# Create container instance
echo "🚀 Creating container instance..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $DOCKER_USERNAME/cricket-rag:latest \
    --dns-name-label $DNS_NAME \
    --ports 8000 \
    --cpu 2 \
    --memory 4 \
    --restart-policy Always \
    --environment-variables PYTHONPATH=/app PYTHONWARNINGS=ignore::FutureWarning

# Get the FQDN
FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query ipAddress.fqdn --output tsv)

echo "✅ Deployment completed!"
echo "🌐 Your API is available at: http://$FQDN:8000"
echo "📖 API docs at: http://$FQDN:8000/docs"
echo "🏥 Health check: http://$FQDN:8000/health"

# Cleanup
rm -f cricket-rag.tar

echo ""
echo "📋 Next steps:"
echo "1. Wait 2-3 minutes for container to start"
echo "2. Test: curl http://$FQDN:8000/health"
echo "3. Ingest data: curl -X POST http://$FQDN:8000/ingest"