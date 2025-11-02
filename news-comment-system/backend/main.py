from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
import os
from dotenv import load_dotenv

from services.news_extractor import NewsExtractor
from services.summary_generator import SummaryGenerator
from services.comment_generator import CommentGenerator
from database.models import init_db, get_db
from database.crud import create_record, get_all_records, get_record_by_id

load_dotenv()

app = FastAPI(title="新闻评论生成系统", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
init_db()

# 初始化服务
news_extractor = NewsExtractor()
summary_generator = SummaryGenerator()
comment_generator = CommentGenerator()


class NewsRequest(BaseModel):
    url: HttpUrl


class CommentConfig(BaseModel):
    count: int = 10
    styles: Dict[str, float] = {}  # {"formal": 0.3, "casual": 0.4, "humorous": 0.3}
    perspectives: Dict[str, float] = {}  # {"positive": 0.4, "neutral": 0.4, "negative": 0.2}


class GenerateRequest(BaseModel):
    url: HttpUrl
    comment_config: Optional[CommentConfig] = CommentConfig()


@app.get("/")
async def root():
    return {"message": "新闻评论生成系统API"}


@app.post("/api/extract")
async def extract_news(request: NewsRequest):
    """提取新闻内容"""
    try:
        content = await news_extractor.extract(request.url)
        return {
            "success": True,
            "data": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_comments(request: GenerateRequest):
    """生成新闻摘要和评论"""
    try:
        # 1. 提取新闻内容
        news_content = await news_extractor.extract(request.url)
        
        # 2. 生成摘要
        summary = await summary_generator.generate(news_content["text"], news_content["title"])
        
        # 3. 生成评论
        comments = await comment_generator.generate(
            news_content["text"],
            summary,
            request.comment_config.count,
            request.comment_config.styles,
            request.comment_config.perspectives
        )
        
        # 4. 保存到数据库
        record = create_record(
            url=str(request.url),
            title=news_content["title"],
            summary=summary,
            comments=comments,
            metadata={
                "comment_config": request.comment_config.dict(),
                "extracted_at": datetime.now().isoformat()
            }
        )
        
        return {
            "success": True,
            "data": {
                "id": record["id"],
                "title": news_content["title"],
                "summary": summary,
                "comments": comments,
                "url": str(request.url),
                "created_at": record["created_at"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history():
    """获取历史记录"""
    try:
        records = get_all_records()
        return {
            "success": True,
            "data": records
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{record_id}")
async def get_record(record_id: int):
    """获取单条历史记录"""
    try:
        record = get_record_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")
        return {
            "success": True,
            "data": record
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/{record_id}")
async def export_csv(record_id: int):
    """导出评论为CSV"""
    try:
        from services.csv_exporter import CSVExporter
        exporter = CSVExporter()
        csv_content = exporter.export_record(record_id)
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=comments_{record_id}.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    # 启用详细日志，方便调试
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",  # 日志级别：debug, info, warning, error
        access_log=True     # 显示访问日志
    )



