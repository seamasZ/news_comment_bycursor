from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()


class NewsRecord(Base):
    """新闻记录模型"""
    __tablename__ = "news_records"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text)
    comments = Column(JSON)  # 存储评论列表
    extra_metadata = Column(JSON)  # 存储额外元数据（不能用metadata，因为是SQLAlchemy保留字）
    created_at = Column(DateTime, default=datetime.now)


# 数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news_comments.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

