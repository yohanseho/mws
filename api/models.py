from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class AccessToken(db.Model):
    __tablename__ = 'access_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)
    
    def is_expired(self):
        """Check if token is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        # For backward compatibility, check if token is older than 5 hours
        return datetime.utcnow() > (self.created_at + timedelta(hours=5))
    
    def __repr__(self):
        return f'<AccessToken {self.name}>'

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    token_id = db.Column(db.Integer, db.ForeignKey('access_tokens.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    token = db.relationship('AccessToken', backref='sessions')
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at