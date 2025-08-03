# Azure Deployment Guide for Cricket RAG System

## Prerequisites
- Azure for Students account
- Azure CLI installed
- Docker installed locally

## Deployment Options

### Option 1: Azure Container Instances (Recommended for Students)

```bash
# Login to Azure
az login

# Create resource group
az group create --name cricket-rag-rg --location eastus

# Create container instance
az container create \
  --resource-group cricket-rag-rg \
  --name cricket-rag-container \
  --image your-registry/cricket-rag:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --ip-address public \
  --environment-variables PYTHONPATH=/app
```

### Option 2: Azure App Service

```bash
# Create App Service plan (Free tier)
az appservice plan create \
  --name cricket-rag-plan \
  --resource-group cricket-rag-rg \
  --sku F1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group cricket-rag-rg \
  --plan cricket-rag-plan \
  --name cricket-rag-api \
  --deployment-container-image-name your-registry/cricket-rag:latest
```

### Option 3: Azure VM (Most Flexible)

```bash
# Create VM
az vm create \
  --resource-group cricket-rag-rg \
  --name cricket-rag-vm \
  --image UbuntuLTS \
  --admin-username azureuser \
  --generate-ssh-keys \
  --size Standard_B2s

# Open port 8000
az vm open-port \
  --port 8000 \
  --resource-group cricket-rag-rg \
  --name cricket-rag-vm
```

## Cost Estimates (Azure for Students)

### Free Tier (First 12 months)
- **Container Instances**: 1 million requests/month
- **App Service**: F1 plan (1GB memory, 1GB storage)
- **VM**: B1s (1 vCPU, 1GB RAM) - Limited hours
- **Storage**: 5GB blob storage

### After Free Tier
- **Container Instances**: ~$10-20/month
- **App Service**: ~$13-20/month
- **VM B2s**: ~$15-25/month
- **Storage**: ~$2-5/month

## Deployment Steps

### 1. Build and Push Docker Image

```bash
# Build image
docker build -f docker/Dockerfile -t cricket-rag .

# Tag for Azure Container Registry
docker tag cricket-rag cricketrag.azurecr.io/cricket-rag:latest

# Push to registry
docker push cricketrag.azurecr.io/cricket-rag:latest
```

### 2. Deploy using Azure CLI

```bash
# Set variables
RESOURCE_GROUP="cricket-rag-rg"
LOCATION="eastus"
APP_NAME="cricket-rag-api"

# Create container instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --image cricketrag.azurecr.io/cricket-rag:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --ip-address public \
  --restart-policy Always
```

### 3. Verify Deployment

```bash
# Get public IP
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --query ipAddress.ip \
  --output tsv

# Test API
curl http://<PUBLIC_IP>:8000/health
```

## Environment Variables

Set these in Azure:

```bash
az container create \
  # ... other options ... \
  --environment-variables \
    PYTHONPATH=/app \
    CHROMA_PERSIST_DIRECTORY=/app/chroma_db
```

## Monitoring and Logs

```bash
# View logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME

# Stream logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --follow
```

## Storage Setup

For persistent storage:

```bash
# Create storage account
az storage account create \
  --name cricketragstg \
  --resource-group $RESOURCE_GROUP \
  --sku Standard_LRS

# Create file share
az storage share create \
  --name cricket-data \
  --account-name cricketragstg
```

## Scaling Options

### Auto-scaling (Container Instances)
```yaml
# azure-deploy.yml
apiVersion: '2021-09-01'
type: Microsoft.ContainerInstance/containerGroups
properties:
  containers:
  - name: cricket-rag
    properties:
      resources:
        requests:
          cpu: 1
          memoryInGB: 2
        limits:
          cpu: 2
          memoryInGB: 4
```

## Security Best Practices

1. **Use managed identity** for Azure services
2. **Enable HTTPS** with Azure Front Door
3. **Set up firewall rules** to restrict access
4. **Use Key Vault** for secrets

```bash
# Enable HTTPS
az network application-gateway create \
  --name cricket-rag-gateway \
  --resource-group $RESOURCE_GROUP \
  --capacity 1 \
  --sku Standard_v2
```

## Troubleshooting

### Common Issues

1. **Out of memory**: Increase memory allocation
2. **Slow startup**: Use smaller embedding model
3. **Port conflicts**: Ensure port 8000 is open
4. **SSL errors**: Configure HTTPS properly

### Debug Commands

```bash
# Check resource usage
az monitor metrics list \
  --resource $RESOURCE_ID \
  --metric "CpuUsage,MemoryUsage"

# Container logs
az container logs --resource-group $RG --name $NAME --follow
```

## Cost Optimization

1. **Use B-series VMs** (burstable performance)
2. **Auto-shutdown VMs** during off-hours
3. **Use Azure Functions** for light workloads
4. **Monitor usage** with Azure Cost Management

## Next Steps

1. Set up CI/CD pipeline with GitHub Actions
2. Configure monitoring with Application Insights
3. Set up backup strategy for vector database
4. Implement caching layer with Redis

---

**Note**: Always monitor your Azure spending through the Azure portal to avoid unexpected charges!