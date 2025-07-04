from bs4 import BeautifulSoup
import re
import json
import os
from pathlib import Path
import re
from scraper.actions.base import Base
from playwright.async_api import Page
import asyncio
import json
import random
import os
from pathlib import Path
from ..logger import setup_logger


class CompanyAboutScraper(Base):

    # logger = setup_logger("linkedn", "INFO")

    def __init__(self, page_content, source_url, logger):
        self.soup = BeautifulSoup(page_content, 'html.parser')
        self.source_url = source_url
        self.logger = logger
        self.data = {
            "source_company_name": "",
            "source_company_countries": "",
            "source_company_phone": "",
            "source_company_sector_or_activity": "",
            "source_company_business_description": "",
            "source_company_transaction": "No transactions found",
            "Source_company_url": source_url,
            "source_company_specialties": "",
            "source_founding_date": "",
            "source_company_size": "",
            "source_company_website": "",

        }

    def extract_company_name(self):
        """Extract company name from the page header"""
        header = self.soup.select_one('h1.org-top-card-summary__title')
        if header:
            self.data["source_company_name"] = header.get_text(strip=True)
            self.logger.info("Extracting company Name Successful")

    def extract_company_website(self):
        """Extract company website from the page overview"""
        try:
            header = self.soup.select_one('dt h3')
            if header:
                self.data["source_company_name"] = header.get_text(strip=True)
                self.logger.info("Extracting company Name Successful")
        except Exception as e:
            self.logger.info(f"Extracting company website failed: {e}")

    def extract_overview_section(self):
        """Extract data from the Overview section"""
        overview_section = self.soup.select_one('section.org-about-module__margin-bottom')
        if not overview_section:
            return

        # Extract description
        description = overview_section.select_one('p.break-words.white-space-pre-wrap')
        if description:
            desc_text = description.get_text(strip=True)
            # Limit to 50 words
            words = desc_text.split()[:50]
            self.data["source_company_business_description"] = ' '.join(words)

        # Extract details from definition list
        for dt in overview_section.select('dt'):
            key = dt.get_text(strip=True)
            dd = dt.find_next_sibling('dd')
            if not dd:
                continue

            value = dd.get_text(strip=True)

            if "Industry" in key:
                self.data["source_company_sector_or_activity"] = value
            elif "Website" in key:
                # Extract website URL
                link = dd.find('a')
                if link:
                    self.data["source_company_website"] = link.get_text(strip=True)
            elif "Phone" in key:
                # Extract phone number
                link = dd.find('a')
                if link:
                    self.data["source_company_phone"] = link.get_text(strip=True)
            elif "Company size" in key:
                self.data["source_company_size"] = value
            elif "Founded" in key:
                self.data["source_founding_date"] = value
            elif "Specialties" in key:
                self.data["source_company_specialties"] = value
            self.logger.info(self.data)

    def extract_locations_section(self):
        """Extract country from locations section"""
        locations_section = self.soup.select_one('h3:-soup-contains("Locations")')
        if not locations_section:
            return

        # Find primary location
        primary_location = locations_section.find_next(class_='org-location-card')
        if primary_location:
            address = primary_location.select_one('p.t-14.t-black--light.t-normal')
            if address:
                address_text = address.get_text(strip=True)
                # Extract country from address (last part after comma)
                country = address_text.split(',')[-1].strip()
                # Clean country code (e.g., "MZ" -> "Mozambique")
                self.data["source_company_countries"] = country

    # def map_country_code(self, code):
    #     """Map country codes to full country names"""
    #     country_map = {
    #         "US": "United States", "UK": "United Kingdom", "CA": "Canada",
    #         "AU": "Australia", "DE": "Germany", "FR": "France",
    #         "IN": "India", "CN": "China", "JP": "Japan", "BR": "Brazil",
    #         "MZ": "Mozambique", "ZA": "South Africa", "NG": "Nigeria",
    #         "KE": "Kenya", "GH": "Ghana", "EG": "Egypt"
    #     }
    #     # Remove any numbers or special characters
    #     clean_code = re.sub(r'[^A-Za-z]', '', code)
    #     return country_map.get(clean_code.upper(), code)

    def extract_transactions(self):
        """Placeholder for transaction extraction (not in provided HTML)"""
        # This would need custom implementation based on actual page structure
        # For now, we'll leave the default "No transactions found"
        pass

    def scrape(self):
        """Execute all extraction methods"""
        self.extract_company_name()
        self.extract_overview_section()
        self.extract_locations_section()
        # self.extract_transactions()
        self.save_to_json()

        return self.data

    def save_to_json(self, filename=None):
        """Save extracted data to JSON file"""
        if not filename:
            # Generate filename from company name
            company_slug = re.sub(r'[^a-zA-Z0-9]+', '-', self.data["source_company_name"]).strip('-')
            # filename = f"{company_slug}_about.json"
            filename = f"companies_about.json"

        base_folder = Path(__name__).resolve().parent
        results_dir = base_folder / "scraper" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        # Now, define the full path to the file itself
        filepath = results_dir / filename
        with open(filepath, 'a', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        return str(filepath)

    async def execute(self):
        # Extract data
        company_data = self.scrape()
        self.logger.info(f'{company_data}')

        # Save to JSON
        # json_path = self.save_to_json()
        # self.logger.info(f"Company data saved to: {json_path}")
        self.logger.info(f"{company_data}")

        return company_data
