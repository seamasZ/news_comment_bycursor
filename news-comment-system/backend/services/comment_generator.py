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
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # 尝试使用OpenAI库，如果失败则使用httpx直接调用
        self.use_openai_lib = False
        self.use_httpx = False
        
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                # 测试调用
                self.use_openai_lib = True
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[评论生成] OpenAI库初始化失败: {str(e)}，将使用httpx直接调用")
                self.use_openai_lib = False
        
        # 如果OpenAI库不可用，使用httpx
        if self.api_key and not self.use_openai_lib:
            try:
                import httpx
                self.httpx_client = httpx
                self.use_httpx = True
            except ImportError:
                self.use_httpx = False
        
        self.use_openai = self.use_openai_lib or self.use_httpx
        
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[评论生成] 开始生成 {count} 条评论，内容长度: {len(content)}, 摘要长度: {len(summary)}")
        
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
            
            # 从新闻内容中提取关键实体，用于在提示词中强调
            import re
            from collections import Counter
            
            # 提取关键名词
            keywords = re.findall(r'[\u4e00-\u9fff]{2,6}', content_for_comment[:2000])
            keyword_freq = Counter(keywords)
            top_keywords = [word for word, freq in keyword_freq.most_common(10) if len(word) >= 2][:5]
            
            # 提取数字、时间、地点
            numbers = re.findall(r'[0-9]+(?:\.?[0-9]+)?(?:万|亿|%|人|元|次|项)?', content_for_comment[:2000])[:3]
            times = re.findall(r'[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日', content_for_comment[:2000])[:2]
            locations = re.findall(r'([^，。]{2,8}?)(?:省|市|区|县)', content_for_comment[:2000])[:3]
            
            key_entities_str = ""
            if top_keywords:
                key_entities_str += f"关键词语：{', '.join(top_keywords[:3])}\n"
            if numbers:
                key_entities_str += f"关键数据：{', '.join(numbers[:2])}\n"
            if times:
                key_entities_str += f"时间信息：{', '.join(times[:2])}\n"
            if locations:
                key_entities_str += f"地点信息：{', '.join(locations[:2])}\n"
            
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
   - "这个新闻反映了当前的一些趋势"
   - "这个事件值得关注，需要进一步观察"
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
{content_for_comment[:4000]}

{key_entities_str if key_entities_str else ""}
**重要提示：**
- 评论的第一句话或前两句话必须明确提及新闻中的具体信息（人物、事件、数据、时间、地点等）
- 不能使用"这件事"、"这个情况"、"这种做法"等模糊指代，必须明确说明是什么事件、什么情况、什么做法
- 评论必须让人能够清楚地看出是针对这篇新闻的，而不是通用的评论
- 示例：如果新闻提到"第十五届全运会在广东举行"，评论应该说"第十五届全运会在广东的举办..."而不是"这个活动值得关注"
- 如果新闻提到具体人物，评论中必须提及该人物的姓名或具体角色
- 如果新闻提到具体数据，评论中应该引用该数据

**任务：基于以上新闻的具体内容，生成一条评论。评论必须明确提及或引用新闻中的具体事件、人物、数据、时间、地点或观点。如果评论是通用性的、不包含新闻具体信息的，则评论完全无效。**"""
            
            try:
                if not self.use_openai:
                    raise Exception("API不可用")
                
                # 添加超时和重试机制
                import time
                max_retries = 2
                retry_count = 0
                comment_text = None
                
                while retry_count < max_retries:
                    try:
                        if self.use_openai_lib and hasattr(self, 'client'):
                            # 使用OpenAI库
                            response = self.client.chat.completions.create(
                                model=self.model,
                                messages=[
                                    {
                                        "role": "system", 
                                        "content": f"""你是一名专业的新闻评论员。你的任务是**必须基于新闻的具体内容**生成评论。

**绝对规则（违反则评论完全无效）：**
1. 评论必须明确提及或引用新闻中的具体信息：人物姓名、具体事件、数据、时间、地点等
2. 严禁生成通用性评论（如'这件事值得关注'、'需要进一步观察'、'这个情况令人担忧'、'这种做法值得肯定'、'这个新闻反映了当前的一些趋势'、'这个事件值得关注，需要进一步观察'等不针对具体内容的泛泛评论）
3. 评论必须在第一句话或前两句话中就明确提及新闻中的具体事件、人物、数据、时间或地点
4. 不能使用模糊指代（如'这件事'、'这个情况'、'这种做法'、'这个政策'、'这种情况'），必须明确说明具体内容
5. 如果评论不包含新闻的具体信息，则该评论完全无效
6. 评论必须让人能够清楚地看出是针对这篇特定新闻的，而不是可以适用于任何新闻的通用评论

