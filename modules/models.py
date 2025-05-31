from sqlalchemy import create_engine, Column, Integer, String, Table, MetaData
from sqlalchemy.orm import declarative_base
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    passwordHash = Column(String(200), nullable=False)
    
    def __repr__(self):
        return f"User {self.username}"
    
    
class Product(db.Model):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    URL = Column(String(500), nullable=False)
    name = Column(String(300), nullable=False)
    ogPrice = Column(Integer, nullable=False)
    currentPrice = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"Product {self.name}"
    
    
class UserProduct(db.Model):
    __tablename__ = "userProducts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    userID = Column(Integer, nullable=False)
    productID = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"UserProduct {self.id}"