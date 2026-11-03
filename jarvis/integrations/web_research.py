"""Fact-first research: trusted APIs first, compact web sources second."""
from __future__ import annotations

from html import unescape
from urllib.parse import quote_plus, urlparse
from xml.etree import ElementTree
import re
import requests


class WebResearch:
    headers = {"User-Agent": "Mozilla/5.0 JARVIS/2.0"}

    @staticmethod
    def clean(value: str) -> str:
        return unescape(re.sub(r"<.*?>", "", value or "")).strip()

    def population_answer(self, query: str) -> str | None:
        countries = {"india": ("IND", "India"), "earth": ("WLD", "the world"), "world": ("WLD", "the world"), "usa": ("USA", "the United States"), "united states": ("USA", "the United States"), "china": ("CHN", "China")}
        lowered = query.lower()
        regions = {"africa": "Africa", "asia": "Asia", "europe": "Europe", "oceania": "Oceania", "north america": "Americas", "south america": "Americas"}
        region = next((name for keyword, name in regions.items() if keyword in lowered), None)
        if "population" in lowered and region:
            try:
                # REST Countries returns structured, current country records; sum them instead of scraping search pages.
                data = requests.get(f"https://restcountries.com/v3.1/region/{quote_plus(region)}?fields=population", headers=self.headers, timeout=12).json()
                total = sum(int(country.get("population", 0)) for country in data if isinstance(country, dict))
                if total > 0:
                    return f"{region} has an estimated population of about {total / 1_000_000_000:.3f} billion people ({total:,} people).\n\nSource: REST Countries regional data — https://restcountries.com/"
            except Exception:
                pass
            regional_estimates = {
                "Africa": (1.515, "2024"), "Asia": (4.807, "2024"), "Europe": (.745, "2024"),
                "Americas": (1.045, "2024"), "Oceania": (.046, "2024"),
            }
            estimate, year = regional_estimates[region]
            return f"{region} has an estimated population of about {estimate:.3f} billion people ({year} estimate).\n\nSource: United Nations Population Division — https://population.un.org/wpp/"
        matched = next(((code, name) for keyword, (code, name) in countries.items() if keyword in lowered), None)
        if "population" not in lowered or not matched:
            return None
        code, name = matched
        try:
            url = f"https://api.worldbank.org/v2/country/{code}/indicator/SP.POP.TOTL?format=json&per_page=8"
            data = requests.get(url, headers=self.headers, timeout=10).json()[1]
            latest = next(item for item in data if item.get("value") is not None)
            value, year = int(latest["value"]), latest["date"]
            readable = f"{value / 1_000_000_000:.3f} billion" if value >= 1_000_000_000 else f"{value / 1_000_000:.1f} million"
            return f"{name.title()}'s latest World Bank population estimate is {readable} ({value:,} people, {year}).\n\nSource: World Bank Data — https://data.worldbank.org/indicator/SP.POP.TOTL"
        except Exception:
            return None

    def wiki_answer(self, query: str) -> str | None:
        try:
            search = requests.get("https://en.wikipedia.org/w/api.php", params={"action": "query", "list": "search", "srsearch": query, "srlimit": 1, "format": "json"}, headers=self.headers, timeout=10).json()
            hits = search.get("query", {}).get("search", [])
            if not hits:
                return None
            title = hits[0]["title"]
            summary = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote_plus(title)}", headers=self.headers, timeout=10).json()
            extract = summary.get("extract", "").strip()
            page = summary.get("content_urls", {}).get("desktop", {}).get("page", "")
            return f"{extract}\n\nSource: Wikipedia — {page}" if extract else None
        except Exception:
            return None

    def instant_answer(self, query: str) -> str | None:
        """Use DuckDuckGo's structured instant-answer endpoint; never render raw result pages."""
        try:
            data = requests.get("https://api.duckduckgo.com/", params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}, headers=self.headers, timeout=10).json()
            text, url = data.get("AbstractText", "").strip(), data.get("AbstractURL", "")
            if text and url:
                return f"{text}\n\nSource: {data.get('AbstractSource', 'DuckDuckGo')} — {url}"
        except Exception:
            pass
        return None

    def search(self, query: str, limit: int = 3) -> str:
        return self.population_answer(query) or self.instant_answer(query) or self.wiki_answer(query) or f"I could not find a reliable, readable source for '{query}' right now."
