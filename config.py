from pydantic import BaseModel


class ServerConfig(BaseModel):
    # Server port.
    port: int

    # Minimum text length when getting from the database.
    short_length: int

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


class AnalyzerConfig(BaseModel):
    # The limit to show.
    limit: int

    # Font name to show.
    font_name: str

    # Minimum word length to count.
    min_word_length: int

    # Whether to count each word once per file.
    once_per_file: bool


class Config(BaseModel):
    spider: SpiderConfig
    server: ServerConfig
    analyzer: AnalyzerConfig


config: Config = Config.parse_file('config.json')
