# 🚀 Microsoft Bing Search Automation

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://microsoft.com/windows)

> **⚠️ Educational Purpose Only**: This tool is created for educational purposes to demonstrate automation techniques. Users are responsible for complying with Microsoft's Terms of Service and any applicable laws.

## 📋 Overview

An advanced Bing search automation tool that integrates with your actual Chrome profiles, uses fresh content sources, and follows Microsoft's guidelines with human-like behavior patterns. Perfect for Microsoft Rewards users who want to automate their daily searches while maintaining authenticity.

## ✨ Key Features

### � **Chrome Profile Integration**
- **Real Account Usage**: Works with your logged-in Chrome profiles
- **Multi-Profile Support**: Automatically detects all Chrome profiles
- **No Temporary Profiles**: Uses your actual browsing session

### 📰 **Smart Content Sources**
- **Google News Headlines**: Fresh daily news topics
- **Google Trends**: Trending searches in your region  
- **Mixed Sources**: Combination of news and trends
- **Gemini AI Integration**: AI-generated unique search topics (optional)

### 🤖 **Human-like Behavior**
- **Microsoft Compliant**: 2-5 minute delays between searches
- **Random Patterns**: Varied timing and interactions
- **Progressive Delays**: Longer waits as session progresses (fatigue simulation)
- **Natural Flow**: Realistic search progression

### 🛡️ **Anti-Detection Features**
- **SQLite Database**: Prevents duplicate searches across sessions
- **Rotating User Agents**: Different browser signatures
- **Variable Timing**: Random delays and interactions
- **Logged Activity**: Comprehensive logging for monitoring

## 🚀 Quick Start

### Prerequisites
- Windows 10/11
- Google Chrome installed
- Python 3.7 or higher
- Chrome profiles set up (at least one)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bing-search-automation.git
   cd bing-search-automation
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python bing_automation.py
   ```

## 📖 Usage Guide

### Basic Usage

1. **Launch the application**
   ```bash
   python bing_automation.py
   ```

2. **Choose your options**:
   - **Search Source**: Google News (recommended), Trends, Mixed, or AI
   - **Automation Method**: Automated (opens tabs with delays) or Manual (shows list)
   - **Chrome Profile**: Select from your available profiles
   - **Search Count**: 5-15 searches per session

3. **Let it run**: The tool will open searches in new tabs with human-like delays

### Configuration

Edit `config.json` to customize:

```json
{
  "search_delay_min": 120,          // Minimum delay (seconds)
  "search_delay_max": 300,          // Maximum delay (seconds)
  "max_searches": 15,               // Max searches per session
  "bing_market": "en-IN",           // Your market region
  "gemini_api_key": "your-key",     // Optional: Gemini AI key
  "geo": "IN",                      // Country code
  "hl": "en-IN"                     // Language
}
```

## 🔧 Advanced Features

### Gemini AI Integration

For unique, AI-generated search topics:

1. **Get API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Add to config**: Put your API key in `config.json`
3. **Enable**: Select option 4 when choosing search sources

### Database Management

The tool maintains a SQLite database to track used searches:
- **View used terms**: Check `used_terms.db`
- **Reset database**: Use option C in the main menu
- **Manual cleanup**: Delete the database file to start fresh

### Logging

All activities are logged to `bing_search.log`:
- Search terms used
- Timing information
- Errors and warnings
- Profile selections

## 📊 Search Sources Explained

| Source | Description | Refresh Rate | Best For |
|--------|-------------|--------------|----------|
| **Google News** | Real-time news headlines | Every few hours | Fresh, relevant topics |
| **Google Trends** | Trending searches in India | Daily | Popular current topics |
| **Mixed Sources** | News + Trends combination | Dynamic | Balanced variety |
| **Gemini AI** | AI-generated topics | Unlimited | Unique, diverse topics |

## 🎯 Automation Methods

### Method A: Automated with Delays
- Opens Chrome tabs automatically
- 2-5 minute delays between searches
- You can use your computer normally
- Follows Microsoft's guidelines

### Method B: Manual List
- Shows you terms to search manually
- Opens Bing in your chosen profile
- Marks terms as used automatically
- Full manual control

## 🔒 Safety & Compliance

### Microsoft Guidelines Compliance
- ✅ **Proper Delays**: 2-5 minutes between searches
- ✅ **Human Patterns**: Variable timing and behavior
- ✅ **Single Sessions**: Limited searches per run
- ✅ **Real Content**: Actual news and trending topics

### Best Practices
1. **Don't Run 24/7**: Use realistic session times
2. **Vary Your Schedule**: Don't search at exact same times
3. **Use Real Profiles**: Always use logged-in Chrome profiles
4. **Monitor Logs**: Check for any errors or issues
5. **Respect Limits**: Stick to reasonable search counts

## 🐛 Troubleshooting

### Common Issues

**Chrome Profile Not Detected**
```bash
# Check if Chrome is installed
# Ensure you've used Chrome at least once
# Try running Chrome and creating a profile manually
```

**No Search Terms Available**
```bash
# Reset the database using option C
# Check your internet connection
# Verify Google News/Trends are accessible
```

**Permission Errors**
```bash
# Run as administrator if needed
# Check Chrome isn't running in admin mode
# Ensure proper file permissions
```

## 📦 Project Structure

```
bing-search-automation/
├── bing_automation.py          # Main application
├── config.json                 # Configuration file
├── requirements.txt            # Python dependencies
├── used_terms.db              # SQLite database (auto-created)
├── bing_search.log            # Log file (auto-created)
├── README.md                  # This file
└── legacy/                    # Previous versions
    ├── micro_enhanced.py      # Enhanced version with Selenium
    ├── micro_native.py        # Native Chrome integration
    └── micro_*.py             # Other experimental versions
