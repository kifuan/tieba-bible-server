# 贴吧圣经服务端

爬取贴吧的圣经并开启一个服务端，用来随机获取这些帖子的内容。

基于 `Web API` 的交互，你可以很方便的将其与你的其它 `App` 进行集成，如 `nonebot` 或 `koishi` 机器人。可以参考我分享的 [gist](https://gist.github.com/kifuan/1b440cd848c3677f3486904f8ad2e44b) 来创建一个 `nonebot` 机器人。

出于安全因素考虑，最好**不要将此项目的接口暴露到公网**。如果因为机器人需将此项目部署到服务器，请确保此项目所占用端口（默认为 `8003`）**已被防火墙拦截**。在本文结尾将为你演示如何绕过本项目的安全校验。

此项目附带一个 `analyze.py` 脚本，你可以运行它分析帖子的词频，下文会介绍这个脚本。

## 版本

理论上版本最低 `Python 3.9`，不过我使用的是 `Python 3.10`，不考虑向下兼容的问题。

**推荐创建**一个 `Python 3.10` 的**虚拟环境**来避免版本问题。


## 迁移

迁移仅针对之前已经 `clone` 了本仓库的用户，新用户可以跳过本节。

此项目不再存储每个帖子单独的信息，而是都存到数据库中。你可以运行 `migrate.py` 来**迁移数据**到数据库中，如果不需要迁移它会告诉你。

就算你压根没看到这个地方也无所谓，它只是可能会重新爬取你已经爬到的数据而已，并不会导致什么错误。

```bash
python migrate.py
```

## 使用

1. 安装 `requirements.txt` 中的依赖。

   ```bash
   pip install -r requirements.txt
   ```

2. 配置 `config.json` 中 `server` 下的内容之后开启服务端，每项解释如下。
   
   + `port`：默认为 `8003`，表示运行端口。
   + `host`：默认为 `127.0.0.1`，表示 `uvicorn` 运行的 `host`。
   + `allowed_hosts`：默认为 `['127.0.0.1', 'localhost']`，表示允许以哪些 `host` 访问，为了安全，推荐保留默认值只允许本地访问，参考[文档](https://fastapi.tiangolo.com/zh/advanced/middleware/#trustedhostmiddleware)进行配置。
   + `short_length`：默认为 `100`，表示短文本的最大长度。

   其实我也知道 `allowed_hosts` 通过修改 `HEADERS` 就能被轻松绕过，仅仅是聊胜于无罢了。

   配置完后运行 `server.py`。你可以使用 `uvicorn` 命令运行，也可以直接使用 `python server.py` 运行。

   ```bash
   # uvicorn server:app --port 8003
   python server.py
   ```

   关于如何使用 `uvicorn` 部署，请参考它的[文档](http://www.uvicorn.org/deployment/)了解。

   此外，你还可以用 `pm2` 等工具来部署，请参考它的[文档](https://pm2.keymetrics.io/docs/usage/quick-start/)进行了解。

3. 运行 `spider.py` 爬取数据。

   下面是 `config.json` 中 `spider` 下各配置项的说明：

   + `forum_name`：默认为 `复制粘贴`，表示吧名，推荐使用默认的复制粘贴吧。
   + `start_page`：默认为 `1`，表示从哪页开始爬取，包含这页。
   + `end_page`：默认为 `5`，表示从哪页结束，包含这页。
   + `max_post_pages`：默认为 `10`，表示每个帖子最多爬多少页，实际情况爬取可能比它少，不会比它多，因为这个帖可能没那么多回复。

   首次运行会产生 `aiotieba.toml`，请参考他们的[官方文档](https://v-8.top/tutorial/quickstart/#_4)来进行配置 `aiotieba.toml`。

   不过如果你只是需要爬取数据，这应该是**不需要你配置**的，你可以不管它。

4. 有下列 `API` 可供调用，所有 `API` 返回的都是 `application/json` 类型的数据。

   为了**简化返回数据**，此项目并没有按照传统的方式返回一个 `{success: boolean, message: string, data: any}`，而是以 `HTTP` 状态码的形式说明运行成功与否，这样方便你直接用 `response.json()` 来获取 `API` 的返回结果。

   + 统计指定关键字下的所有文本或短文本数量，不填 `keyword` 统计所有文本的数量，不填 `short` 默认为 `false` 即统计所有文本。

     ```http
     GET /count?keyword=关键字&short=true
     ```

     返回：`int`，表示文本数量，此 `API` 一般不会报错。

   + 从含指定关键字的所有文本或短文本中抽取一个，不填 `keyword` 从全部文本中抽取，不填 `short` 默认为 `false` 即从所有文本中获取。

     ```http
     GET /text?keyword=关键字&short=false
     ```

     返回：`str`，表示抽取到的文本或错误信息。如果没有匹配到指定的关键字，它会返回 `404` 状态码。


## 分析

其实 `requirements.txt` 中的 `jieba` 与 `matplotlib` 都是为了这个脚本依赖的，而我也不想再单独为了它单独写一个文件了。注意，它只会分析**中英文和数字**，忽略其它各种各样的语言。如果数据很多，运行效率较慢，因为 `jieba.cut` 需要时间，请耐心等待。

以下为 `config.json` 的 `analyzer` 配置下每个配置项的解释：

+ `limit`：默认为 `30`，表示显示排名前多少的词。
+ `font_name`：默认为 `Microsoft YaHei`，传给 `matplotlib` 的字体来避免中文乱码。如果你是 `MacOS` 请考虑设置为 `PingFang SC` 或其它中文字体。
+ `min_word_length`：默认为 `2`，表示最短词的长度。
+ `once_per_file`：默认为 `false`，表示是否每个词在一个文件只统计一次。

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

