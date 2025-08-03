#!/bin/bash

# Cricket RAG Azure Deployment Script
# Run this script to deploy to Azure Container Instances

set -e

# Configuration
RESOURCE_GROUP="cricket-rag-rg"
LOCATION="eastus"
CONTAINER_NAME="cricket-rag-api"
IMAGE_NAME="cricket-rag:latest"
REGISTRY_NAME="cricketragregistry"
DNS_NAME="cricket-rag-api-$(date +%s)"

echo "🏏 Cricket RAG Azure Deployment"
echo "================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo "🔐 Logging into Azure..."
az login

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)

# Build and push Docker image
echo "🔨 Building and pushing Docker image..."
cd ..
docker build -f docker/Dockerfile -t $IMAGE_NAME .
docker tag $IMAGE_NAME $ACR_LOGIN_SERVER/$IMAGE_NAME

# Login to ACR and push
az acr login --name $REGISTRY_NAME
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --resource-group $RESOURCE_GROUP --query passwords[0].value --output tsv)

# Create container instance
echo "🚀 Creating container instance..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
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

echo ""
echo "📋 Next steps:"
echo "1. Ingest data: curl -X POST http://$FQDN:8000/ingest"
echo "2. Test search: curl -X POST http://$FQDN:8000/search -H 'Content-Type: application/json' -d '{\"query\":\"cricket\"}'"
echo "3. Upload files: Use the /upload endpoint"

echo ""
echo "💰 Cost estimate: ~$15-25/month with Azure for Students"
echo "🗑️  To delete everything: az group delete --name $RESOURCE_GROUP --yes"