**示例（好的评论）：**
- 如果新闻提到"第十五届全运会在广东举行"，评论应该说"第十五届全运会在广东的举办展现了..."而不是"这个活动值得关注"
- 如果新闻提到具体人物"张三"，评论应该说"张三在...中表示..."而不是"相关人士表示..."
- 如果新闻提到具体数据"1000人"，评论应该说"1000人这一数字反映了..."而不是"这个数字值得关注"

你必须严格遵守这些规则，确保生成的评论明确针对新闻的具体内容。"""
                                    },
                                    {"role": "user", "content": prompt}
                                ],
                                max_tokens=350,
                                temperature=0.5
                            )
                            comment_text = response.choices[0].message.content.strip()
                        elif self.use_httpx:
                            # 使用httpx直接调用API
                            import httpx
                            import json
                            
                            url = f"{self.base_url}/chat/completions"
                            headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                            payload = {
                                "model": self.model,
                                "messages": [
                                    {
                                        "role": "system",
                                        "content": f"""你是一名专业的新闻评论员。你的任务是**必须基于新闻的具体内容**生成评论。

**绝对规则（违反则评论完全无效）：**
1. 评论必须明确提及或引用新闻中的具体信息：人物姓名、具体事件、数据、时间、地点等
2. 严禁生成通用性评论（如'这件事值得关注'、'需要进一步观察'、'这个情况令人担忧'、'这种做法值得肯定'、'这个新闻反映了当前的一些趋势'、'这个事件值得关注，需要进一步观察'等不针对具体内容的泛泛评论）
3. 评论必须在第一句话或前两句话中就明确提及新闻中的具体事件、人物、数据、时间或地点
4. 不能使用模糊指代（如'这件事'、'这个情况'、'这种做法'、'这个政策'、'这种情况'），必须明确说明具体内容
5. 如果评论不包含新闻的具体信息，则该评论完全无效
6. 评论必须让人能够清楚地看出是针对这篇特定新闻的，而不是可以适用于任何新闻的通用评论

你必须严格遵守这些规则，确保生成的评论明确针对新闻的具体内容。"""
                                    },
                                    {"role": "user", "content": prompt}
                                ],
                                "max_tokens": 350,
                                "temperature": 0.5
                            }
                            
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                response = await client.post(url, headers=headers, json=payload)
                                response.raise_for_status()
                                result = response.json()
                                comment_text = result["choices"][0]["message"]["content"].strip()
                        else:
                            raise Exception("没有可用的API调用方式")
                        
                        break  # 成功则跳出重试循环
                    except Exception as api_error:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise api_error
                        logger.warning(f"[评论生成] API调用失败，重试 {retry_count}/{max_retries}: {str(api_error)}")
                        time.sleep(1)  # 等待1秒后重试
                
                if not comment_text:
                    raise Exception("API返回空内容")
                
                # 移除可能的引导性文字
                for prefix in ["评论：", "评论:", "我认为：", "我认为:", "笔者认为：", "笔者认为:", "评论内容：", "评论内容:"]:
                    if comment_text.startswith(prefix):
                        comment_text = comment_text[len(prefix):].strip()
                
                logger.debug(f"[评论生成] 生成评论 {len(comments)+1}/{count}: {comment_text[:50]}...")
                
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
                                    "content": f"""你是一名专业的新闻评论员。你的任务是**必须基于新闻的具体内容**生成评论。

**绝对规则（违反则评论完全无效）：**
1. 评论必须明确提及或引用新闻中的具体信息：人物姓名、具体事件、数据、时间、地点等
2. 严禁生成通用性评论（如'这件事值得关注'、'需要进一步观察'、'这个情况令人担忧'、'这种做法值得肯定'、'这个新闻反映了当前的一些趋势'、'这个事件值得关注，需要进一步观察'等不针对具体内容的泛泛评论）
3. 评论必须在第一句话或前两句话中就明确提及新闻中的具体事件、人物、数据、时间或地点
4. 不能使用模糊指代（如'这件事'、'这个情况'、'这种做法'、'这个政策'、'这种情况'），必须明确说明具体内容
5. 如果评论不包含新闻的具体信息，则该评论完全无效
6. 评论必须让人能够清楚地看出是针对这篇特定新闻的，而不是可以适用于任何新闻的通用评论

