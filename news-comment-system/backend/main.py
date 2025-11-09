from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# 配置日志（同时输出到控制台和文件）
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'backend.log')

# 清除现有的handlers，避免重复
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别，记录更多信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(log_file, encoding='utf-8', mode='a'),  # 追加模式，不清空旧日志
    ],
    force=True  # 强制重新配置日志
)

# 确保日志立即刷新到文件
file_handler = None
for handler in logging.root.handlers:
    if isinstance(handler, logging.FileHandler):
        file_handler = handler
        break

if file_handler:
    file_handler.flush()

logger = logging.getLogger(__name__)
logger.info(f"日志文件位置: {log_file}")

from services.news_extractor import NewsExtractor
from services.summary_generator import SummaryGenerator
from services.comment_generator import CommentGenerator
from database.models import init_db, get_db
from database.crud import create_record, get_all_records, get_record_by_id

load_dotenv()

app = FastAPI(title="新闻评论生成系统", version="1.0.0")

# CORS配置（必须在日志中间件之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件（在CORS之后，确保能记录所有请求）
@app.middleware("http")
async def log_requests(request, call_next):
    import sys
    try:
        logger.info(f"[请求] {request.method} {request.url.path}")
        if request.url.path.startswith("/api/"):
            origin = request.headers.get('origin', 'N/A')
            logger.info(f"[请求] 来源: {origin}")
            # 强制刷新日志
            sys.stdout.flush()
        response = await call_next(request)
        logger.info(f"[响应] {request.method} {request.url.path} - 状态码: {response.status_code}")
        # 刷新所有日志处理器
        for handler in logging.root.handlers:
            handler.flush()
            if hasattr(handler, 'stream') and hasattr(handler.stream, 'flush'):
                handler.stream.flush()
        sys.stdout.flush()
        return response
    except Exception as e:
        logger.error(f"[中间件错误] {str(e)}", exc_info=True)
        raise

# 初始化数据库
init_db()

# 初始化服务
logger.info("正在初始化服务...")
news_extractor = NewsExtractor()
summary_generator = SummaryGenerator()
comment_generator = CommentGenerator()

# 记录API配置状态
import os
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
api_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

if api_key:
    logger.info(f"[配置] OpenAI API已配置，Base URL: {api_base}, Model: {api_model}")
    logger.info(f"[配置] API Key前10位: {api_key[:10]}...")
else:
    logger.warning("[配置] 未找到OPENAI_API_KEY，将使用备用方法生成摘要和评论")

logger.info("服务初始化完成")


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
    logger.info(f"[API] 收到提取请求，URL: {request.url}")
    try:
        content = await news_extractor.extract(request.url)
        logger.info(f"[API] 提取成功，标题: {content.get('title', 'N/A')[:50]}...，内容长度: {len(content.get('text', ''))}")
        return {
            "success": True,
            "data": content
        }
    except Exception as e:
        logger.error(f"[API] 提取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate")
async def generate_comments(request: GenerateRequest):
    """生成新闻摘要和评论"""
    logger.info(f"[API] 收到生成请求，URL: {request.url}，评论数量: {request.comment_config.count}")
    # 立即刷新日志到文件
    for handler in logging.root.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
    try:
        # 1. 提取新闻内容
        logger.info("[API] 步骤1: 开始提取新闻内容")
        news_content = await news_extractor.extract(request.url)
        logger.info(f"[API] 提取完成，标题: {news_content['title'][:50]}...，文本长度: {len(news_content['text'])}")
        
        # 2. 生成摘要
        logger.info("[API] 步骤2: 开始生成摘要")
        summary = await summary_generator.generate(news_content["text"], news_content["title"])
        logger.info(f"[API] 摘要生成完成，长度: {len(summary)}")
        logger.debug(f"[API] 摘要内容: {summary[:200]}...")
        
        # 3. 生成评论
        logger.info(f"[API] 步骤3: 开始生成 {request.comment_config.count} 条评论")
        comments = await comment_generator.generate(
            news_content["text"],
            summary,
            request.comment_config.count,
            request.comment_config.styles,
            request.comment_config.perspectives
        )
        logger.info(f"[API] 评论生成完成，共 {len(comments)} 条")
        
        # 4. 保存到数据库
        logger.info("[API] 步骤4: 保存到数据库")
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
        
        logger.info(f"[API] 生成请求完成，记录ID: {record['id']}")
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
        logger.error(f"[API] 生成请求失败: {str(e)}", exc_info=True)
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



