import tornado.ioloop
import tornado.web
import tornado.template
from urllib.parse import urlparse  # I noticed you used urlparse, but you forgot to import it
import redis
import datetime
import string
import random
import time

# Admin Handler
class HashHandler(tornado.web.RedirectHandler):
    def initialize(self, cache, admin_token):
        self.cache = cache
        self.admin_token = admin_token
        self.life_of_hash = 60 * 60 * 6

    def get(self):
        if self.get_argument("admin_token") != self.admin_token:
            self.write({"error": 1, "errorMsg": "Are you the admin?"})
            return

        num = int(self.get_argument("num", 10))
        if num > 1000000000000:
            self.write({"error": 1, "errorMsg": "No more than 100 at a time, please."})
            return

        expiration = int(time.mktime(time.gmtime())) + self.life_of_hash
        tokens = []
        for i in range(num):
            token = self.generateRandomToken()
            self.cache.zadd("linkshim:hashes", {token: expiration})
            tokens.append(token)

        self.write({"error": 0, "tokens": tokens, "expiration": expiration})

    def generateRandomToken(self, size=25, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
        return "".join(random.choice(chars) for x in range(size))

# Handle requests to redirect
class RedirectHandler(tornado.web.RequestHandler):
    def initialize(self, cache, templates_dir):
        self.cache = cache
        self.loader = tornado.template.Loader(templates_dir)

    def get(self):
        href = self.get_argument("href")
        current_timestamp = int(time.mktime(time.gmtime()))
        today = datetime.date.today().strftime("%Y-%m-%d")
        self.cache.zincrby("linkshim:outbound:" + today, 1, href)
        domain = self.getDomain(href)
        ismember = self.cache.sismember("linkshim:watchlist", domain)
        if ismember:
            self.writeConfirmationMessage("watchlist.html", href)
            return

        h = str(self.get_argument("h"))
        expiration = self.cache.zscore("linkshim:hashes", h)
        if expiration == None or expiration < time.mktime(time.gmtime()):
            self.writeConfirmationMessage("warning.html", href)
            return

        self.smartRedirect(href)

    def writeConfirmationMessage(self, file, href):
        html = self.loader.load(file).generate(href=href)
        self.write(html)

    def smartRedirect(self, href):
        self.set_header("Refresh", "1")
        self.set_header("URL", href)
        if self.isIE():
            self.write("<a href='" + href + "' id='a'></a><script>document.getElementById('a').click();</script>")
        else:
            self.write("<script>document.location.replace('" + href + "');</script>")

    def isIE(self):
        if "User-Agent" not in self.request.headers:
            return False
        
        user_agent = self.request.headers["User-Agent"]
        if user_agent.find("MSIE") != -1:
            return True

        return False

    def getDomain(self, href):
        url_parts = urlparse(href)
        domain = '.'.join(url_parts.netloc.split('.')[-2:])
        index = domain.find(":")
        if index != -1:
            domain = domain[:index]

        return domain

if __name__ == "__main__":
    redis_cache = redis.StrictRedis(host='localhost', port=6379, db=0)
    admin_token = "JTCyFFO7OMWRxlnLCp6gp4fcJaLj2234tv3U0AabE7iQ"
    listen_on_port = 8888
    templates_dir = "templates"

    application = tornado.web.Application([
        (r"/r", RedirectHandler, dict(cache=redis_cache, templates_dir=templates_dir)),
        (r"/hash", HashHandler, dict(cache=redis_cache, admin_token=admin_token)),
    ])
    application.listen(listen_on_port)
    tornado.ioloop.IOLoop.instance().start()
