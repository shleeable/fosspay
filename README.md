# shleepay-fosspay
*fosspay fork*

Donation collection for FOSS groups and individuals.

* Supports one-time and monthly donations
* Process cards with Stripe
* Flexible and customizable

## Changes from fosspay
*patches and inspiration taken from many many other forks*

* Added Docker Support
* Added additional currencies - Example: aud
* Added Fee description - (from unascribed fork)

## Notes

* you must serve your site with https for Stripe to work.

## Before you start

You will need a number of things set up before you start:

1. An approved [Stripe](https://stripe.com/) account
1. A mail server
1. A domain name and an SSL certificate
1. A web server to host fosspay on

## Installation

* Install Docker, and Docker-Compose.

* Clone the git repository on the server that you want to host shleepay on:
```
    git clone git://github.com/shleeable/shleepay.git
    cd shleepay
```

* Create and edit the configuration file:
```
    cp config.ini.docker config.ini
    vim config.ini
```

* Build and start shleepay using docker-compose
```
    docker-compose build
    docker-compose up -d
```

* Setup Crontab
```
    * * * * * cd /path-to-your-project && docker-compose run --rm fosspay python3 /usr/src/app/cronjob.py >> /dev/null 2>&1 && docker-compose restart fosspay
```

* Setup nginx reverse proxy with HTTPS TLS - see `contrib/nginx.conf`
* Setup DNS.

* Log into https://donate.domain.com, and you will receive further instructions.
