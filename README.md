# http-cache-analyzer

Analyze HTTP cache headers, checks if it's public-cache-compliant (cloudfront,
azure cdn, fastly, akamai, etc) or private-cache compliant (browser cache).

Usage:
```
./hca.py www.exemple.com
```

```
./hca.py https://www.example.com/assets/app.js
```

