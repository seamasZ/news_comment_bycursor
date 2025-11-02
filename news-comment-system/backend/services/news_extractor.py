import asyncio
from typing import Dict
import httpx
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
        
        # 提取文本
        text = self._clean_text(content.get_text())
        
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
        """清理文本"""
        import re
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

