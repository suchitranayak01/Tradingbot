# Deploying to Streamlit Community Cloud

## Steps to Deploy Your Trading Bot

### 1. Prepare Your Repository
✅ Your code is already on GitHub at: https://github.com/suchitranayak01/Tradingbot

### 2. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/

2. **Sign in with GitHub**
   - Click "Sign in" 
   - Authorize with your GitHub account (suchitranayak01)

3. **Deploy Your App**
   - Click "New app"
   - Select repository: `suchitranayak01/Tradingbot`
   - Branch: `main`
   - Main file path: `dashboard.py`
   - Click "Deploy!"

4. **Configure Secrets (Important!)**
   - After deployment starts, click on "⚙️ Settings" → "Secrets"
   - Copy the content from `.streamlit/secrets.toml.example`
   - Replace with your actual credentials
   - Save

### 3. Your App Will Be Live At:
```
https://suchitranayak01-tradingbot-dashboard-xxxxx.streamlit.app
```

## Important Notes

⚠️ **Security:**
- Never commit `config.yaml` or `.streamlit/secrets.toml` to GitHub
- Always use Streamlit Cloud's secrets management for credentials
- The `.gitignore` file is configured to protect sensitive files

📝 **Free Tier Limits:**
- 1 GB of storage
- Sleeps after 7 days of inactivity
- Can wake up on first visit

🔄 **Auto-Deploy:**
- Any push to `main` branch will auto-update your live app

## Alternative Deployment Options

### Option 1: Heroku
```bash
# Requires Procfile and setup.sh
heroku create tradingbot-app
git push heroku main
```

### Option 2: AWS/GCP/Azure
- Deploy as a containerized app
- Requires Dockerfile

### Option 3: Self-Hosted
```bash
python3 -m streamlit run dashboard.py --server.port 80
```

## Troubleshooting

**App won't start:**
- Check logs in Streamlit Cloud dashboard
- Verify all dependencies in requirements.txt
- Check secrets are properly configured

**Can't connect to broker:**
- Verify API credentials in secrets
- Check if broker API allows cloud IP addresses
- Some brokers may require IP whitelisting
