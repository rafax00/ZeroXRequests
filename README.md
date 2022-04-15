# ZeroXRequests
Raw Requests for python - without client-side security checking

## Intro
With this lib, you can send invalid HTTP characters, invalid headers, duplicated headers, invalid methods, invalid pathnames, etc ...

Very useful for HTTP Request Smuggling vulnerabilities or others exploits that could not be exploited with HTTP libs for devs.

## How to use

git clone the repo into your project


**Method send_raw**:

*send_raw(raw_request, port, host, connection_timeout, use_ssl)*:

```
from ZeroXRequests import RawRequests

response = RawRequests.send_raw('GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n', 443, 'www.example.com', 7, True)

print(response)
```


**Method send** (Like python request but without security checking):

*send(url, method, headers, body, timeout)*:

```
from ZeroXRequests import RawRequests

response = send('https://www.example.com', 'GET', {'User-Agent':'ZeroXRequests'}, '', 10)

print(response)
```