```

## 🔧 Technical Details

### Dependencies
- `requests`: HTTP requests for news feeds
- `feedparser`: RSS feed parsing
- `beautifulsoup4`: HTML parsing
- `fake-useragent`: User agent rotation
- `sqlite3`: Database management (built-in)
- `google-generativeai`: Gemini AI integration (optional)

### System Requirements
- **OS**: Windows 10/11 (Chrome profile detection is Windows-specific)
- **Python**: 3.7 or higher
- **RAM**: 2GB minimum (4GB recommended)
- **Storage**: 100MB for application + logs
- **Network**: Internet connection for content sources

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This tool is created for educational purposes to demonstrate automation techniques. Users are responsible for:

- Complying with Microsoft's Terms of Service
- Following applicable laws and regulations
- Using the tool responsibly and ethically
- Not violating any platform policies

The authors are not responsible for any misuse or violations resulting from the use of this tool.

---

<div align="center">

**⭐ Star this repo if it helped you!**

Made with ❤️ for the automation community

</div>
- `config.json` - Configuration settings
- `requirements.txt` - Python dependencies
- `used_terms.db` - SQLite database tracking searched terms
- `bing_search.log` - Detailed execution logs

## Browser Support

1. **Chrome** (Default) - Uses undetected-chromedriver
2. **Edge** - Microsoft Edge browser
3. **Existing Window** - Attempts to use currently open browser

## Example Session

```
==========================================
BING SEARCH AUTOMATION - HUMAN-LIKE BEHAVIOR
==========================================

Browser Options:
1. Use existing browser window (if open)
2. Open new Chrome window
3. Open new Edge window
4. Exit

Enter your choice (1-4): 2

Operation Mode:
1. Interactive Mode - Visible browser with interactions (you cannot use device freely)
2. Background Mode - Minimized browser, basic searches only (you can use device freely)
3. Headless Mode - Completely hidden browser (you can use device freely)

Enter operation mode (1-3): 2

How many searches do you want to perform? (10-20, default: 15): 12

Setup Summary:
- Browser: Existing/Chrome
- Operation Mode: Background
- Device Usage: ✅ Can use device freely
- Number of searches: 12
- Delay between searches: 120-300 seconds
- Human-like behavior: Basic timing only

Proceed with these settings? (y/n): y

Setting up browser...
Background Mode: Browser will be minimized (you can use device freely)
Fetching search terms...
Starting 12 searches...
✅ You can now use your device freely - the browser will run in the background!

[1/12] Searching for: IPL 2025
Waiting 4m 12s before next search...
  3m 42s remaining...
  2m 45s remaining...
  ...

[2/12] Searching for: Digital India
Waiting 3m 56s before next search...
...
```

## Important Notes

⚠️ **Usage Guidelines**
- Keep searches to 10-20 per session
- Use realistic delays (2-5 minutes minimum)
- Don't run multiple instances simultaneously
- Respect Microsoft's terms of service

🔧 **Technical Requirements**
- Python 3.7+
- Chrome or Edge browser installed
- Stable internet connection
- Windows/Mac/Linux supported

## Troubleshooting

### Common Issues
1. **Browser Driver Issues**: Update undetected-chromedriver
2. **Network Timeouts**: Check internet connection
3. **Permission Errors**: Run with appropriate privileges

### Logs
Check `bing_search.log` for detailed error information and execution traces.
