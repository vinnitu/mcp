import urllib.request
import urllib.error
import re
import html
from html.parser import HTMLParser
from fastmcp import FastMCP

mcp = FastMCP("telegram-moderator")


class MetaTagParser(HTMLParser):
    """Простий парсер для витягування meta тегів та класів"""
    
    def __init__(self):
        super().__init__()
        self.og_description = None
        self.twitter_description = None
        self.in_message_text = False
        self.message_text_content = []
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        # Шукаємо meta теги
        if tag == 'meta':
            # og:description
            if attrs_dict.get('property') == 'og:description':
                self.og_description = attrs_dict.get('content')
            # twitter:description
            elif attrs_dict.get('name') == 'twitter:description':
                self.twitter_description = attrs_dict.get('content')
        
        # Шукаємо div з класом tgme_widget_message_text
        if tag == 'div':
            class_attr = attrs_dict.get('class', '')
            if 'tgme_widget_message_text' in class_attr:
                self.in_message_text = True
    
    def handle_endtag(self, tag):
        if tag == 'div' and self.in_message_text:
            self.in_message_text = False
    
    def handle_data(self, data):
        if self.in_message_text:
            self.message_text_content.append(data)
    
    def get_message_text(self):
        """Повертає знайдений текст повідомлення"""
        if self.og_description:
            return self.og_description
        if self.twitter_description:
            return self.twitter_description
        if self.message_text_content:
            return ''.join(self.message_text_content).strip()
        return None


@mcp.tool()
def get_telegram_message_content_by_ling(url: str) -> str:
    """
    Витягує текст повідомлення з публічного Telegram каналу
    
    Args:
        url (str): URL повідомлення типу https://t.me/channel_name/message_id
        
    Returns:
        str: Текст повідомлення
    """
    return get_telegram_message(url)


def get_telegram_message(url: str) -> str:
    """
    Витягує текст повідомлення з публічного Telegram каналу
    Використовує тільки вбудовані бібліотеки Python (urllib, html.parser, re, html)
    
    Args:
        url (str): URL повідомлення типу https://t.me/channel_name/message_id
        
    Returns:
        str: Текст повідомлення
        
    Raises:
        ValueError: Якщо формат URL невірний
        Exception: Якщо виникла помилка при отриманні або парсингу повідомлення
    """
    # Перевірка формату URL
    url_pattern = r'^https?://t\.me/[\w\d_]+/\d+$'
    if not re.match(url_pattern, url):
        raise ValueError('Невірний формат URL. Очікується: https://t.me/channel_name/message_id')
    
    try:
        # Створюємо запит з User-Agent
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        
        # Робимо HTTP запит до Telegram
        with urllib.request.urlopen(req) as response:
            html_content = response.read().decode('utf-8')
        
        # Парсимо HTML за допомогою вбудованого парсера
        parser = MetaTagParser()
        parser.feed(html_content)
        
        message_text = parser.get_message_text()
        
        if not message_text or message_text.strip() == '':
            raise Exception('Не вдалося знайти текст повідомлення. Можливо, повідомлення не існує або канал приватний.')
        
        # Декодуємо HTML entities (наприклад, &#33; -> !)
        message_text = html.unescape(message_text).strip()
        
        return message_text
        
    except urllib.error.HTTPError as e:
        raise Exception(f'Помилка HTTP: {e.code} - {e.reason}')
    except urllib.error.URLError as e:
        raise Exception(f'Помилка URL: {str(e.reason)}')
    except Exception as e:
        if 'знайти текст повідомлення' in str(e):
            raise
        raise Exception(f'Помилка: {str(e)}')


if __name__ == '__main__':
    # Приклад використання
    test_url = 'https://t.me/atodoneckpobeda/1341833'
    
    try:
        message = get_telegram_message(test_url)
        print(message)
    except Exception as error:
        print(f'Помилка: {error}')