**示例（好的评论）：**
- 如果新闻提到"第十五届全运会在广东举行"，评论应该说"第十五届全运会在广东的举办展现了..."而不是"这个活动值得关注"
- 如果新闻提到具体人物"张三"，评论应该说"张三在...中表示..."而不是"相关人士表示..."
- 如果新闻提到具体数据"1000人"，评论应该说"1000人这一数字反映了..."而不是"这个数字值得关注"

你必须严格遵守这些规则，确保生成的评论明确针对新闻的具体内容。"""
                                },
                                {"role": "user", "content": retry_prompt}
                            ],
                            max_tokens=350,
                            temperature=0.4  # 进一步降低温度，提高准确性
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
                logger.error(f"[评论生成] 生成评论失败 (风格:{assignment['style']}, 观点:{assignment['perspective']}): {str(e)}")
                continue
        
        # 如果生成数量不足，使用备用方法补充
        if len(comments) < count:
            remaining = count - len(comments)
            logger.warning(f"[评论生成] 只生成了 {len(comments)} 条评论，使用备用方法补充 {remaining} 条")
            fallback = await self._generate_fallback(content, summary, remaining, styles, perspectives)
            comments.extend(fallback)
        
        logger.info(f"[评论生成] 完成，共生成 {len(comments)} 条评论")
        return comments[:count]
    
    async def _generate_fallback(
        self,
        content: str,
        summary: str,
        count: int,
        styles: Dict[str, float],
        perspectives: Dict[str, float]
    ) -> List[Dict[str, str]]:
        """备用评论生成方法（基于内容提取关键信息生成评论）"""
        import re
        
        assignments = self._assign_style_perspective(count, styles, perspectives)
        comments = []
        
        # 从新闻内容中提取关键信息用于生成评论
        key_entities = []
        
        # 提取标题中的关键词（去除常见停用词）
        title = summary.split('\n')[0].strip() if summary else ""
        if title:
            # 提取标题中的名词性短语（2-6字）
            title_keywords = re.findall(r'[\u4e00-\u9fff]{2,6}', title)
            key_entities.extend([kw for kw in title_keywords if len(kw) >= 2][:3])
        
        # 从内容中提取关键名词（人名、地名、事件名等）
        content_keywords = re.findall(r'[\u4e00-\u9fff]{2,5}', content[:1000])
        # 统计词频，取出现频率较高的词
        from collections import Counter
        keyword_freq = Counter(content_keywords)
        # 过滤掉常见停用词
        stopwords = {'的', '了', '在', '是', '和', '与', '及', '等', '或', '以及', '以及', '以及', 
                    '这个', '那个', '这些', '那些', '一种', '一个', '一项', '一次', '一种',
                    '进行', '开展', '实施', '推进', '加强', '提高', '完善', '发展', '建设'}
        filtered_keywords = [(word, freq) for word, freq in keyword_freq.items() 
                           if word not in stopwords and len(word) >= 2 and freq >= 2]
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        key_entities.extend([word for word, _ in filtered_keywords[:5]])
        
        # 提取具体数据、时间、地点
        numbers = re.findall(r'[0-9]+(?:\.?[0-9]+)?(?:万|亿|%|人|元|次|项|个|条|件)?', content[:2000])
        if numbers:
            key_entities.extend(numbers[:3])
        
        # 提取时间信息
        times = re.findall(r'[0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{1,2}月[0-9]{1,2}日', content[:2000])
        if times:
            key_entities.extend(times[:2])
        
        # 提取地点信息
        locations = re.findall(r'([^，。]{2,8}?)(?:省|市|区|县|镇|村|市|区)', content[:2000])
        if locations:
            key_entities.extend([loc for loc in locations if len(loc) >= 2][:3])
        
        # 去重但保持顺序
        seen = set()
        unique_entities = []
        for entity in key_entities:
            if entity not in seen:
                seen.add(entity)
                unique_entities.append(entity)
        
        # 提取新闻的核心句子用于生成评论
        sentences = [s.strip() for s in content.split('。') if s.strip() and 20 <= len(s.strip()) <= 200]
        core_sentences = sentences[:5]  # 取前5个核心句子
        
        # 如果提取到了关键实体，基于这些实体生成评论
        if unique_entities and core_sentences:
            # 选择2-3个关键实体用于生成评论
            selected_entities = unique_entities[:min(3, len(unique_entities))]
            
            for assignment in assignments:
                perspective = assignment["perspective"]
                style = assignment["style"]
                
                # 随机选择一个关键实体和核心句子
                entity_ref = random.choice(selected_entities)
                core_sentence = random.choice(core_sentences)
                
                # 提取核心句子中的关键信息（前30-50字）
                sentence_excerpt = core_sentence[:50] if len(core_sentence) > 50 else core_sentence
                
                # 根据观点和风格生成更具体的评论
                if perspective == "positive":
                    if style == "formal":
                        comment_text = f"新闻中提到{sentence_excerpt}，这体现了{entity_ref}的积极意义，值得肯定。"
                    elif style == "casual":
                        comment_text = f"看到{sentence_excerpt}，感觉{entity_ref}这个方向挺好的，希望继续发展。"
                    elif style == "humorous":
                        comment_text = f"{sentence_excerpt}，看来{entity_ref}这次做对了，值得点赞！"
                    elif style == "analytical":
                        comment_text = f"从{sentence_excerpt}可以看出，{entity_ref}这一举措具有积极影响，值得深入分析。"
                    else:  # emotional
                        comment_text = f"{sentence_excerpt}，{entity_ref}让人感到鼓舞，期待更多好消息。"
                elif perspective == "negative":
                    if style == "formal":
                        comment_text = f"新闻中提到{sentence_excerpt}，{entity_ref}相关情况需要引起重视，存在改进空间。"
                    elif style == "casual":
                        comment_text = f"{sentence_excerpt}，{entity_ref}这个问题确实需要关注，希望尽快解决。"
                    elif style == "humorous":
                        comment_text = f"{sentence_excerpt}，{entity_ref}这个情况有点让人担心，得好好处理。"
                    elif style == "analytical":
                        comment_text = f"从{sentence_excerpt}来看，{entity_ref}存在一些问题，需要客观评估和应对。"
                    else:  # emotional
                        comment_text = f"{sentence_excerpt}，{entity_ref}的情况令人担忧，希望相关部门重视。"
                else:  # neutral
                    if style == "formal":
                        comment_text = f"新闻中提到{sentence_excerpt}，关于{entity_ref}的情况需要客观分析，持续关注后续发展。"
                    elif style == "casual":
                        comment_text = f"{sentence_excerpt}，{entity_ref}这个事值得关注，看看后续会怎样。"
                    elif style == "humorous":
                        comment_text = f"{sentence_excerpt}，{entity_ref}这个情况挺有意思，需要观察一下。"
                    elif style == "analytical":
                        comment_text = f"从{sentence_excerpt}可以看出，{entity_ref}涉及多个方面，需要多角度分析。"
                    else:  # emotional
                        comment_text = f"{sentence_excerpt}，{entity_ref}这个话题值得思考，需要理性看待。"
                
                # 根据风格调整
                if style == "humorous":
                    comment_text = f"😄 {comment_text}"
                elif style == "emotional":
                    comment_text = f"💭 {comment_text}"
                elif style == "analytical":
                    comment_text = f"📊 {comment_text}"
                
                comments.append({
                    "text": comment_text,
                    "style": style,
                    "perspective": perspective
                })
        else:
            # 如果没有提取到关键实体，使用改进的模板（至少包含一些内容引用）
            for assignment in assignments:
                perspective = assignment["perspective"]
                style = assignment["style"]
                
                # 尝试从内容中提取第一句有意义的话
                first_sentence = ""
                sentences = [s.strip() for s in content.split('。') if s.strip() and 20 <= len(s.strip()) <= 150]
                if sentences:
                    first_sentence = sentences[0][:50]  # 取前50字符
                
                if first_sentence:
                    if perspective == "positive":
                        comment_text = f"新闻中提到{first_sentence[:30]}...，这是一个积极的信号。"
                    elif perspective == "negative":
                        comment_text = f"新闻中提到{first_sentence[:30]}...，这需要引起关注。"
                    else:
                        comment_text = f"新闻中提到{first_sentence[:30]}...，值得进一步观察。"
                else:
                    # 最后的备用方案
                    templates = {
                        "positive": ["这个新闻反映了积极的进展，值得肯定。"],
                        "neutral": ["这个新闻提供了重要信息，需要客观分析。"],
                        "negative": ["这个新闻反映了一些需要关注的问题。"]
                    }
                    comment_text = random.choice(templates.get(perspective, templates["neutral"]))
                
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

