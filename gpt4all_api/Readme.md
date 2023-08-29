# Install

    pip install -r requirements.txt

# Deploy

Edit the parameter app_spp.py:Num_TREADS depending on your available ressources.

    gunicorn -w 2 -b 127.0.0.1:4000 app_spp:app --timeout 120


# Reverse proxy

### Nginx

```/etc/nginx/site-available/legal-assistant
server {
    listen 80;

    server_name gpt.datascience.etalab.studio;

    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;

    location / {
        proxy_pass         http://127.0.0.1:4000/;
        proxy_redirect     off;
        proxy_buffering off;

        proxy_set_header   Host                 $host;
        proxy_set_header   X-Real-IP            $remote_addr;
        proxy_set_header   X-Forwarded-For      $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto    $scheme;
    }
}
```
