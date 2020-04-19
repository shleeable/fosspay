#!/usr/bin/env python3
from fosspay.objects import *
from fosspay.database import db
from fosspay.config import _cfg
from fosspay.email import send_thank_you, send_declined

from datetime import datetime, timedelta

import requests
import stripe
import subprocess

stripe.api_key = _cfg("stripe-secret")

print("Processing monthly donations at " + str(datetime.utcnow()))

donations = Donation.query \
    .filter(Donation.type == DonationType.monthly) \
    .filter(Donation.active) \
    .all()

limit = datetime.now() - timedelta(days=30)

for donation in donations:
    if donation.updated < limit:
        print("Charging {}".format(donation))
        user = donation.user
        customer = stripe.Customer.retrieve(user.stripe_customer)
        try:
            charge = stripe.Charge.create(
                amount=donation.amount,
                currency="usd",
                customer=user.stripe_customer,
                description="Donation to " + _cfg("your-name")
            )
        except stripe.error.CardError as e:
            donation.active = False
            db.commit()
            send_declined(user, donation.amount)
            print("Declined")
            continue

        send_thank_you(user, donation.amount, donation.type == DonationType.monthly)
        donation.updated = datetime.now()
        donation.payments += 1
        db.commit()
    else:
        print("Skipping {}".format(donation))

print("{} records processed.".format(len(donations)))

if _cfg("patreon-refresh-token"):
    print("Updating Patreon API token")

    r = requests.post('https://www.patreon.com/api/oauth2/token', params={
        'grant_type': 'refresh_token',
        'refresh_token': _cfg("patreon-refresh-token"),
        'client_id': _cfg("patreon-client-id"),
        'client_secret': _cfg("patreon-client-secret")
    })
    if r.status_code != 200:
        print("Failed to update Patreon API token")
        sys.exit(1)
    resp = r.json()
    with open("config.ini") as f:
        config = f.read()
    config = config.replace(_cfg("patreon-access-token"), resp["access_token"])
    config = config.replace(_cfg("patreon-refresh-token"), resp["refresh_token"])
    with open("config.ini", "w") as f:
        f.write(config)
    print("Refreshed Patreon API token")
