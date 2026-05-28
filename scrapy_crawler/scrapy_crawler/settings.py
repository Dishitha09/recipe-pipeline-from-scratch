@'
import scrapy


class HebbarsSpider(scrapy.Spider):
    name = "hebbars"
    allowed_domains = ["hebbarskitchen.com"]
    start_urls = ["https://hebbarskitchen.com/"]

    def parse(self, response):
        yield {
            "url": response.url,
            "title": response.css("title::text").get(),
        }
'@ | Set-Content .\crawler\spiders\hebbars_spider.py