from typing import Dict
import os
import httpx
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class SummaryGenerator:
    """新闻摘要生成器"""
    
    def __init__(self):
        # 优先使用OpenAI API，如果没有配置则使用其他大模型
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                self.use_openai = True
            except Exception:
                self.use_openai = False
        else:
            self.use_openai = False
        
        self.api_endpoint = os.getenv("LLM_API_ENDPOINT", "")
        self.api_key_alt = os.getenv("LLM_API_KEY", "")
    
    async def generate(self, content: str, title: str = "") -> str:
        """生成新闻摘要"""
        # 截取内容前4000字符（避免过长但保留更多信息）
        content_preview = content[:4000]
        
        prompt = f"""请仔细阅读以下新闻内容，生成简洁准确的摘要。

**摘要要求：**
1. 第一行必须是新闻标题（如果标题为空则写"未提供标题"）
2. 接下来总结主要事件和核心信息
3. 提取关键信息：人物、时间、地点、数据、重要观点等
4. 控制在200字以内
5. 使用简洁明了的语言
6. 确保摘要能够准确反映新闻的核心内容

**新闻标题：** {title if title else '未提供标题'}

**新闻正文：**
{content_preview}

请生成摘要（格式：标题\\n\\n主要事件和关键信息）："""
        
        if self.use_openai and hasattr(self, 'client'):
            try:
                response = self.client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[
                        {"role": "system", "content": "你是一个专业的新闻摘要生成助手，擅长提取新闻的核心信息和关键要点。你的摘要必须准确反映新闻的主要内容，包括标题、主要事件、关键人物、时间、地点、数据等重要信息。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.4  # 进一步降低温度，使摘要更准确
                )
                summary = response.choices[0].message.content.strip()
                return summary
            except Exception as e:
                # 如果OpenAI失败，尝试备用方案
                return await self._generate_fallback(content, title)
        else:
            return await self._generate_fallback(content, title)
    
    async def _generate_fallback(self, content: str, title: str) -> str:
        """备用摘要生成方法（使用本地逻辑或其他API）"""
        # 简单提取：取前几段作为摘要
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()][:3]
        summary_parts = [title] if title else []
        summary_parts.extend(paragraphs[:2])
        summary = '\n'.join(summary_parts)
        
        # 如果内容过长，截取
        if len(summary) > 300:
            summary = summary[:300] + "..."
        
        return summary or "未能生成摘要"

