from pydantic import BaseModel


class ServerConfig(BaseModel):
    # Server port.
    port: int

    # Max length for custom-upload texts.
    custom_text_max_length: int

    # Server host.
    host: str

    # Allowed hosts for security.
    allowed_hosts: list[str]


class SpiderConfig(BaseModel):
    # Max post pages it will get.
    max_post_pages: int

    # # The start page to fetch.
    start_page: int

    # The end page to fetch.
    end_page: int

    # The forum name to fetch.
    forum_name: str

    # Whether to merge the threads locally.
    merge_only: bool


class AnalyzerConfig(BaseModel):
    # The limit to show.
    limit: int

    # Font name to show.
    font_name: str

    # Minimal word length to count.
    min_word_length: int


class Config(BaseModel):
    spider: SpiderConfig
    server: ServerConfig
    analyzer: AnalyzerConfig


config: Config = Config.parse_file('config.json')
