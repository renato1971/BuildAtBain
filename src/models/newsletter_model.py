from sqlalchemy import Column, Integer, Text, DateTime, func
from .connection import Base

class Newsletter(Base):
    __tablename__ = "newsletters"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(Text, nullable=False)
    final_html = Column(Text, nullable=True)
    created_on = Column(DateTime(timezone=True), server_default=func.now())
