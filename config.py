from pydantic import BaseModel


class ServerConfig(BaseModel):
    # Server port.
    port: int

    # Max size for custom-upload texts.
    custom_text_max_size: int

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

    # Whether to reload the server after getting data.
    reload_server: bool


class Config(BaseModel):
    spider: SpiderConfig
    server: ServerConfig


config: Config = Config.parse_file('config.json')
