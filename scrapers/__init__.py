"""커뮤니티 스크래퍼 패키지"""
from scrapers.dcinside import DcInsideScraper
from scrapers.ppomppu import PpomppuScraper
from scrapers.blind import BlindScraper

__all__ = ["DcInsideScraper", "PpomppuScraper", "BlindScraper"]
