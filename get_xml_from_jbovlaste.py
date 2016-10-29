'''
<form method="post" action="/login.html">
    <input type="hidden" name="backto" value="http://jbovlaste.lojban.org/export/xml.html" />
    User: <input size="16" name="username" type="text" /> <br />
    Pass: <input size="16" name="password" type="password" /> <br />
    <input type="submit" value="Login" /> <br />
</form>
'''

from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from http.cookiejar import CookieJar

opener = build_opener(HTTPCookieProcessor(CookieJar()))

name, pwd = '', ''

post = {
    'username' : name,
    'password' : pwd
}

data = urlencode(post).encode('utf-8')

conn = opener.open('http://jbovlaste.lojban.org/export/xml-export.html?lang={}', data)
with open('out.html', 'w', encoding='utf-8') as f:
    f.write(conn.read().decode('utf-8'))

url = "http://jbovlaste.lojban.org/export/xml-export.html?lang={}".format("ja")
conn = opener.open(url)
