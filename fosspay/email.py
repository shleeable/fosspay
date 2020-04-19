import smtplib
import os
import html.parser
from email.mime.text import MIMEText
from email.utils import localtime, format_datetime
from werkzeug.utils import secure_filename
from flask import url_for, render_template

from fosspay.database import db
from fosspay.objects import User, DonationType
from fosspay.config import _cfg, _cfgi
from fosspay.currency import currency

def send_thank_you(user, amount, monthly):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.ehlo()
    smtp.starttls()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(render_template("emails/thank-you", 
                user = user,
                root = _cfg("protocol") + "://" + _cfg("domain"),
                your_name = _cfg("your-name"),
                amount = currency.amount("{:.2f}".format(amount / 100)),
                monthly = monthly,
                your_email = _cfg("your-email")
    ))
    message['Subject'] = "Thank you for your donation!"
    message['From'] = _cfg("smtp-from")
    message['To'] = user.email
    message['Date'] = format_datetime(localtime())
    smtp.sendmail(_cfg("smtp-from"), [ user.email ], message.as_string())
    smtp.quit()

def send_password_reset(user):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.ehlo()
    smtp.starttls()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(render_template("emails/reset-password",
                user = user,
                root = _cfg("protocol") + "://" + _cfg("domain"),
                your_name = _cfg("your-name"),
                your_email = _cfg("your-email")
    ))
    message['Subject'] = "Reset your donor password"
    message['From'] = _cfg("smtp-from")
    message['To'] = user.email
    message['Date'] = format_datetime(localtime())
    smtp.sendmail(_cfg("smtp-from"), [ user.email ], message.as_string())
    smtp.quit()

def send_declined(user, amount):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.ehlo()
    smtp.starttls()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(render_template("emails/declined",
                user = user,
                root = _cfg("protocol") + "://" + _cfg("domain"),
                your_name = _cfg("your-name"),
                amount = currency.amount("{:.2f}".format(amount / 100))
    ))
    message['Subject'] = "Your monthly donation was declined."
    message['From'] = _cfg("smtp-from")
    message['To'] = user.email
    message['Date'] = format_datetime(localtime())
    smtp.sendmail(_cfg("smtp-from"), [ user.email ], message.as_string())
    smtp.quit()

def send_new_donation(user, donation):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.ehlo()
    smtp.starttls()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(render_template("emails/new_donation-you", 
                user = user,
                root = _cfg("protocol") + "://" + _cfg("domain"),
                your_name = _cfg("your-name"),
                amount = currency.amount("{:.2f}".format(amount / 100)),
                "frequency": (" per month"
                    if donation.type == DonationType.monthly else ""),
                "comment": donation.comment or "",
    ))
    message['Subject'] = "New donation on ShleePay!"
    message['From'] = _cfg("smtp-from")
    message['To'] = f"{_cfg('your-name')} <{_cfg('your-email')}>"
    message['Date'] = format_datetime(localtime())
    smtp.sendmail(_cfg("smtp-from"), [ _cfg('your-email') ], message.as_string())
    smtp.quit()

def send_cancellation_notice(user, donation):
    if _cfg("smtp-host") == "":
        return
    smtp = smtplib.SMTP(_cfg("smtp-host"), _cfgi("smtp-port"))
    smtp.ehlo()
    smtp.starttls()
    smtp.login(_cfg("smtp-user"), _cfg("smtp-password"))
    message = MIMEText(render_template("emails/cancelled", 
                user = user,
                root = _cfg("protocol") + "://" + _cfg("domain"),
                your_name = _cfg("your-name"),
                amount = currency.amount("{:.2f}".format(amount / 100)),
    ))
    message['Subject'] = "A monthly donation on ShleePay has been cancelled"
    message['From'] = _cfg("smtp-from")
    message['To'] = f"{_cfg('your-name')} <{_cfg('your-email')}>"
    message['Date'] = format_datetime(localtime())
    smtp.sendmail(_cfg("smtp-from"), [ _cfg('your-email') ], message.as_string())
    smtp.quit()
