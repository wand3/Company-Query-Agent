## Company-Query-Agent 
A robust Python Agent script that scrapes company insights data
This  scrapes company information from LinkedIn About pages using Playwright for browser automation and BeautifulSoup for data extraction.

## Prerequisites
- Python 3.10+
- Git (for cloning repository)

## Setup Instructions
Edit scraper.action.login file to input your email and password for login

### Clone Repository
```bash
git clone https://github.com/wand3/Company-Query-Agent.git
cd Company-Query-Agent
python3 -m scraper.main
```

### Create Virtual Environment
bash
```
# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### Launch scraper
```bash
python3 -m scraper.main
```
