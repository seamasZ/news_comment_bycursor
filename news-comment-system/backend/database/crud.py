from database.models import SessionLocal, NewsRecord
from datetime import datetime
from typing import List, Dict, Optional


def create_record(
    url: str,
    title: str,
    summary: str,
    comments: List[Dict],
    metadata: Optional[Dict] = None
) -> Dict:
    """创建新闻记录"""
    db = SessionLocal()
    try:
        record = NewsRecord(
            url=url,
            title=title,
            summary=summary,
            comments=comments,
            extra_metadata=metadata or {},
            created_at=datetime.now()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        
        return {
            "id": record.id,
            "url": record.url,
            "title": record.title,
            "summary": record.summary,
            "comments": record.comments,
            "metadata": record.extra_metadata,  # 返回时仍使用metadata名称保持API兼容
            "created_at": record.created_at.isoformat()
        }
    finally:
        db.close()


def get_all_records() -> List[Dict]:
    """获取所有记录"""
    db = SessionLocal()
    try:
        records = db.query(NewsRecord).order_by(NewsRecord.created_at.desc()).all()
        return [
            {
                "id": r.id,
                "url": r.url,
                "title": r.title,
                "summary": r.summary,
                "comments": r.comments,
                "metadata": r.extra_metadata,  # 返回时仍使用metadata名称保持API兼容
                "created_at": r.created_at.isoformat()
            }
            for r in records
        ]
    finally:
        db.close()


def get_record_by_id(record_id: int) -> Optional[Dict]:
    """根据ID获取记录"""
    db = SessionLocal()
    try:
        record = db.query(NewsRecord).filter(NewsRecord.id == record_id).first()
        if not record:
            return None
        
        return {
            "id": record.id,
            "url": record.url,
            "title": record.title,
            "summary": record.summary,
            "comments": record.comments,
            "metadata": record.extra_metadata,  # 返回时仍使用metadata名称保持API兼容
            "created_at": record.created_at.isoformat()
        }
    finally:
        db.close()

