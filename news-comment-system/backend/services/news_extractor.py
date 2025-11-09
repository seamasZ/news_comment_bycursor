import asyncio
from typing import Dict
import httpx
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
try:
    import newspaper
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False


class NewsExtractor:
    """新闻内容提取器，去除广告、导航等无关内容"""
    
    def __init__(self):
        # 常见需要移除的标签和类名
        self.unwanted_selectors = [
            'nav', 'header', 'footer', 'aside',
            '.advertisement', '.ad', '.ads', '.ad-box',
            '.sidebar', '.menu', '.navigation',
            '.comment-section', '.social-share',
            '[class*="ad"]', '[id*="ad"]',
            'script', 'style', 'iframe',
            '.popup', '.modal', '.overlay'
        ]
    
    async def extract(self, url: str) -> Dict[str, str]:
        """提取新闻内容"""
        # 优先尝试使用newspaper3k（如果可用）
        if NEWSPAPER_AVAILABLE:
            try:
                article = Article(str(url))
                article.download()
                article.parse()
                
                # 如果newspaper提取成功且有足够内容
                if article.text and len(article.text) >= 100:
                    text = self._clean_text(article.text)
                    title = article.title if article.title else "未找到标题"
                    
                    return {
                        "title": title,
                        "text": text,
                        "url": str(url)
                    }
            except Exception as e:
                # newspaper失败，继续使用BeautifulSoup
                # 记录错误但不抛出，尝试BeautifulSoup
                print(f"newspaper3k提取失败，尝试BeautifulSoup: {str(e)}")
        
        # 使用BeautifulSoup作为主要或备选方案
        return await self._extract_with_bs4(url)
    
    async def _extract_with_bs4(self, url: str) -> Dict[str, str]:
        """使用BeautifulSoup提取内容"""
        # 设置浏览器请求头，模拟真实浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers, follow_redirects=True) as client:
                response = await client.get(str(url))
                response.raise_for_status()
                
                # 尝试使用 lxml，如果不可用则使用 html.parser
                try:
                    soup = BeautifulSoup(response.text, 'lxml')
                except:
                    soup = BeautifulSoup(response.text, 'html.parser')
        except httpx.TimeoutException:
            raise Exception(f"请求超时，无法访问URL: {url}")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 403:
                raise Exception(
                    f"HTTP 403 错误：网站拒绝访问（可能是反爬虫机制）。\n"
                    f"URL: {url}\n"
                    f"建议：\n"
                    f"1. 尝试使用其他新闻网站\n"
                    f"2. 某些网站（如搜狐、新浪等）有严格的反爬虫机制\n"
                    f"3. 建议使用公开的、支持爬虫的新闻网站"
                )
            elif status_code == 404:
                raise Exception(f"HTTP 404 错误：找不到该页面。请检查URL是否正确: {url}")
            else:
                raise Exception(f"HTTP错误 {status_code}: 无法访问URL: {url}")
        except Exception as e:
            raise Exception(f"无法访问URL {url}: {str(e)}")
        
        # 移除不需要的元素
        for selector in self.unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # 尝试找到主要内容区域
        # 常见的文章容器
        article_selectors = [
            'article',
            '.article', '.content', '.post', '.story',
            '[class*="article"]', '[class*="content"]',
            'main', '.main-content'
        ]
        
        content = None
        for selector in article_selectors:
            elements = soup.select(selector)
            if elements:
                # 选择最长的内容块
                content = max(elements, key=lambda x: len(x.get_text()))
                break
        
        if not content:
            # 如果找不到特定容器，尝试body
            content = soup.find('body')
            if content:
                # 移除header、nav、footer等
                for tag in ['header', 'nav', 'footer', 'aside']:
                    for elem in content.find_all(tag):
                        elem.decompose()
        
        if not content:
            content = soup
        
        # 提取标题
        title = None
        title_tags = ['h1', 'title']
        for tag in title_tags:
            title_elem = soup.find(tag)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        if not title:
            title = "未找到标题"
        
        # 提取文本并清理
        raw_text = content.get_text()
        logger = logging.getLogger(__name__)
        logger.debug(f"[新闻提取] 提取的原始文本长度: {len(raw_text)}")
        text = self._clean_text(raw_text)
        logger.info(f"[新闻提取] 清理后文本长度: {len(text)}")
        
        # 如果内容过短，提供更友好的错误信息
        if len(text) < 100:
            raise Exception(
                f"提取的内容过短（仅{len(text)}字符），可能不是有效的新闻文章。\n"
                f"可能的原因：\n"
                f"1. URL指向的不是新闻文章页面\n"
                f"2. 网站有反爬虫机制阻止了内容提取\n"
                f"3. 页面需要JavaScript动态加载内容\n"
                f"建议：尝试使用其他新闻网站的URL"
            )
        
        return {
            "title": title,
            "text": text,
            "url": str(url)
        }
    
    def _clean_text(self, text: str) -> str:
        """清理文本，去除导航链接、重复内容等无关信息"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        original_length = len(text)
        logger.debug(f"[文本清理] 开始清理文本，原始长度: {original_length}")
        
        # 移除常见的导航链接文本（这些通常不是新闻正文）
        navigation_patterns = [
            r'首页|主页|Home',
            r'上一页|下一页|上一张|下一张',
            r'返回|返回顶部|Back',
            r'登录|注册|Login|Register',
            r'搜索|Search',
            r'分享|Share|扫码分享',
            r'收藏|收藏夹|Favorites',
            r'专题首页|直播首页|直播关注',
            r'精彩图集|精彩视频',
            r'TOP|置顶',
            r'刷新|自动刷新|手动刷新|间隔.*秒|间隔.*分钟',
            r'扫码|二维码|QR',
            r'关注我们|Follow us',
            r'关于我们|About|联系我们|Contact',
            r'版权|Copyright|©',
            r'ICP备案|备案号',
            r'京公网安备',
            r'[0-9]{4}-[0-9]{2}-[0-9]{2}\s+[0-9]{2}:[0-9]{2}:[0-9]{2}',  # 时间戳（如果单独出现）
        ]
        
        # 移除重复的标题和导航文本
        lines = text.split('\n')
        if len(lines) > 0:
            first_line = lines[0].strip()
            # 如果第一行（可能是标题）在后续内容中重复出现，移除这些重复
            if first_line and len(first_line) > 5:
                filtered_lines = [lines[0]]  # 保留第一行
                for i, line in enumerate(lines[1:], 1):
                    line_stripped = line.strip()
                    # 跳过完全相同的行
                    if line_stripped == first_line:
                        continue
                    # 跳过只包含标题部分的行（如果标题很长）
                    if len(first_line) > 20 and first_line[:20] in line_stripped and len(line_stripped) < len(first_line) + 10:
                        continue
                    filtered_lines.append(line)
                text = '\n'.join(filtered_lines)
        
        # 移除导航链接模式（更彻底）
        for pattern in navigation_patterns:
            # 先尝试整行匹配（如果整行都是导航文本，直接删除）
            lines = text.split('\n')
            filtered_lines = []
            for line in lines:
                line_stripped = line.strip()
                # 如果整行匹配导航模式，跳过
                if re.match(pattern + r'$', line_stripped, flags=re.IGNORECASE):
                    continue
                # 否则只移除匹配的部分
                line = re.sub(pattern, '', line, flags=re.IGNORECASE)
                if line.strip():  # 如果移除后还有内容，保留
                    filtered_lines.append(line)
            text = '\n'.join(filtered_lines)
            
            # 再次在整个文本中移除（处理跨行的模式）
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 移除URL链接文本（保留链接后的描述性文字）
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'www\.[^\s]+', '', text)
        
        # 移除常见的页面元素文本
        page_elements = [
            r'相关新闻|Related|推荐阅读|Recommended',
            r'热门评论|Hot Comments|最新评论',
            r'广告|Advertisement|AD',
            r'下载APP|Download App',
            r'客户端|Client|APP',
        ]
        for element in page_elements:
            text = re.sub(element, '', text, flags=re.IGNORECASE)
        
        # 移除多余空白和换行
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 移除过短的句子和包含导航关键词的句子
        sentences = text.split('。')
        cleaned_sentences = []
        navigation_keywords = ['首页', '返回', '分享', '刷新', '扫码', '专题', '直播', '图集', '视频', 'TOP', '置顶']
        
        for sentence in sentences:
            sentence = sentence.strip()
            # 跳过过短的句子（可能是导航元素）
            if len(sentence) < 10:
                continue
            # 跳过只包含导航关键词的句子
            if any(keyword in sentence and len(sentence) < 30 for keyword in navigation_keywords):
                continue
            # 跳过只包含数字和符号的句子（可能是时间戳或页码）
            if re.match(r'^[0-9\s\-:年月日秒分]+$', sentence):
                continue
            # 保留有意义的句子
            if len(sentence) > 10 or bool(re.search(r'[\u4e00-\u9fff]', sentence)):
                cleaned_sentences.append(sentence)
        
        text = '。'.join(cleaned_sentences)
        
        # 最终清理
        text = re.sub(r'\s+', ' ', text)
        cleaned_text = text.strip()
        
        final_length = len(cleaned_text)
        logger.debug(f"[文本清理] 清理完成，最终长度: {final_length}，减少了 {original_length - final_length} 字符")
        
        return cleaned_text

