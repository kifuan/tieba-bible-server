# 贴吧帖子爬取和内容服务端

爬取贴吧的帖子并开启一个服务端，用来随机获取这些帖子的内容。

基于 `Web API` 的交互，你可以很方便的将其与你的其它 `App` 进行集成，如 `nonebot` 或 `koishi` 机器人。

## 版本

理论上版本最低 `Python 3.8`，不过我使用的是 `Python 3.10`，不考虑向下兼容的问题。

**推荐创建**一个 `Python 3.10` 的**虚拟环境**来避免版本问题。

## 使用

1. 安装 `requirements.txt` 中的依赖。

   ```bash
   pip install -r requirements.txt
   ```

2. 配置 `config.json` 中 `spider` 下的内容，并运行 `spider.py`。

   ```js
   "spider": {
       // 吧名，如复制粘贴吧。
       "forum_name": "复制粘贴",
       // 从哪页开始爬取。
       "start_page": 1,
       // 到哪页截至。
       "end_page": 5,
       // 每个帖子最多爬多少页。
       "max_post_pages": 20
   }
   ```

   配置完了之后运行，首次运行会产生 `aiotieba.toml`，如果出现爬取失败的情况，请参考他们的[官方文档](https://v-8.top/tutorial/quickstart/#_4)来进行配置 `aiotieba.toml`。不过如果你只是需要爬取数据，这应该是**不需要你配置**的，你可以不管它们。

3. 当 `spider.py` 运行结束后，配置 `config.json` 中 `server` 下的内容，并运行 `server.py`。你可以使用 `uvicorn` 命令运行，也可以直接使用 `python server.py` 运行。

   ```js
   "server": {
       // 端口，仅当使用 `python server.py` 时会使用此端口。
       "port": 8003,
       // 用户文本的最大长度。   
       "custom_text_max_size": 200,
       // 为了安全，推荐只允许本地 localhost 访问，参考 https://fastapi.tiangolo.com/advanced/middleware/?h=trusted#trustedhostmiddleware 进行高级配置。
       "allowed_hosts": [
            "localhost"
        ],
       // 对这些关键字的文本进行缓存，提升运行效率。
       "cached_keywords": [
           "原神",
           "压缩毛巾"
       ]
   }
   ```

4. 有下列 `API` 可供调用，参数 `keyword` 可以留空。

   ``` 
   # 获取指定关键字下的文本数量，不填 keyword 获取所有文本的数量。
   GET /count?keyword=
   
   # 从含指定关键字的文本中抽取一个，不填 keyword 从全部文本中抽取。
   GET /text?keyword=
   
   # 手动添加文本。
   POST /text
   {
       "texts": [
           "foo",
           "bar"
       ]
   }
   ```

## 协议

本项目使用 `MIT` 协议，不承担由于用户使用爬虫造成的任何问题。

为了防止被服务器 ban 掉，基本在所有请求前边都有 `asyncio.sleep(1)`。尽管这会让程序运行变慢，但还是不要把它去掉。
