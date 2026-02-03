from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(String)
    owner_user_id = Column(String)
    scope = Column(Enum("user","group","company"))
    group_id = Column(String, nullable=True)
    chroma_collection = Column(String)

# User / Group Tabellen einfach
