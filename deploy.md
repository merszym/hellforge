# Deploy

This is the documentation of deploying hellforge with nginx and uwsgi,
it follows pretty much this [tutorial](https://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)

### Prerequisites

- get a fresh server and root rights
    - `apt-get update`
    - install git `apt-get install git`
    - install uv system wide `curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin/" sh`
    - install uwsgi prerequisites `apt-get install build-essential python3.12-dev` (depends on your python version)
    - install pango (for weasyprint) `apt-get install -y libpangocairo-1.0-0`
- create the 'hellforge' user `adduser hellforge`
    - log in as 'hellforge' as well
    - set up with SSH keys and stuff
    - clone the git repo `git clone git@github.com:merszym/hellforge`
    - create the .env file and add the required ENV variable (see github)
    - check that the server runs `uv run manage.py runserver` --> this will also download the dependencies
- Let the domain point to the correct server (DNS entry)

### uwsgi

- install a system-wide uwsgi `apt-get install uwsgi`
- `apt-get install uwsgi-plugin-python3`
- create a "hellforge_uwsgi.ini" file in the project-dir (see below)

### nginx

- root: install nginx `apt-get install nginx && /etc/init.d/nginx start`
- root: make the hellforge user a member of www-data `usermod -a -G www-data hellforge`
- root: give nginx access to the files (for media and static files) `chown -R :www-data /home/hellforge/`
- create a `/etc/nginx/sites-available/hellforge.conf` file (see below)
- publish the site `sudo ln -s /etc/nginx/sites-available/hellforge.conf /etc/nginx/sites-enabled/`

### django

- copy the media and the database into the new folder
- collect static: `uv run manage.py collectstatic`


#### hellforge.conf

```
upstream django {
  server unix:///home/hellforge/hellforge/hellforge.sock; # for a file socket
}

# configuration of the server
server {
  # the port your site will be served on
  listen 80;
  # the domain name it will serve for
  # substitute your machine's IP address or FQDN
  server_name 87.106.152.166 hellforge.merlin-szymanski.de;
  charset utf-8;
  client_max_body_size 10M;
  # Django media
  location /media {
    alias /home/hellforge/hellforge/media;
    # your Django project's media files -amend as required
  }
  location /static {
    alias /home/hellforge/hellforge/static;
    # your Django project's static files- amend as required
  }
  # Finally, send all non-media requests to the Django server.
  location / {
    uwsgi_pass django;
    include /home/hellforge/hellforge/uwsgi_params;
    # the uwsgi_params file you installed
  }
}

```

#### hellforge_uwsgi.ini 

```
[uwsgi]

# Django-related settings
# the base directory (full path)

chdir = /home/hellforge/hellforge
virtualenv = /home/hellforge/hellforge/.venv

# Django's wsgi file
module = hellforge.wsgi
# process-related settings

# master
master = true

# maximum number of worker processes
processes = 10
# the socket (use the full path to be safe)
socket = /home/hellforge/hellforge/hellforge.sock

# with appropriate permissions - may be needed
chmod-socket = 666
plugins = python3

# clear environment on exit
vacuum = true
```

### Run uwsgi in emperor mode

- `sudo mkdir -p /etc/uwsgi/vassals`
- symlink from the default config directory to your config file `sudo ln -s /home/hellforge/hellforge/hellforge_uwsgi.ini /etc/uwsgi/vassals/`
- run the emperor `uwsgi --emperor /etc/uwsgi/vassals --uid www-data --gid www-data`

### Put the emperor into systemd

- create a systemd service file `/etc/systemd/system/emperor.uwsgi.service` (see below)
- create a "/etc/uwsgi/emperor.ini" file (see below)
- `systemctl enable emperor.uwsgi.service`
- `systemctl start emperor.uwsgi.service`

#### emperor.ini

```
[uwsgi]
emperor = /etc/uwsgi/vassals
uid = www-data
gid = www-data
```


#### systemd-file

```
[Unit]
Description=uWSGI Emperor
After=syslog.target

[Service]
ExecStart=/usr/bin/uwsgi --ini /etc/uwsgi/emperor.ini
RuntimeDirectory=uwsgi
Restart=always
KillSignal=SIGQUIT
Type=notify
StandardError=syslog
NotifyAccess=all

[Install]
WantedBy=multi-user.target
```

With that the page runs under http... so lets create https certificate.

### Lets Encrypt / Certbot

Make the webpage speak https with lets encrypt

- follow the instructions on the certbot website 
- install certbot `apt-get install libaugeas0`
- cd to home (root) `uv venv`
- `uv pip install certbot certbot-nginx`
- `sudo ln -s /root/.venv/bin/certbot /usr/bin/certbot`
- `sudo certbot --nginx`

That was it...