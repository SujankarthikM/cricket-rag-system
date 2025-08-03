# 🚀 Quick Azure Deployment Guide

## Prerequisites
- Azure CLI installed
- Docker installed
- Azure for Students account

## One-Command Deployment

```bash
cd azure_deployment
./deploy.sh
```

## What happens:
1. **Login** to Azure (browser popup)
2. **Create** resource group `cricket-rag-rg`
3. **Build** Docker image
4. **Deploy** to Azure Container Instances
5. **Get** public URL: `http://cricket-rag-api-xxx.eastus.azurecontainer.io:8000`

## After Deployment:

### Test your API:
```bash
# Replace YOUR_URL with the URL from deployment
export API_URL="http://cricket-rag-api-xxx.eastus.azurecontainer.io:8000"

# Health check
curl $API_URL/health

# Ingest data
curl -X POST $API_URL/ingest

# Search
curl -X POST $API_URL/search \
  -H "Content-Type: application/json" \
  -d '{"query": "cricket batting techniques"}'

# Get full context (use document_id from search results)
curl $API_URL/context/cricketrules.pdf_1
```

### Interactive docs:
Visit: `http://your-url:8000/docs`

## Cost Management:
- **Monitor usage**: Azure portal → Cost Management
- **Set alerts**: Budget alerts at $10, $20
- **Auto-shutdown**: Available in advanced settings

## Cleanup:
```bash
az group delete --name cricket-rag-rg --yes
```

## Troubleshooting:

### Container not starting:
```bash
az container logs --resource-group cricket-rag-rg --name cricket-rag-api
```

### Update deployment:
```bash
# Rebuild and redeploy
./deploy.sh
```

### Scale up if needed:
```bash
az container create \
  --cpu 4 \
  --memory 8 \
  # ... other options
```

## Custom Domain (Optional):
1. Buy domain from Azure/external
2. Create DNS CNAME record
3. Point to your container FQDN
4. Add SSL certificate

---
**Your Cricket RAG API will be live at a public URL! 🎉**