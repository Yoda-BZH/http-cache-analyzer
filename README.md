# http-cache-analyzer

Analyze HTTP cache headers, checks if it's public-cache-compliant (cloudfront,
azure cdn, fastly, akamai, etc) or private-cache compliant (browser cache).

Currenlty checked HTTP headers:
* Cache-Control
* Last-Modified
* Age
* Expires
* Pragma
* ETag
* Cookies

It will also try to detect any caching tools (varnish) or public caches (AWS
Cloudfront, Cloudflare, GCP, etc)

Findings are presented and detailed.

TODO: Provide advices on what ot enhance

A final score based on the results is provided. (Scoring rules may need some
tweaking)

Overall presentation is largely inspired by mysqltuner and testssl.sh.

Usage:
```
./hca.py www.exemple.com
```

```
./hca.py https://www.example.com/assets/app.js
```

```
$ ./hca.py --help
usage: hca.py [-h] [-v] [-q] [-A USER_AGENT] [-a] [-o OUT] [-4 | -6] url

positional arguments:
  url                   URL to check

options:
  -h, --help            show this help message and exit
  -v, --verbose         Set to verbose
  -q, --quiet           Set to quiet
  -A USER_AGENT, --user-agent USER_AGENT
                        User agent to use
  -a, --assets          Parse all assets too
  -o OUT, --out OUT     Store results in given file
  -4, --ipv4            Resolve in ipv4 only
  -6, --ipv6            Resolve in ipv6 only

```

Exemple (may not be up to date):

```
$ ./hca.py https://github.com/Yoda-BZH/http-cache-analyzer

-------- HTTP Query --------------------------------------------------------------------
[--] Requesting url https://github.com/Yoda-BZH/http-cache-analyzer
[OK] HTTP Status code is 200

-------- HTTP Header list --------------------------------------------------------------
[--] date: Sat, 12 Dec 2020 16:43:22 GMT
[--] content-type: text/html; charset=utf-8
[--] server: GitHub.com
[--] status: 200 OK
[--] vary: X-PJAX, Accept-Encoding, Accept, X-Requested-With, Accept-Encoding
[--] etag: W/"08b889732d2ef0166e3c0ffadee90cdf"
[--] cache-control: max-age=0, private, must-revalidate
[--] strict-transport-security: max-age=31536000; includeSubdomains; preload
[--] x-frame-options: deny
[--] x-content-type-options: nosniff
[--] x-xss-protection: 1; mode=block
[--] referrer-policy: no-referrer-when-downgrade
[--] expect-ct: max-age=2592000, report-uri="https://api.github.com/_private/browser/errors"
[--] content-security-policy: default-src 'none'; base-uri 'self'; block-all-mixed-content; connect-src 'self' uploads.github.com www.githubstatus.com collector.githubapp.com api.github.com github-cloud.s3.amazonaws.com github-production-repository-file-5c1aeb.s3.amazonaws.com github-production-upload-manifest-file-7fdce7.s3.amazonaws.com github-production-user-asset-6210df.s3.amazonaws.com cdn.optimizely.com logx.optimizely.com/v1/events wss://alive.github.com; font-src github.githubassets.com; form-action 'self' github.com gist.github.com; frame-ancestors 'none'; frame-src render.githubusercontent.com; img-src 'self' data: github.githubassets.com identicons.github.com collector.githubapp.com github-cloud.s3.amazonaws.com *.githubusercontent.com; manifest-src 'self'; media-src 'none'; script-src github.githubassets.com; style-src 'unsafe-inline' github.githubassets.com; worker-src github.com/socket-worker-5029ae85.js gist.github.com/socket-worker-5029ae85.js
[--] Content-Encoding: gzip
[--] Set-Cookie: _gh_sess=<value>; Path=/; HttpOnly; Secure; SameSite=Lax, _octo=<value>; Path=/; Domain=github.com; Expires=Sun, 12 Dec 2021 16:43:22 GMT; Secure; SameSite=Lax, logged_in=no; Path=/; Domain=github.com; Expires=Sun, 12 Dec 2021 16:43:22 GMT; HttpOnly; Secure; SameSite=Lax
[--] Accept-Ranges: bytes
[--] Transfer-Encoding: chunked
[--] X-GitHub-Request-Id: github-ID

-------- Cache systems -----------------------------------------------------------------
[--] No caching system found

-------- Header Age --------------------------------------------------------------------
[--] Age is absent.

-------- Header Cache-Control ----------------------------------------------------------
[OK] Cache-Control ok, current value: 'max-age=0, private, must-revalidate'
[!!] Cache-Control has must-revalidate, removing -1 points
[OK] Cache-Control has private, adding 5 points
[--] Cache-Control: token 'max-age' has value '0'.
[!!] Cache-Control has max-age value to 0 or lower, lowering the score by 5

-------- Header ETag -------------------------------------------------------------------
[OK] ETag is present, current value: W/"08b889732d2ef0166e3c0ffadee90cdf.

-------- Header Expires ----------------------------------------------------------------
[OK] Expires is absent, but Cache-Control is present, which is good.

-------- Header Last-Modified ----------------------------------------------------------
[--] Last-Modified is absent, it's okay

-------- Header Pragma -----------------------------------------------------------------
[OK] Pragma is absent or empty. It's good. Pragma is useless since HTTP/1.1.

-------- Cookie ------------------------------------------------------------------------
[!!] Cookies are being defined. This may deactivates caching capabilities: '_gh_sess=<value>; Path=/; HttpOnly; Secure; SameSite=Lax, _octo=<value>; Path=/; Domain=github.com; Expires=Sun, 12 Dec 2021 16:43:22 GMT; Secure; SameSite=Lax, logged_in=no; Path=/; Domain=github.com; Expires=Sun, 12 Dec 2021 16:43:22 GMT; HttpOnly; Secure; SameSite=Lax'

-------- Final score -------------------------------------------------------------------
Final score: 69/100

```
