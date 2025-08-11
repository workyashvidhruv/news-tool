# News Tool - Daily Tech & Startup News Aggregator

A smart news aggregation tool that scrapes, ranks, and presents the most important tech and startup news from India and around the world.

## Features

- **Smart Scraping**: Automatically fetches news from 20+ sources
- **AI Ranking**: Articles ranked by impact, virality, and controversy scores
- **Beautiful Website**: Modern, responsive design with dark mode
- **Daily Updates**: Fresh content every day at 7 AM
- **Multiple Sources**: TechCrunch, Wired, Reddit, Indian startups, and more

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run daily pipeline
python3 main.py --mode daily

# Generate website only
python3 main.py --mode website-only

# Open website
open index.html
```

### Automation Setup
```bash
# Set up daily automation at 7 AM
./setup_automation.sh
```

## Deployment Options

### 1. GitHub Pages (Recommended - Free)
```bash
# Initialize git and push to GitHub
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/news-tool.git
git push -u origin main

# Enable GitHub Pages in repository settings
# Set source to main branch
# Your site will be available at: https://YOUR_USERNAME.github.io/news-tool/
```

### 2. Netlify (Free Tier)
- Drag and drop the `News tool` folder to [netlify.com](https://netlify.com)
- Get instant public URL

### 3. Vercel (Free Tier)
- Install Vercel CLI: `npm i -g vercel`
- Run `vercel` in the project directory
- Get instant public URL

### 4. Local Network Sharing
```bash
# Start a simple HTTP server
python3 -m http.server 8000

# Share your local IP address
# Others on your network can access: http://YOUR_IP:8000
```

## Configuration

Edit `config.py` to:
- Add/remove news sources
- Adjust scraping delays
- Modify ranking weights
- Customize website settings

## File Structure

```
News tool/
├── main.py              # Main pipeline
├── scrapers.py          # News source scrapers
├── processor.py         # Article processing & ranking
├── data_manager.py      # Data storage & management
├── website_generator.py # HTML generation
├── config.py            # Configuration
├── static/              # CSS & assets
├── templates/           # HTML templates
├── data/                # News data storage
└── *.html               # Generated website files
```

## Troubleshooting

- **SSL Issues**: The tool handles LibreSSL compatibility automatically
- **Rate Limiting**: Increased delays and retry logic built-in
- **Failed Sources**: Some sources may be temporarily unavailable

## License

MIT License - Feel free to use and modify! 