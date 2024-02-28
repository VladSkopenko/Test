import json

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.item import Item, Field


class QuoteItem(Item):
    quote = Field()
    author = Field()
    tags = Field()


class AuthorItem(Item):
    fullname = Field()
    born_date = Field()
    born_location = Field()
    description = Field()


class DataPipeline:
    quotes = []
    authors = []

    def process_item(self, item, spider):
        if isinstance(item, AuthorItem):
            self.authors.append(dict(item))
        elif isinstance(item, QuoteItem):
            self.quotes.append(dict(item))
        return item

    def close_spider(self, spider):
        with open("quotes.json", "w", encoding="utf-8") as file:
            json.dump(self.quotes, file, ensure_ascii=False, indent=2)
        with open("authors.json", "w", encoding="utf-8") as file:
            json.dump(self.authors, file, ensure_ascii=False, indent=2)


class QuotesSpider(scrapy.Spider):
    name = "get_quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]
    custom_settings = {"ITEM_PIPELINES": {DataPipeline: 300}}

    def parse(self, response):
        for q in response.xpath("//div[@class='quote']"):
            quote = q.xpath("span[@class='text']/text()").get().strip()
            author = q.xpath("span/small[@class='author']/text()").get().strip()
            tags = q.xpath("div[@class='tags']/a/text()").extract()
            yield QuoteItem(quote=quote, author=author, tags=tags)
            yield response.follow(url=self.start_urls[0] + q.xpath("span/a/@href").get(), callback=self.parse_author)

        next_page = response.xpath("//li[@class='next']/a/@href").get()
        if next_page:
            yield scrapy.Request(url=self.start_urls[0] + next_page, callback=self.parse)

    def parse_author(self, response):
        content = response.xpath("//div[@class='author-details']")
        fullname = content.xpath("h3[@class='author-title']/text()").get().strip()
        born_date = content.xpath("p/span[@class='author-born-date']/text()").get().strip()
        born_location = content.xpath("p/span[@class='author-born-location']/text()").get().strip()
        description = content.xpath("div[@class='author-description']/text()").get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, born_location=born_location, description=description)


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(QuotesSpider)
    process.start()
