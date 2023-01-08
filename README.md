# 贴吧圣经服务端

爬取贴吧的圣经并开启一个服务端，用来随机获取这些帖子的内容。

基于 `Web API` 的交互，你可以很方便的将其与你的其它 `App` 进行集成，如 `nonebot` 或 `koishi` 机器人。可以参考我分享的 [gist](https://gist.github.com/kifuan/1b440cd848c3677f3486904f8ad2e44b) 来创建一个 `nonebot` 机器人。

出于安全因素考虑，最好**不要将此项目的接口暴露到公网**。如果因为机器人需将此项目部署到服务器，请确保此项目所占用端口（默认为 `8003`）**已被防火墙拦截**。在本文结尾将为你演示如何绕过本项目的安全校验。

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
       // 吧名，推荐复制粘贴吧。
       "forum_name": "复制粘贴",
       // 开始爬取页，包含这页。
       "start_page": 1,
       // 结束爬取页，包含这页。
       "end_page": 5,
       // 每个帖子最多爬多少页，实际情况爬取可能比它少，不会比它多，因为这个帖可能没那么多回复。
       "max_post_pages": 10
   }
   ```

   配置完了之后运行，首次运行会产生 `aiotieba.toml`，如果出现爬取失败的情况，请参考他们的[官方文档](https://v-8.top/tutorial/quickstart/#_4)来进行配置 `aiotieba.toml`。不过如果你只是需要爬取数据，这应该是**不需要你配置**的，你可以不管它们。

3. 当 `spider.py` 运行结束后，配置 `config.json` 中 `server` 下的内容，每项解释如下。

   ```js
   "server": {
       // 运行端口。
       "port": 8003,
       // 用户上传文本的最大长度，仅在 POST 请求时校验使用，与爬取的数据无关。
       "custom_text_max_size": 200,
       // 为了安全，推荐只允许本地访问，参考 https://fastapi.tiangolo.com/zh/advanced/middleware/#trustedhostmiddleware 进行配置。
       "allowed_hosts": [
            "127.0.0.1",
            "localhost"
        ],
       // 对这些关键字的查询结果进行缓存，提升运行效率。
       "cached_keywords": [
           "原神",
           "压缩毛巾"
       ]
   }
   ```
   其实我也知道 `allowed_hosts` 通过修改 `HEADERS` 就能被轻松绕过，仅仅是聊胜于无罢了。

   配置完后运行 `server.py`。你可以使用 `uvicorn` 命令运行，也可以直接使用 `python server.py` 运行。

   ```bash
   # uvicorn server:app --port 8003
   python server.py
   ```

   关于如何使用 `uvicorn` 部署，请参考它的[文档](http://www.uvicorn.org/deployment/)了解。

   此外，你还可以用 `pm2` 等工具来部署，请参考它的[文档](https://pm2.keymetrics.io/docs/usage/quick-start/)进行了解。

4. 有下列 `API` 可供调用，所有 `API` 返回的都是 `application/json` 类型的数据。

   为了**简化返回数据**，我没有按照传统的方式返回一个 `{success: boolean, message: string, data: any}`，而是以 `HTTP` 状态码的形式说明运行成功与否，这样方便你直接用 `response.json()` 来获取 `API` 的返回结果。
   
   + 获取指定关键字下的文本数量，不填 `keyword` 获取所有文本的数量。
   
     ```http
     GET /count?keyword=
     ```
   
     返回：`int`，表示文本数量，此 `API` 一般不会报错。
   
   + 从含指定关键字的文本中抽取一个，不填 `keyword` 从全部文本中抽取。
   
     ```http
     GET /text?keyword=
     ```
   
     返回：`str`，表示抽取到的文本或错误信息。如果没有匹配到指定的关键字，它会返回 `404` 状态码。
   
   + 添加自定义文本。你可以传字符串或者数组，注意，如果**任意一个字符串**超过最大要求，本次请求的**所有数据**都将视为无效。
   
     ```http
     POST /text
     {
       "text": "foo"
     }
     
     POST /text
     {
       "text": [
         "foo",
         "bar"
       ]
     }
     ```
     
     返回：`str`，表示成功或错误信息。如果数据校验失败，返回 `400` 状态码。
     
   + 
## 安全

上文中提到，此项目并没有做太多的安全措施，以下代码就可以绕过 `TrustedHostMiddleware` 的限制：

```py
import requests

requests.get('http://example.com/text', headers={'HOST': 'localhost'})
```

因此，我才在本文开头说要仔细检查防火墙的设置是否正确，不要轻易暴露出去。当然，如果你实在是想给别人分享 `API` 也无所谓，毕竟那是你的自由。


## 协议

本项目使用 `MIT` 协议，不对用户使用爬虫造成的任何问题负责。

为了防止被服务器 ban 掉，基本在所有请求前边都有 `asyncio.sleep(1)`。尽管这会让程序运行变慢，但还是不要把它去掉。

