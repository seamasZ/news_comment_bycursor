from typing import List, Dict
import os
import random
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class CommentGenerator:
    """多样化评论生成器"""
    
    def __init__(self):
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
        
        # 默认风格和观点
        self.default_styles = {
            "formal": "正式、客观、严谨",
            "casual": "轻松、随意、口语化",
            "humorous": "幽默、风趣、调侃",
            "analytical": "分析性、深度思考",
            "emotional": "情感化、表达强烈感受"
        }
        
        self.default_perspectives = {
            "positive": "积极、支持、肯定",
            "neutral": "中性、客观、理性",
            "negative": "批评、质疑、担忧"
        }
    
    async def generate(
        self,
        content: str,
        summary: str,
        count: int = 10,
        styles: Dict[str, float] = None,
        perspectives: Dict[str, float] = None
    ) -> List[Dict[str, str]]:
        """生成多样化评论"""
        if styles is None:
            styles = {"formal": 0.3, "casual": 0.3, "humorous": 0.2, "analytical": 0.1, "emotional": 0.1}
        
        if perspectives is None:
            perspectives = {"positive": 0.4, "neutral": 0.4, "negative": 0.2}
        
        # 生成评论（保留更多内容，让模型获取完整信息）
        comments = []
        
        if self.use_openai:
            comments = await self._generate_with_openai(content, summary, count, styles, perspectives)
        else:
            comments = await self._generate_fallback(content, summary, count, styles, perspectives)
        
        return comments
    
    async def _generate_with_openai(
        self,
        content: str,
        summary: str,
        count: int,
        styles: Dict[str, float],
        perspectives: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """使用OpenAI生成评论"""
        # 根据比例分配风格和观点
        assignments = self._assign_style_perspective(count, styles, perspectives)
        
        # 确保使用新闻内容（如果内容太长，保留前6000字符以获得更多上下文）
        content_for_comment = content[:6000] if len(content) > 6000 else content
        
        comments = []
        for assignment in assignments:
            style_desc = self.default_styles.get(assignment["style"], assignment["style"])
            perspective_desc = self.default_perspectives.get(assignment["perspective"], assignment["perspective"])
            
            # 从摘要中提取标题（第一行通常是标题）
            title_line = summary.split('\n')[0].strip() if summary else '无标题'
            
            # 使用完整的新闻内容（确保有足够上下文）
            news_preview = content_for_comment[:4000]  # 保留更多内容以获得完整上下文
            
            # 构建强调必须引用具体内容的提示词
            prompt = f"""作为新闻评论员，你需要基于以下新闻的具体内容生成一条评论。

**严格规则（违反则评论无效）：**
1. **评论必须明确提及新闻中的具体信息**，至少包含以下之一：
   - 新闻中的具体事件或事实（不能泛泛而谈）
   - 新闻中提到的人物姓名或具体角色
   - 新闻中的具体数据、数字、时间、地点等信息
   - 新闻中的具体观点、说法或引述
2. **严禁生成以下类型的通用评论**（这些评论不针对具体内容，适用于任何新闻）：
   - "这件事值得关注"
   - "需要进一步观察"
   - "这个情况令人担忧"
   - "希望相关部门能够妥善处理"
   - "这种做法值得肯定"
   - 其他不提及新闻具体内容的泛泛评论
3. **评论示例（好的评论）：**
   - "根据报道，[具体人物]在[具体地点]发生的[具体事件]表明[具体观点]"
   - "[具体数据]这一数字反映了[具体分析]"
   - "新闻中提到[具体事实]，我认为[具体观点]"
4. 语言风格：{style_desc}
5. 观点倾向：{perspective_desc}
6. 评论长度：60-150字

**新闻内容：**

标题：{title_line}

摘要：
{summary}

正文：
{news_preview}

**重要提示：**
- 评论的第一句话或前两句话必须明确提及新闻中的具体信息（人物、事件、数据、时间、地点等）
- 不能使用"这件事"、"这个情况"、"这种做法"等模糊指代，必须明确说明是什么事件、什么情况、什么做法
- 评论必须让人能够清楚地看出是针对这篇新闻的，而不是通用的评论
- 示例：如果新闻提到"张三在北京发布了新政策"，评论应该说"张三在北京发布的新政策..."而不是"这个政策值得关注"

**任务：基于以上新闻的具体内容，生成一条评论。评论必须明确提及或引用新闻中的具体事件、人物、数据、时间、地点或观点。如果评论是通用性的、不包含新闻具体信息的，则评论完全无效。**"""
            
            try:
                if not self.use_openai or not hasattr(self, 'client'):
                    raise Exception("OpenAI client not available")
                
                response = self.client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                    messages=[
                        {
                            "role": "system", 
                            "content": "你是一名专业的新闻评论员。你的任务是**必须基于新闻的具体内容**生成评论。\n\n**绝对规则（违反则评论完全无效）：**\n1. 评论必须明确提及或引用新闻中的具体信息：人物姓名、具体事件、数据、时间、地点等\n2. 严禁生成通用性评论（如'这件事值得关注'、'需要进一步观察'、'这个情况令人担忧'、'这种做法值得肯定'等不针对具体内容的泛泛评论）\n3. 评论必须在第一句话或前两句话中就明确提及新闻中的具体事件、人物、数据、时间或地点\n4. 不能使用模糊指代（如'这件事'、'这个情况'），必须明确说明具体内容\n5. 如果评论不包含新闻的具体信息，则该评论完全无效\n\n你必须严格遵守这些规则，确保生成的评论明确针对新闻的具体内容。"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=350,
                    temperature=0.6  # 进一步降低温度，提高相关性
                )
                comment_text = response.choices[0].message.content.strip()
                
                # 移除可能的引导性文字
                if comment_text.startswith("评论：") or comment_text.startswith("评论:"):
                    comment_text = comment_text[3:].strip()
                if comment_text.startswith("我认为："):
                    comment_text = comment_text[4:].strip()
                if comment_text.startswith("笔者认为："):
                    comment_text = comment_text[5:].strip()
                
                # 验证评论是否包含新闻具体内容
                # 检查通用评论的常见开头（这些通常不相关）
                generic_starters = [
                    "这件事值得关注",
                    "需要进一步观察",
                    "这个情况令人担忧",
                    "这种做法值得肯定",
                    "希望相关部门",
                    "这个政策",
                    "这种情况",
                    "这种做法",
                    "这一事件"
                ]
                
                is_generic = False
                comment_start = comment_text[:20]  # 检查前20个字符
                for starter in generic_starters:
                    if starter in comment_start:
                        is_generic = True
                        break
                
                # 如果检测到可能是通用评论，尝试重新生成一次（最多重试1次）
                retry_count = 0
                max_retries = 1
                
                while is_generic and retry_count < max_retries:
                    retry_count += 1
                    print(f"检测到可能的通用评论，尝试重新生成 (第{retry_count}次)...")
                    
                    # 使用更强的提示词重新生成
                    retry_prompt = f"""{prompt}

**重要：你刚才生成的评论可能是通用评论。请重新生成，确保：**
- 评论的开头必须明确提及新闻中的具体人物姓名、具体事件、具体数据等
- 不能以"这件事"、"这个情况"、"这种做法"等模糊词开头
- 必须在评论中引用新闻的具体内容"""
                    
                    try:
                        retry_response = self.client.chat.completions.create(
                            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "你是一名专业的新闻评论员。你的任务是**必须基于新闻的具体内容**生成评论。\n\n**绝对规则（违反则评论完全无效）：**\n1. 评论必须明确提及或引用新闻中的具体信息：人物姓名、具体事件、数据、时间、地点等\n2. 严禁生成通用性评论（如'这件事值得关注'、'需要进一步观察'、'这个情况令人担忧'、'这种做法值得肯定'等不针对具体内容的泛泛评论）\n3. 评论必须在第一句话或前两句话中就明确提及新闻中的具体事件、人物、数据、时间或地点\n4. 不能使用模糊指代（如'这件事'、'这个情况'），必须明确说明具体内容\n5. 如果评论不包含新闻的具体信息，则该评论完全无效\n\n你必须严格遵守这些规则，确保生成的评论明确针对新闻的具体内容。"
                                },
                                {"role": "user", "content": retry_prompt}
                            ],
                            max_tokens=350,
                            temperature=0.5  # 进一步降低温度
                        )
                        comment_text = retry_response.choices[0].message.content.strip()
                        
                        # 再次检查
                        comment_start = comment_text[:20]
                        is_generic = False
                        for starter in generic_starters:
                            if starter in comment_start:
                                is_generic = True
                                break
                    except Exception as retry_e:
                        print(f"重试生成失败: {str(retry_e)}")
                        break
                
                comments.append({
                    "text": comment_text,
                    "style": assignment["style"],
                    "perspective": assignment["perspective"]
                })
            except Exception as e:
                # 如果单个评论生成失败，记录错误并跳过
                print(f"生成评论失败 (风格:{assignment['style']}, 观点:{assignment['perspective']}): {str(e)}")
                continue
        
        # 如果生成数量不足，使用备用方法补充
        if len(comments) < count:
            remaining = count - len(comments)
            fallback = await self._generate_fallback(content, summary, remaining, styles, perspectives)
            comments.extend(fallback)
        
        return comments[:count]
    
    async def _generate_fallback(
        self,
        content: str,
        summary: str,
        count: int,
        styles: Dict[str, float],
        perspectives: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """备用评论生成方法"""
        assignments = self._assign_style_perspective(count, styles, perspectives)
        comments = []
        
        # 简单的模板生成（作为备用）
        templates = {
            "positive": [
                "这是一个很好的进展，值得肯定。",
                "支持这种做法，期待更多积极的变化。",
                "这个新闻令人鼓舞，希望未来会更好。"
            ],
            "neutral": [
                "这个事件值得关注，需要进一步观察。",
                "客观来看，这个情况比较复杂，需要多角度分析。",
                "这个新闻反映了当前的一些趋势。"
            ],
            "negative": [
                "这个情况令人担忧，需要引起重视。",
                "这种做法存在一些问题，需要谨慎考虑。",
                "希望相关部门能够妥善处理这个问题。"
            ]
        }
        
        for assignment in assignments:
            perspective = assignment["perspective"]
            style = assignment["style"]
            
            template_list = templates.get(perspective, templates["neutral"])
            comment_text = random.choice(template_list)
            
            # 根据风格调整
            if style == "humorous":
                comment_text = f"😄 {comment_text}"
            elif style == "emotional":
                comment_text = f"💭 {comment_text}"
            
            comments.append({
                "text": comment_text,
                "style": style,
                "perspective": perspective
            })
        
        return comments
    
    def _assign_style_perspective(
        self,
        count: int,
        styles: Dict[str, float],
        perspectives: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """根据比例分配风格和观点"""
        assignments = []
        
        # 归一化比例
        style_total = sum(styles.values())
        perspective_total = sum(perspectives.values())
        
        normalized_styles = {k: v / style_total if style_total > 0 else 1.0 / len(styles) for k, v in styles.items()}
        normalized_perspectives = {k: v / perspective_total if perspective_total > 0 else 1.0 / len(perspectives) for k, v in perspectives.items()}
        
        # 计算每种风格和观点的数量
        style_list = []
        remaining_style = count
        for i, (style, ratio) in enumerate(normalized_styles.items()):
            if i == len(normalized_styles) - 1:
                # 最后一个分配剩余数量
                style_list.extend([style] * remaining_style)
            else:
                num = int(ratio * count)
                style_list.extend([style] * num)
                remaining_style -= num
        
        perspective_list = []
        remaining_perspective = count
        for i, (perspective, ratio) in enumerate(normalized_perspectives.items()):
            if i == len(normalized_perspectives) - 1:
                perspective_list.extend([perspective] * remaining_perspective)
            else:
                num = int(ratio * count)
                perspective_list.extend([perspective] * num)
                remaining_perspective -= num
        
        # 随机打乱
        random.shuffle(style_list)
        random.shuffle(perspective_list)
        
        # 组合生成
        for i in range(count):
            assignments.append({
                "style": style_list[i] if i < len(style_list) else list(normalized_styles.keys())[0],
                "perspective": perspective_list[i] if i < len(perspective_list) else list(normalized_perspectives.keys())[0]
            })
        
        return assignments

