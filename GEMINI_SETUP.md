# GEMINI AI INTEGRATION SETUP (Optional)

## What is Gemini AI Integration?

The enhanced script can now use Google's Gemini AI to generate diverse, unique search topics instead of relying on fixed lists. This makes your searches even more varied and human-like.

## Benefits of Using Gemini AI:

✅ **Unique Topics**: AI generates fresh topics every time
✅ **Diverse Content**: Mix of technology, news, entertainment, education
✅ **Contextual**: Topics relevant to current trends and India
✅ **Anti-Detection**: Never repeat the same search patterns
✅ **Smart**: AI understands what topics humans actually search for

## Setup Instructions:

### Step 1: Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated API key

### Step 2: Add API Key to Config
1. Open `config.json` in your project folder
2. Find the line: `"gemini_api_key": ""`
3. Replace it with: `"gemini_api_key": "YOUR_API_KEY_HERE"`
4. Save the file

### Step 3: Test the Integration
Run the enhanced script:
```bash
python micro_enhanced.py
```

Choose option 4 for "Gemini AI Generated Topics" when prompted.

## Example Generated Topics:

When you use Gemini AI, it might generate topics like:
- "Latest ChatGPT features 2025"
- "India space mission updates"
- "Electric car charging stations Delhi"
- "Best streaming shows January 2025"
- "Cryptocurrency regulations India"
- "AI tools for students"
- "Climate change solutions technology"

## Cost Information:

- Gemini API has a generous free tier
- Typical usage: ~0.001$ per search session
- 15 searches = approximately free
- [Check current pricing](https://ai.google.dev/pricing)

## If You Don't Want Gemini:

No problem! The script works perfectly without it. You can still use:
- **Google News Headlines** (Recommended) - Fresh and diverse
- **Google Trends** - Traditional trending topics
- **Mixed Sources** - Best of both worlds

## Troubleshooting:

### Error: "API key not found"
- Make sure you added the API key to `config.json`
- Check that there are no extra spaces or quotes

### Error: "API quota exceeded"
- You've used the free tier limit
- Wait 24 hours or upgrade to paid plan

### Error: "Import error"
- Run: `pip install google-generativeai`

## Security Note:

⚠️ **Keep your API key safe!**
- Don't share it with others
- Don't commit it to public repositories
- Regenerate it if compromised
