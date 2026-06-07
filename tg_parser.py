from telethon import TelegramClient
from datetime import datetime
import re

class TGParser:
    def __init__(self, api_id, api_hash):
        self.api_id = int(api_id)
        self.api_hash = api_hash
        self.client = TelegramClient('parser_session', self.api_id, self.api_hash)

    async def start(self):
        await self.client.start()

    async def stop(self):
        await self.client.disconnect()

    async def get_channel_info(self, channel_username):
        """Получение информации о канале"""
        try:
            entity = await self.client.get_entity(channel_username)

            return {
                'name': entity.title if hasattr(entity, 'title') else channel_username,
                'username': entity.username if hasattr(entity, 'username') else channel_username,
                'id': entity.id,
                'link': f"https://t.me/{entity.username if hasattr(entity, 'username') else channel_username}"
            }
        except Exception as e:
            print(f"Не удалось получить информацию о канале {channel_username}: {e}")
            return {
                'name': channel_username,
                'username': channel_username,
                'id': channel_username,
                'link': f"https://t.me/{channel_username}"
            }

    def extract_links_from_tg_message(self, message):
        """Извлечение ссылок из Telegram сообщения"""
        links = []

        if message.entities:
            for entity in message.entities:
                try:

                    entity_type = entity.__class__.__name__

                    if entity_type == 'MessageEntityTextUrl':
                        if hasattr(entity, 'url'):
                            links.append(entity.url)

                    elif entity_type == 'MessageEntityUrl':
                        offset = entity.offset
                        length = entity.length
                        url = message.message[offset:offset + length]

                        if not url.startswith('http'):
                            if 'vk.com' in url or 't.me' in url:
                                url = f"https://{url}"
                        links.append(url)

                    elif entity_type == 'MessageEntityMention':
                        offset = entity.offset
                        length = entity.length
                        username = message.message[offset:offset + length]

                        if username.startswith('@'):
                            username = username[1:]
                        if len(username) >= 5:
                            links.append(f"https://t.me/{username}")

                except Exception as e:
                    print(f"Ошибка при обработке entity {entity_type}: {e}")
                    continue

        text = message.message

        vk_pattern = r'\bhttps?://vk\.com/([a-zA-Z0-9_]+)'
        vk_matches = re.findall(vk_pattern, text)
        for match in vk_matches:
            links.append(f"https://vk.com/{match}")

        tg_pattern = r'\bhttps?://t\.me/([a-zA-Z0-9_]+)'
        tg_matches = re.findall(tg_pattern, text)
        for match in tg_matches:
            links.append(f"https://t.me/{match}")

        text_for_vk = text
        for link in links:
            text_for_vk = text_for_vk.replace(link, '')

        vk_no_protocol = r'\bvk\.com/([a-zA-Z0-9_]+)'
        vk_no_proto_matches = re.findall(vk_no_protocol, text_for_vk)
        for match in vk_no_proto_matches:
            link = f"https://vk.com/{match}"
            if link not in links:
                links.append(link)

        tg_no_protocol = r'\bt\.me/([a-zA-Z0-9_]+)'
        tg_no_proto_matches = re.findall(tg_no_protocol, text_for_vk)
        for match in tg_no_proto_matches:
            link = f"https://t.me/{match}"
            if link not in links:
                links.append(link)

        unique_links = []
        seen = set()

        for link in links:

            normalized = link.lower().rstrip('/')
            if normalized not in seen:
                seen.add(normalized)
                unique_links.append(link)

        return unique_links

    async def parse_channel(self, link, keywords):
        results = []

        try:
            channel_username = link.replace('https://t.me/', '').replace('@', '').strip()

            channel_info = await self.get_channel_info(channel_username)
            channel_name = channel_info['name']
            channel_link = channel_info['link']

            print(f"Найден канал: {channel_name} ({channel_link})")

            criteria = keywords.get('criteria', [])

            print(f"Критериев поиска: {len(criteria)}")

            async for message in self.client.iter_messages(channel_username, limit=1000):
                if not message.message:
                    continue

                message_text = message.message
                message_links = self.extract_links_from_tg_message(message)

                match_found = False
                matched_criterion = None

                for criterion in criteria:
                    text_elements = criterion.get('text_elements', [])
                    link_elements = criterion.get('link_elements', [])

                    all_text_found = True
                    all_links_found = True

                    if text_elements:
                        for text_elem in text_elements:
                            if not self._contains_text(message_text, text_elem):
                                all_text_found = False
                                break

                    if link_elements:
                        for link_elem in link_elements:
                            normalized_search = link_elem.replace('https://', '').replace('http://', '').replace('www.',
                                                                                                                 '')

                            link_found_in_message = False
                            for msg_link in message_links:
                                normalized_msg = msg_link.replace('https://', '').replace('http://', '').replace('www.',
                                                                                                                 '')

                                if normalized_search in normalized_msg or normalized_msg in normalized_search:
                                    link_found_in_message = True
                                    break

                            if not link_found_in_message:
                                all_links_found = False
                                break

                    if all_text_found and all_links_found:
                        match_found = True
                        matched_criterion = criterion
                        print(f"Совпадение по критерию: {text_elements} + {link_elements}")
                        break

                if match_found:
                    result = {
                        'source_name': channel_name,
                        'source_link': channel_link,
                        'link': f"https://t.me/{channel_username}/{message.id}",
                        'date': message.date,
                        'views': message.views if message.views else 0,
                        'text': message_text,
                        'found_links': message_links,
                        'matched_criterion': matched_criterion
                    }
                    results.append(result)

            print(f"TG парсинг завершён: найдено {len(results)} постов в {channel_name}")

        except Exception as e:
            print(f"Ошибка TG парсинга: {e}")

        return results

    def _normalize_hashtag(self, text):
        """Нормализация хештегов для поиска"""

        text = re.sub(r'#(\w+)\.(\w+)', r'#\1\2', text)
        return text

    def _contains_text(self, text, keyword):
        """Проверка наличия текста с нормализацией"""
        import re

        text_normalized = self._normalize_hashtag(text.lower())
        keyword_normalized = self._normalize_hashtag(keyword.lower().strip())

        keyword_escaped = re.escape(keyword_normalized)

        if keyword_normalized.startswith('#'):

            pattern = r'(?:^|[\s])' + keyword_escaped + r'(?=[\s\.\,\;\!\?\)\]\}]|$)'
        else:

            pattern = r'\b' + keyword_escaped + r'\b'

        return bool(re.search(pattern, text_normalized))

    def _contains_keywords(self, text, keywords):
        """Поиск ключевых слов с поддержкой AND-оператора (+)"""
        if not keywords:
            return False

        text_normalized = ' '.join(text.split()).lower()

        for keyword in keywords:
            if '+' in keyword:
                parts = [part.strip() for part in keyword.split('+')]
                parts_normalized = [' '.join(p.split()).lower() for p in parts]
                all_found = all(part in text_normalized for part in parts_normalized)
                if all_found:
                    return True
            else:
                keyword_normalized = ' '.join(keyword.split()).lower()
                if keyword_normalized in text_normalized:
                    return True

        return False
