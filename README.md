# Automated Cold Email Outreach System

A 100% free, fully automated cold email outreach system that runs daily via GitHub Actions. Uses Google Sheets for contact management, BeautifulSoup for website scraping, Google Gemini AI for personalization, and Gmail SMTP for delivery.

## Architecture

| Component | Tool (Free Tier) |
|-----------|------------------|
| Database | Google Sheets API |
| Compute | GitHub Actions (cron) |
| Scraping | BeautifulSoup + Requests |
| AI Generation | Google Gemini API (gemini-1.5-flash) |
| Email | Gmail SMTP (smtplib) |

## Quick Start

### 1. Google Cloud Setup (Service Account)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to **IAM & Admin > Service Accounts**
5. Create Service Account → Name it → Grant **Editor** role → Done
6. Click the service account → **Keys** tab → **Add Key** → **Create new key** → **JSON**
7. Save the downloaded JSON file securely
8. Share your Google Sheet with the service account email (found in JSON as `client_email`) with **Editor** access

### 2. Google Sheet Setup

Create a Google Sheet with these exact column headers in Row 1:
```
First Name | Last Name | Email | Company | Website | Date Sent
```

Fill in your contacts (leave "Date Sent" blank for new contacts).
Copy the **Spreadsheet ID** from the URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`

### 3. Gmail App Password

1. Enable 2-Factor Authentication on your Google Account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Create new app password → Name it "Outreach Bot" → Copy the 16-char password
4. Use your Gmail address as `EMAIL_USER` and the app password as `EMAIL_PASSWORD`

### 4. Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create API Key → Copy it
3. Uses `gemini-1.5-flash` model (free tier: 1500 req/day)

### 5. GitHub Repository Secrets

Go to your repo → **Settings > Secrets and variables > Actions > New repository secret**. Add all 5:

| Secret Name | Value |
|-------------|-------|
| `GEMINI_API_KEY` | Your Gemini API key from AI Studio |
| `EMAIL_USER` | Your Gmail address (e.g., `you@gmail.com`) |
| `EMAIL_PASSWORD` | 16-char Gmail App Password |
| `GOOGLE_CREDENTIALS` | **Entire JSON content** from Service Account key file |
| `SPREADSHEET_ID` | Your Google Sheet ID from the URL |

### 6. Enable GitHub Actions

1. Push this repo to GitHub
2. Go to **Actions** tab → Enable workflows
3. The workflow runs daily at **9:00 AM UTC** (adjust cron in `.github/workflows/outreach.yml` for your timezone)
4. Or trigger manually via **Actions > Daily Cold Email Outreach > Run workflow**

## How It Works

1. **Reads** Google Sheet for rows where "Date Sent" is empty
2. **Limits** to first 50 contacts per run (respects Gmail free limits)
3. **Scrapes** each company website for context
4. **Generates** personalized hook via Gemini AI
5. **Sends** personalized email via Gmail SMTP
6. **Updates** "Date Sent" column with timestamp immediately after sending
7. **Logs** all activity to `outreach.log` (uploaded as artifact)

## Email Template

The system uses this exact template (customize in `outreach_script.py`):

```
Subject: Connecting regarding Software Engineering / AI roles at {Company}

Hi {First Name},

I was researching {Company} and was really impressed by how you are tackling {AI_Generated_Problem_Statement}.

I am a Computer Science graduate specializing in Cyber Security with a strong foundation in Python, C++, and AI/ML infrastructure. Recently, during my internship at Amazon, I built an optimization-driven data pipeline that improved operational efficiency by 36.81% across 54 stations. I have also developed production-ready computer vision systems (YOLOv11) and RAG-based LLM pipelines. I would love to bring this same results-driven engineering mindset to the team at {Company}.

My resume and GitHub are linked below, showcasing my system architecture and my top 0.14% global ranking in TCS CodeVita. Are you currently considering entry-level candidates for any upcoming roles?

Best regards,
Sahil Bhagwat Jadhav
+91 8482976123 | sahiljadhav618@gmail.com
[Link to LinkedIn]
[Link to GitHub / Portfolio]
```

## Rate Limits & Safety

- **Gmail SMTP**: ~500 emails/day free tier (we limit to 50/day)
- **Gemini API**: 1500 requests/day free tier
- **GitHub Actions**: 2000 min/month free
- **Sleep**: 2 seconds between emails to prevent throttling
- **Error Handling**: Graceful fallback to generic hook if scraping/AI fails

## Monitoring

- Check **Actions** tab for run history
- Download `outreach-logs` artifact for detailed logs
- Google Sheet "Date Sent" column tracks sent emails

## Customization

Edit `outreach_script.py`:
- `DAILY_LIMIT` (line ~20): Change max emails per run
- `EMAIL_TEMPLATE`: Modify email content
- `GEMINI_PROMPT`: Adjust AI prompt
- `SCRAPE_HEADERS`: Modify User-Agent if needed
- Cron schedule in `.github/workflows/outreach.yml`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GOOGLE_CREDENTIALS` error | Ensure JSON is valid, no extra whitespace, service account has Editor access to Sheet |
| Gmail auth failed | Verify 2FA enabled, App Password correct (not regular password) |
| Gemini API error | Check API key valid, quota not exceeded |
| Scraping fails | Site may block bots; fallback hook will be used |
| Sheet not updating | Verify service account email has Editor access on the Sheet |

## License

MIT License - Free to use and modify.