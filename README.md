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

It will also try to detect avec caching tools (varnish) or public caches (AWS
Cloudfront, Cloudflare, GCP, etc)

Findinds will are presented and detailed.

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

Exemple (may not be up to date):

```
$ ./hca.py https://github.com/Yoda-BZH/http-cache-analyzer

-------- HTTP Query --------------------------------------------------------------------
[--] Requesting url https://github.com/Yoda-BZH/http-cache-analyzer
[OK] HTTP Status code is 200

-------- HTTP Header list --------------------------------------------------------------
[--] date: Fri, 20 Nov 2020 12:00:57 GMT
[--] content-type: text/html; charset=utf-8
[--] server: GitHub.com
[--] status: 200 OK
[--] vary: X-PJAX, Accept-Encoding, Accept, X-Requested-With, Accept-Encoding
[--] etag: W/"e70be94f854983035a79391858fed15e"
[--] cache-control: max-age=0, private, must-revalidate
[--] strict-transport-security: max-age=31536000; includeSubdomains; preload
[--] x-frame-options: deny
[--] x-content-type-options: nosniff
[--] x-xss-protection: 1; mode=block
[--] referrer-policy: no-referrer-when-downgrade
[--] expect-ct: max-age=2592000, report-uri="https://api.github.com/_private/browser/errors"
[--] content-security-policy: default-src 'none'; base-uri 'self'; block-all-mixed-content; connect-src 'self' uploads.github.com www.githubstatus.com collector.githubapp.com api.github.com github-cloud.s3.amazonaws.com github-production-repository-file-5c1aeb.s3.amazonaws.com github-production-upload-manifest-file-7fdce7.s3.amazonaws.com github-production-user-asset-6210df.s3.amazonaws.com cdn.optimizely.com logx.optimizely.com/v1/events wss://alive.github.com; font-src github.githubassets.com; form-action 'self' github.com gist.github.com; frame-ancestors 'none'; frame-src render.githubusercontent.com; img-src 'self' data: github.githubassets.com identicons.github.com collector.githubapp.com github-cloud.s3.amazonaws.com *.githubusercontent.com; manifest-src 'self'; media-src 'none'; script-src github.githubassets.com; style-src 'unsafe-inline' github.githubassets.com; worker-src github.com/socket-worker.js gist.github.com/socket-worker.js
[--] Content-Encoding: gzip
[--] Set-Cookie: _gh_sess=SESSION_ID_TOKEN; Path=/; HttpOnly; Secure; SameSite=Lax, _octo=GH1.1.ID.ID; Path=/; Domain=github.com; Expires=Sat, 20 Nov 2021 12:00:56 GMT; Secure; SameSite=Lax, logged_in=no; Path=/; Domain=github.com; Expires=Sat, 20 Nov 2021 12:00:56 GMT; HttpOnly; Secure; SameSite=Lax
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
[OK] ETag is present, current value: W/"e70be94f854983035a79391858fed15e.

-------- Header Expires ----------------------------------------------------------------
[OK] Expires is absent, but Cache-Control is present, which is good.

-------- Header Last-Modified ----------------------------------------------------------
[--] Last-Modified is absent, it's okay

-------- Header Pragma -----------------------------------------------------------------
[OK] Pragma is absent or empty. It's good. Pragma is useless since HTTP/1.1.

-------- Final score -------------------------------------------------------------------
Final score: 99/100
```
