# Deployment Guide for VoxOver

This guide will help you deploy your VoxOver app to Streamlit Community Cloud (free hosting).

## Option 1: Streamlit Community Cloud (Recommended - Free)

### Prerequisites
1. A GitHub account
2. Your code pushed to a GitHub repository
3. API keys ready (OpenAI, ElevenLabs)

### Step-by-Step Instructions

#### 1. Push Your Code to GitHub

If you haven't already, push your code to GitHub:

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

#### 2. Sign Up for Streamlit Community Cloud

1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Click "Sign up" and sign in with your GitHub account
3. Authorize Streamlit to access your GitHub repositories

#### 3. Deploy Your App

1. Click "New app" in the Streamlit Cloud dashboard
2. Select your GitHub repository
3. Choose the branch (usually `main` or `master`)
4. Set the main file path to: `app.py`
5. Click "Deploy"

#### 4. Configure Secrets (API Keys)

**Important:** Never commit your `.env` file to GitHub! Instead, use Streamlit's secrets management.

1. In your Streamlit Cloud app dashboard, click "⚙️ Settings" → "Secrets"
2. Add your secrets in TOML format:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
ELEVENLABS_API_KEY = "your_elevenlabs_api_key_here"
ELEVENLABS_VOICE_ID = "your_voice_id_here"
APP_USERNAME = "your_username_here"
PASSWORD = "your_password_here"
```

3. Click "Save"
4. Your app will automatically redeploy with the new secrets

#### 5. Important Notes for Streamlit Cloud

- **FFmpeg**: Streamlit Cloud includes FFmpeg by default, so you don't need to install it
- **File Storage**: Temporary files are stored in the app's temporary directory
- **Resource Limits**: Free tier has some limits on memory and CPU usage
- **File Size Limits**: Large video uploads may take time to process

### Your App URL

Once deployed, your app will be available at:
```
https://your-app-name.streamlit.app
```

## Option 2: Self-Hosting on a Server

### Requirements
- A server with Python 3.8+
- FFmpeg installed
- Domain name (optional, for custom URL)

### Installation Steps

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Install FFmpeg**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

3. **Set Environment Variables**
```bash
export OPENAI_API_KEY="your_key"
export ELEVENLABS_API_KEY="your_key"
export ELEVENLABS_VOICE_ID="your_voice_id"
export APP_USERNAME="your_username"
export PASSWORD="your_password"
```

4. **Run Streamlit**
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

5. **Use a Process Manager (Optional)**
For production, use `systemd`, `supervisor`, or `pm2` to keep the app running.

## Option 3: Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t voxover .
docker run -p 8501:8501 -e OPENAI_API_KEY=your_key -e ELEVENLABS_API_KEY=your_key voxover
```

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Make sure all dependencies are in `requirements.txt`
   - Check that Streamlit Cloud is using the correct Python version

2. **FFmpeg errors**
   - Streamlit Cloud includes FFmpeg automatically
   - For self-hosting, verify FFmpeg is installed: `ffmpeg -version`

3. **API key errors**
   - Verify secrets are set correctly in Streamlit Cloud
   - Check that secret names match exactly (case-sensitive)

4. **Memory errors**
   - Large videos may cause memory issues
   - Consider processing smaller videos or upgrading resources

5. **Slow processing**
   - Video processing is CPU-intensive
   - Consider optimizing video size before upload

## Security Best Practices

1. **Never commit `.env` files** - Use `.gitignore`
2. **Use Streamlit secrets** for cloud deployment
3. **Rotate API keys** regularly
4. **Use strong passwords** for app authentication
5. **Monitor API usage** to prevent unexpected costs

## Cost Considerations

- **Streamlit Community Cloud**: Free (with usage limits)
- **OpenAI API**: Pay-per-use (check pricing)
- **ElevenLabs API**: Pay-per-use (check pricing)
- **Self-hosting**: Server costs vary

## Support

For issues or questions:
- Check Streamlit documentation: https://docs.streamlit.io/
- Streamlit Community: https://discuss.streamlit.io/

