#!/usr/bin/env python3
"""
Setup Helper Script
Helps you set up the Google Sheet, Service Account, and test the outreach script.
"""
import os
import json
import csv
import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file"
]


def create_sample_sheet(service_account_json: str, sheet_title: str = "Outreach Companies") -> str:
    """Create a new Google Sheet with the companies template and share with service account."""
    creds = Credentials.from_service_account_info(
        json.loads(service_account_json), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    
    # Create new spreadsheet
    sh = gc.create(sheet_title)
    sheet_id = sh.id
    
    # Share with service account email (optional, but helpful)
    sa_email = json.loads(service_account_json)["client_email"]
    
    # Get the first worksheet
    worksheet = sh.sheet1
    
    # Load template CSV
    with open("companies_template.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)
    
    # Write to sheet
    worksheet.update("A1", rows)
    
    print(f"✅ Created Google Sheet: {sheet_title}")
    print(f"📋 Sheet ID: {sheet_id}")
    print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    print(f"📧 Share this sheet with: {sa_email} (Editor access)")
    
    return sheet_id


def test_connection(service_account_json: str, sheet_id: str):
    """Test connection to Google Sheet."""
    creds = Credentials.from_service_account_info(
        json.loads(service_account_json), scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    worksheet = sh.sheet1
    
    # Read first few rows
    data = worksheet.get_all_records()
    print(f"✅ Connected to sheet: {sh.title}")
    print(f"📊 Found {len(data)} company records")
    for row in data[:3]:
        print(f"   - {row.get('company_name', 'N/A')}: {row.get('contact_first_name', 'N/A')} {row.get('contact_last_name', 'N/A')}")


def test_gemini_api(api_key: str):
    """Test Google Generative AI API."""
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("Say 'API working' in one word.")
    print(f"✅ Gemini API working: {response.text.strip()}")


def main():
    print("🚀 Outreach Automation Setup Helper")
    print("=" * 50)
    
    # Get service account JSON
    sa_json = input("\n📋 Paste your Google Service Account JSON (single line): ").strip()
    if not sa_json:
        print("❌ Service account JSON required")
        return
    
    # Create or use existing sheet
    choice = input("\n📋 Create new Google Sheet from template? (y/n): ").strip().lower()
    if choice == 'y':
        sheet_title = input("Sheet title (default: 'Outreach Companies'): ").strip() or "Outreach Companies"
        sheet_id = create_sample_sheet(sa_json, sheet_title)
    else:
        sheet_id = input("📋 Enter existing Google Sheet ID: ").strip()
    
    if not sheet_id:
        print("❌ Sheet ID required")
        return
    
    # Test connection
    print("\n🔍 Testing Google Sheets connection...")
    try:
        test_connection(sa_json, sheet_id)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test Gemini API
    api_key = input("\n🔑 Enter Google AI Studio API Key (or press Enter to skip): ").strip()
    if api_key:
        print("\n🔍 Testing Gemini API...")
        try:
            test_gemini_api(api_key)
        except Exception as e:
            print(f"❌ Gemini API test failed: {e}")
    
    # Write .env file
    env_content = f"""GOOGLE_SERVICE_ACCOUNT_JSON={sa_json}
GOOGLE_SHEET_ID={sheet_id}
GOOGLE_API_KEY={api_key or "your_api_key_here"}
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("\n✅ Created .env file")
    print("\n🎉 Setup complete! Run the outreach script with:")
    print("   python outreach_script.py --dry-run  # Test run (no emails sent)")
    print("   python outreach_script.py            # Live run")


if __name__ == "__main__":
    main()