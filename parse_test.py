from urllib.parse import urlparse

proxy = "http://11de131690b3fdc7ba16__cr.in_12345:e3e7d1a8f82bd8e3@gw.dataimpulse.com:823"
u = urlparse(proxy)
print(f"Scheme: {u.scheme}")
print(f"Netloc: {u.netloc}")
print(f"Hostname: {u.hostname}")
print(f"Port: {u.port}")
print(f"Username: {u.username}")
print(f"Password: {u.password}")
