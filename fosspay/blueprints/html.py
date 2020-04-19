from flask import Blueprint, render_template, abort, request, redirect, session, url_for, send_file, Response
from flask_login import current_user, login_user, logout_user
from datetime import datetime, timedelta
from fosspay.objects import *
from fosspay.database import db
from fosspay.common import *
from fosspay.config import _cfg, load_config
from fosspay.email import send_thank_you, send_password_reset
from fosspay.email import send_new_donation, send_cancellation_notice
from fosspay.currency import currency

import os
import locale
import bcrypt
import hashlib
import stripe
import binascii
import requests

encoding = locale.getdefaultlocale()[1]
html = Blueprint('html', __name__, template_folder='../../templates')

@html.route("/")
def index():
    if User.query.count() == 0:
        load_config()
        return render_template("setup.html")
    projects = sorted(Project.query.all(), key=lambda p: p.name)
    avatar = "//www.gravatar.com/avatar/" + hashlib.md5(_cfg("your-email").encode("utf-8")).hexdigest()
    selected_project = request.args.get("project")
    if selected_project:
        try:
            selected_project = int(selected_project)
        except:
            selected_project = None
    active_recurring = (Donation.query
            .filter(Donation.type == DonationType.monthly)
            .filter(Donation.active == True)
            .filter(Donation.hidden == False))
    recurring_count = active_recurring.count()
    recurring_sum = sum([d.amount for d in active_recurring])

    access_token = _cfg("patreon-access-token")
    campaign = _cfg("patreon-campaign")
    if access_token and campaign:
        try:
            import patreon
            client = patreon.API(access_token)
            campaign = client.fetch_campaign()
            attrs = campaign.json_data["data"][0]["attributes"]
            patreon_count = attrs["patron_count"]
            patreon_sum = attrs["pledge_sum"]
        except:
            patreon_count = 0
            patreon_sum = 0
    else:
        patreon_count = 0
        patreon_sum = 0

    liberapay = _cfg("liberapay-campaign")
    if liberapay:
        lp = (requests
                .get("https://liberapay.com/{}/public.json".format(liberapay))
            ).json()
        lp_count = lp['npatrons']
        lp_sum = int(float(lp['receiving']['amount']) * 100)
        # Convert from weekly to monthly
        lp_sum = lp_sum * 52 // 12
    else:
        lp_count = 0
        lp_sum = 0

    github_token = _cfg("github-token")
    if github_token:
        query = """
        {
            viewer {
                login
                sponsorsListing {
                    tiers(first:100) {
                        nodes {
                            monthlyPriceInCents
                            adminInfo {
                                sponsorships(includePrivate:true) {
                                    totalCount
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        r = requests.post("https://api.github.com/graphql", json={
            "query": query
        }, headers={
            "Authorization": f"bearer {github_token}"
        })
        result = r.json()
        nodes = result["data"]["viewer"]["sponsorsListing"]["tiers"]["nodes"]
        cnt = lambda n: n["adminInfo"]["sponsorships"]["totalCount"]
        gh_count = sum(cnt(n) for n in nodes)
        gh_sum = sum(n["monthlyPriceInCents"] * cnt(n) for n in nodes)
        gh_user = result["data"]["viewer"]["login"]
    else:
        gh_count = 0
        gh_sum = 0
        gh_user = 0

    return render_template("index.html", projects=projects,
            avatar=avatar, selected_project=selected_project,
            recurring_count=recurring_count, recurring_sum=recurring_sum,
            patreon_count=patreon_count, patreon_sum=patreon_sum,
            lp_count=lp_count, lp_sum=lp_sum,
            gh_count=gh_count, gh_sum=gh_sum, gh_user=gh_user,
            currency=currency)

@html.route("/setup", methods=["POST"])
def setup():
    if not User.query.count() == 0:
        abort(400)
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return redirect("..") # TODO: Tell them what they did wrong (i.e. being stupid)
    user = User(email, password)
    user.admin = True
    db.add(user)
    db.commit()
    login_user(user)
    return redirect("admin?first-run=1")

@html.route("/admin")
@adminrequired
def admin():
    first = request.args.get("first-run") is not None
    projects = Project.query.all()
    unspecified = Donation.query.filter(Donation.project == None).all()
    donations = Donation.query.order_by(Donation.created.desc()).limit(50).all()
    return render_template("admin.html",
        first=first,
        projects=projects,
        donations=donations,
        currency=currency,
        one_times=lambda p: sum([d.amount for d in p.donations if d.type == DonationType.one_time]),
        recurring=lambda p: sum([d.amount for d in p.donations if d.type == DonationType.monthly and d.active]),
        recurring_ever=lambda p: sum([d.amount * d.payments for d in p.donations if d.type == DonationType.monthly]),
        unspecified_one_times=sum([d.amount for d in unspecified if d.type == DonationType.one_time]),
        unspecified_recurring=sum([d.amount for d in unspecified if d.type == DonationType.monthly and d.active]),
        unspecified_recurring_ever=sum([d.amount * d.payments for d in unspecified if d.type == DonationType.monthly]),
        total_one_time=sum([d.amount for d in Donation.query.filter(Donation.type == DonationType.one_time)]),
        total_recurring=sum([d.amount for d in Donation.query.filter(Donation.type == DonationType.monthly, Donation.active == True)]),
        total_recurring_ever=sum([d.amount * d.payments for d in Donation.query.filter(Donation.type == DonationType.monthly)]),
    )

@html.route("/create-project", methods=["POST"])
@adminrequired
def create_project():
    name = request.form.get("name")
    project = Project(name)
    db.add(project)
    db.commit()
    return redirect("admin")


@html.route("/delete-project", methods=["POST"])
@adminrequired
def delete_project():
    id = request.form.get("id")
    project = Project.query.get(id)
    db.delete(project)
    db.commit()
    return redirect("admin")


@html.route("/login", methods=["GET", "POST"])
def login():
    if current_user:
        if current_user.admin:
            return redirect("admin")
        return redirect("panel")
    if request.method == "GET":
        return render_template("login.html")
    email = request.form.get("email")
    password = request.form.get("password")
    if not email or not password:
        return render_template("login.html", errors=True)
    user = User.query.filter(User.email == email).first()
    if not user:
        return render_template("login.html", errors=True)
    if not bcrypt.hashpw(password.encode('UTF-8'), user.password.encode('UTF-8')) == user.password.encode('UTF-8'):
        return render_template("login.html", errors=True)
    login_user(user)
    if user.admin:
        return redirect("admin")
    return redirect("panel")

@html.route("/logout")
@loginrequired
def logout():
    logout_user()
    return redirect(_cfg("protocol") + "://" + _cfg("domain"))

@html.route("/donate", methods=["POST"])
@json_output
def donate():
    email = request.form.get("email")
    stripe_token = request.form.get("stripe_token")
    amount = request.form.get("amount")
    type = request.form.get("type")
    comment = request.form.get("comment")
    project_id = request.form.get("project")

    # validate and rejigger the form inputs
    if not email or not stripe_token or not amount or not type:
        return { "success": False, "reason": "Invalid request" }, 400
    try:
        if project_id is None or project_id == "null":
            project = None
        else:
            project_id = int(project_id)
            project = Project.query.filter(Project.id == project_id).first()

        if type == "once":
            type = DonationType.one_time
        else:
            type = DonationType.monthly

        amount = int(amount)
    except:
        return { "success": False, "reason": "Invalid request" }, 400

    new_account = False
    user = User.query.filter(User.email == email).first()
    if not user:
        new_account = True
        user = User(email, binascii.b2a_hex(os.urandom(20)).decode("utf-8"))
        user.password_reset = binascii.b2a_hex(os.urandom(20)).decode("utf-8")
        user.password_reset_expires = datetime.now() + timedelta(days=1)
        customer = stripe.Customer.create(email=user.email, card=stripe_token)
        user.stripe_customer = customer.id
        db.add(user)
    else:
        customer = stripe.Customer.retrieve(user.stripe_customer)
        new_source = customer.sources.create(source=stripe_token)
        customer.default_source = new_source.id
        customer.save()

    donation = Donation(user, type, amount, project, comment)
    db.add(donation)

    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency=_cfg("currency"),
            customer=user.stripe_customer,
            description="Donation to " + _cfg("your-name")
        )
    except stripe.error.CardError as e:
        db.rollback()
        db.close()
        return { "success": False, "reason": "Your card was declined." }

    db.commit()

    send_thank_you(user, amount, type == DonationType.monthly)
    send_new_donation(user, donation)

    if new_account:
        return { "success": True, "new_account": new_account, "password_reset": user.password_reset }
    else:
        return { "success": True, "new_account": new_account }

def issue_password_reset(email):
    user = User.query.filter(User.email == email).first()
    if not user:
        return render_template("reset.html", errors="No one with that email found.")
    user.password_reset = binascii.b2a_hex(os.urandom(20)).decode("utf-8")
    user.password_reset_expires = datetime.now() + timedelta(days=1)
    send_password_reset(user)
    db.commit()
    return render_template("reset.html", done=True)

@html.route("/password-reset", methods=['GET', 'POST'], defaults={'token': None})
@html.route("/password-reset/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if request.method == "GET" and not token:
        return render_template("reset.html")

    if request.method == "POST":
        token = request.form.get("token")
        email = request.form.get("email")

        if email:
            return issue_password_reset(email)

        if not token:
            return redirect("..")

    user = User.query.filter(User.password_reset == token).first()
    if not user:
        return render_template("reset.html", errors="This link has expired.")

    if request.method == 'GET':
        if user.password_reset_expires == None or user.password_reset_expires < datetime.now():
            return render_template("reset.html", errors="This link has expired.")
        if user.password_reset != token:
            redirect("..")
        return render_template("reset.html", token=token)
    else:
        if user.password_reset_expires == None or user.password_reset_expires < datetime.now():
            abort(401)
        if user.password_reset != token:
            abort(401)
        password = request.form.get('password')
        if not password:
            return render_template("reset.html", token=token, errors="You need to type a new password.")
        user.set_password(password)
        user.password_reset = None
        user.password_reset_expires = None
        db.commit()
        login_user(user)
        return redirect("../panel")

@html.route("/panel")
@loginrequired
def panel():
    return render_template("panel.html",
        one_times=lambda u: [d for d in u.donations if d.type == DonationType.one_time],
        recurring=lambda u: [d for d in u.donations if d.type == DonationType.monthly and d.active],
        currency=currency)

@html.route("/cancel/<id>")
@loginrequired
def cancel(id):
    donation = Donation.query.filter(Donation.id == id).first()
    if donation.user != current_user:
        abort(401)
    if donation.type != DonationType.monthly:
        abort(400)
    donation.active = False
    db.commit()
    send_cancellation_notice(current_user, donation)
    return redirect("../panel")

@html.route("/invoice/<id>")
def invoice(id):
    invoice = Invoice.query.filter(Invoice.external_id == id).first()
    if not invoice:
        abort(404)
    return render_template("invoice.html", invoice=invoice)
