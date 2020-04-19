from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime
from sqlalchemy import ForeignKey, Table, UnicodeText, Text, text
from sqlalchemy.orm import relationship, backref
from sqlalchemy_utils import ChoiceType

from .database import Base

from datetime import datetime
from enum import Enum
import bcrypt
import binascii
import os
import hashlib

class DonationType(Enum):
    one_time = "one_time"
    monthly = "monthly"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(256), nullable=False, index=True)
    admin = Column(Boolean())
    password = Column(String)
    created = Column(DateTime)
    password_reset = Column(String(128))
    password_reset_expires = Column(DateTime)
    stripe_customer = Column(String(256))

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode("utf-8"),
                bcrypt.gensalt()).decode("utf-8")

    def __init__(self, email, password):
        self.email = email
        self.admin = False
        self.created = datetime.now()
        self.set_password(password)

    def __repr__(self):
        return "<User {}>".format(self.email)

    # Flask.Login stuff
    # We don't use most of these features
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return self.email

class Donation(Base):
    __tablename__ = 'donations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", backref=backref("donations"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    project = relationship("Project", backref=backref("donations"))
    type = Column(ChoiceType(DonationType, impl=String()))
    amount = Column(Integer, nullable=False)
    created = Column(DateTime, nullable=False)
    updated = Column(DateTime, nullable=False)
    comment = Column(String(512))
    active = Column(Boolean)
    payments = Column(Integer)
    hidden = Column(Boolean, server_default='f', nullable=False)

    def __init__(self, user, type, amount, project=None, comment=None):
        self.user = user
        self.type = type
        self.amount = amount
        self.created = datetime.now()
        self.updated = datetime.now()
        self.emailed_about = False
        self.comment = comment
        self.active = True
        self.payments = 1
        if project:
            self.project_id = project.id

    def __repr__(self):
        return "<Donation {} from {}: ${} ({})>".format(
                self.id,
                self.user.email,
                "{:.2f}".format(self.amount / 100),
                self.type
            )

class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created = Column(DateTime, nullable=False)

    def __init__(self, name):
        self.name = name
        self.created = datetime.now()

    def __repr__(self):
        return "<Project {} {}>".format(self.id, self.name)

class Invoice(Base):
    __tablename__ = 'invoices'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False)
    external_id = Column(String(16), index=True)
    amount = Column(Integer, nullable=False)
    comment = Column(String(512), nullable=False)

    def __init__(self):
        self.external_id = binascii.hexlify(os.urandom(8)).decode()
        self.created = datetime.now()
