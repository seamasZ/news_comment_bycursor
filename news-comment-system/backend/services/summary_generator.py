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
        import logging
        logger = logging.getLogger(__name__)
        
        # 记录输入内容长度
        logger.info(f"[摘要生成] 开始生成摘要，标题长度: {len(title)}, 内容长度: {len(content)}")
        
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
7. **重要：只输出摘要内容，不要包含"摘要："、"总结："等前缀**
8. **必须去除所有导航链接、页面元素等无关内容，只保留新闻正文的核心信息**

**新闻标题：** {title if title else '未提供标题'}

**新闻正文：**
{content_preview}

**注意：** 如果正文中包含"首页"、"返回"、"分享"、"刷新"、"扫码"、"专题"、"直播"等导航元素，请忽略这些内容，只提取真正的新闻正文。

请生成摘要（格式：标题\\n\\n主要事件和关键信息）："""
        
        if self.use_openai and hasattr(self, 'client'):
            logger.info(f"[摘要生成] 使用OpenAI API，模型: {os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
            try:
                response = self.client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[
                        {"role": "system", "content": "你是一个专业的新闻摘要生成助手，擅长提取新闻的核心信息和关键要点。你的摘要必须准确反映新闻的主要内容，包括标题、主要事件、关键人物、时间、地点、数据等重要信息。只输出摘要内容，不要包含任何前缀或说明文字。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.4  # 进一步降低温度，使摘要更准确
                )
                summary = response.choices[0].message.content.strip()
                # 移除可能的引导性文字
                for prefix in ["摘要：", "摘要:", "总结：", "总结:", "以下是摘要：", "以下是摘要:"]:
                    if summary.startswith(prefix):
                        summary = summary[len(prefix):].strip()
                
                logger.info(f"[摘要生成] OpenAI API调用成功，摘要长度: {len(summary)}")
                logger.debug(f"[摘要生成] 生成的摘要: {summary[:100]}...")
                return summary
            except Exception as e:
                # 如果OpenAI失败，尝试备用方案
                logger.warning(f"[摘要生成] OpenAI API调用失败: {str(e)}，使用备用方法")
                return await self._generate_fallback(content, title)
        else:
            logger.warning(f"[摘要生成] OpenAI未配置或不可用，使用备用方法")
            if not self.api_key:
                logger.warning(f"[摘要生成] 未找到OPENAI_API_KEY环境变量")
            return await self._generate_fallback(content, title)
    
    async def _generate_fallback(self, content: str, title: str) -> str:
        """备用摘要生成方法（使用本地逻辑提取关键信息）"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[摘要生成-备用] 使用备用方法生成摘要")
        
        # 如果内容为空，返回默认摘要
        if not content or len(content.strip()) < 50:
            return title if title else "未能提取新闻内容"
        
        summary_parts = []
        
        # 1. 添加标题
        if title and title != "未找到标题":
            summary_parts.append(title)
        else:
            # 尝试从内容中提取标题（第一段或第一个长句子）
            first_sentence = content.split('。')[0].strip()
            if len(first_sentence) > 10 and len(first_sentence) < 100:
                summary_parts.append(first_sentence)
        
        # 2. 提取关键信息：时间、地点、人物、事件
        key_info = []
        
        # 提取时间（年份、日期等）
        time_patterns = [
            r'[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日',
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}',
            r'[0-9]{1,2}月[0-9]{1,2}日',
            r'[0-9]{4}年',
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, content[:2000])  # 只在前2000字符中查找
            if matches:
                key_info.append(f"时间：{matches[0]}")
                break
        
        # 提取地点（包含"在"、"于"等介词的地点信息）
        location_patterns = [
            r'在([^，。]{2,20}?)(?:举行|召开|举办|召开|发生)',
            r'于([^，。]{2,20}?)(?:举行|召开|举办)',
            r'([^，。]{2,15}?)(?:省|市|区|县|镇|村)',
        ]
        for pattern in location_patterns:
            matches = re.findall(pattern, content[:2000])
            if matches and len(matches[0]) > 2:
                key_info.append(f"地点：{matches[0]}")
                break
        
        # 提取人物（常见人物标识）
        person_patterns = [
            r'([^，。]{2,6}?)(?:出席|参加|表示|指出|强调|宣布)',
            r'([^，。]{2,6}?)(?:主席|总理|部长|主任|局长|市长)',
        ]
        for pattern in person_patterns:
            matches = re.findall(pattern, content[:2000])
            if matches and len(matches[0]) > 1:
                key_info.append(f"人物：{matches[0]}")
                break
        
        # 3. 提取主要内容（前几个完整句子，去除过短或过长的）
        sentences = [s.strip() for s in content.split('。') if s.strip()]
        main_sentences = []
        for sentence in sentences[:10]:  # 只取前10句
            # 过滤掉过短（可能是导航元素）或过长（可能是列表）的句子
            if 15 <= len(sentence) <= 200:
                # 排除常见的导航文本
                if not re.search(r'首页|返回|分享|刷新|扫码', sentence):
                    main_sentences.append(sentence)
                    if len(main_sentences) >= 3:  # 最多取3句
                        break
        
        # 4. 组合摘要
        if summary_parts:
            summary = summary_parts[0]  # 标题
        else:
            summary = "新闻摘要"
        
        if key_info:
            summary += "\n\n" + "\n".join(key_info[:3])  # 最多3条关键信息
        
        if main_sentences:
            summary += "\n\n主要内容：\n" + "。".join(main_sentences) + "。"
        else:
            # 如果没有提取到有效句子，使用前300字符
            preview = content[:300].strip()
            if preview:
                summary += "\n\n" + preview
                if len(content) > 300:
                    summary += "..."
        
        # 限制总长度
        if len(summary) > 500:
            summary = summary[:500] + "..."
        
        return summary if summary else "未能生成摘要"

