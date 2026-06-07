import vk_api
from datetime import datetime
import re

class VKParser:
    def __init__(self, token):
        self.vk_session = vk_api.VkApi(token=token)
        self.vk = self.vk_session.get_api()

    def extract_group_id(self, link):
        """Извлечение ID/domain группы из различных форматов ссылок"""
        link = link.split('?')[0].strip()

        wall_pattern = r'vk\.com/wall(-?\d+)_\d+'
        wall_match = re.search(wall_pattern, link)

        if wall_match:
            group_id = wall_match.group(1)
            print(f"Обнаружена ссылка на пост, извлекаю группу: {group_id}")
            return group_id

        public_club_pattern = r'vk\.com/(public|club)(\d+)'
        public_club_match = re.search(public_club_pattern, link)

        if public_club_match:
            group_type = public_club_match.group(1)
            group_num = public_club_match.group(2)
            print(f"Обнаружен формат {group_type}{group_num}")
            return f"-{group_num}"

        screen_name_pattern = r'vk\.com/([a-zA-Z0-9_.]+)'
        screen_name_match = re.search(screen_name_pattern, link)

        if screen_name_match:
            screen_name = screen_name_match.group(1)
            print(f"Извлечён screen_name: {screen_name}")
            return screen_name

        raise ValueError(f"Не удалось извлечь ID/domain из ссылки: {link}")

    def get_group_info(self, group_id):
        """Получение информации о группе/паблике"""
        try:
            clean_id = group_id.replace('-', '')

            if clean_id.isdigit():
                response = self.vk.groups.getById(group_id=clean_id)[0]
            else:
                response = self.vk.groups.getById(group_id=clean_id)[0]

            return {
                'name': response.get('name', 'Неизвестно'),
                'screen_name': response.get('screen_name', clean_id),
                'id': response.get('id', clean_id),
                'link': f"https://vk.com/{response.get('screen_name', f'public{clean_id}')}"
            }
        except Exception as e:
            print(f"Не удалось получить информацию о группе {group_id}: {e}")
            return {
                'name': f'Группа {group_id}',
                'screen_name': group_id,
                'id': group_id,
                'link': f"https://vk.com/public{group_id.replace('-', '')}"
            }

    def extract_links_from_vk_text(self, text):
        """Извлечение ссылок из текста VK поста"""
        links = []

        https_pattern = r'https?://[^\s\)\],<>\"\']+'
        https_matches = re.findall(https_pattern, text)
        links.extend(https_matches)

        text_cleaned = text
        for match in https_matches:
            text_cleaned = text_cleaned.replace(match, '')

        vk_internal_pattern = r'\[(club|public)(\d+)\|[^\]]+\]'
        vk_matches = re.findall(vk_internal_pattern, text_cleaned)
        for match in vk_matches:

            club_type = match[0]
            club_id = match[1]

            links.append(f"https://vk.com/{club_type}{club_id}")
            links.append(f"https://vk.com/club{club_id}")
            links.append(f"vk.com/{club_type}{club_id}")
            links.append(f"{club_type}{club_id}")

        vk_direct_pattern = r'\bvk\.com/([a-zA-Z0-9_.]+)'
        vk_direct_matches = re.findall(vk_direct_pattern, text_cleaned)
        for match in vk_direct_matches:
            full_link = f"https://vk.com/{match}"
            if full_link not in links:
                links.append(full_link)
                links.append(f"vk.com/{match}")

        tg_pattern = r'\bt\.me/([a-zA-Z0-9_]+)'
        tg_matches = re.findall(tg_pattern, text_cleaned)
        for match in tg_matches:
            links.append(f"https://t.me/{match}")
            links.append(f"t.me/{match}")

        seen = set()
        unique_links = []
        for link in links:
            link_lower = link.lower()
            if link_lower not in seen:
                seen.add(link_lower)
                unique_links.append(link)

        return unique_links

    async def parse_group(self, link, keywords):
        """Парсинг постов группы VK"""
        results = []

        try:
            group_id = self.extract_group_id(link)
            print(f"Парсинг VK группы: {group_id}")

            group_info = self.get_group_info(group_id)
            group_name = group_info['name']
            group_link = group_info['link']

            print(f"Найдена группа: {group_name} ({group_link})")

            criteria = keywords.get('criteria', [])

            print(f"Критериев поиска: {len(criteria)}")

            for i, criterion in enumerate(criteria, 1):
                text_elems = criterion.get('text_elements', [])
                link_elems = criterion.get('link_elements', [])
                print(f"   Критерий {i}:")
                if text_elems:
                    print(f"      Текст: {text_elems}")
                if link_elems:
                    print(f"      Ссылки: {link_elems}")

            offset = 0
            max_posts = 500
            posts_per_request = 100

            total_posts_checked = 0
            posts_with_text = 0

            while offset < max_posts:
                try:

                    clean_id = group_id.replace('-', '')

                    if clean_id.isdigit():

                        owner_id_param = f"-{clean_id}" if not group_id.startswith('-') else group_id

                        print(f"Запрос VK API: owner_id={owner_id_param}, offset={offset}")

                        response = self.vk.wall.get(
                            owner_id=owner_id_param,
                            count=min(posts_per_request, max_posts - offset),
                            offset=offset
                        )
                    else:

                        print(f"Запрос VK API: domain={group_id}, offset={offset}")

                        response = self.vk.wall.get(
                            domain=group_id,
                            count=min(posts_per_request, max_posts - offset),
                            offset=offset
                        )

                    posts = response['items']

                    if not posts:
                        print(f"Больше нет постов (offset={offset})")
                        break

                    print(f"Получено {len(posts)} постов (offset {offset})")

                    for post in posts:
                        total_posts_checked += 1
                        post_text = post.get('text', '')

                        if post_text:
                            posts_with_text += 1

                        post_links = self.extract_links_from_vk_text(post_text)

                        if 'attachments' in post:
                            for attach in post['attachments']:
                                if attach['type'] == 'link':
                                    post_links.append(attach['link']['url'])

                        match_found = False
                        matched_criterion = None

                        for criterion in criteria:
                            text_elements = criterion.get('text_elements', [])
                            link_elements = criterion.get('link_elements', [])

                            all_text_found = True
                            all_links_found = True

                            if text_elements:
                                for text_elem in text_elements:
                                    if not self._contains_text(post_text, text_elem):
                                        all_text_found = False
                                        break

                            if link_elements:
                                for link_elem in link_elements:

                                    normalized_search = link_elem.replace('https://', '').replace('http://',
                                                                                                  '').replace('www.',
                                                                                                              '').lower().rstrip(
                                        '/')

                                    clean_search = normalized_search.split('/')[-1]

                                    link_found_in_post = False
                                    for post_link in post_links:
                                        normalized_post = post_link.replace('https://', '').replace('http://',
                                                                                                    '').replace('www.',
                                                                                                                '').lower().rstrip(
                                            '/')
                                        clean_post = normalized_post.split('/')[-1]

                                        if (normalized_search in normalized_post or
                                                normalized_post in normalized_search or
                                                clean_search == clean_post or
                                                clean_search in clean_post or
                                                clean_post in clean_search):
                                            link_found_in_post = True
                                            print(f"   Найдена ссылка: {link_elem} {post_link}")
                                            break

                                    if not link_found_in_post:
                                        all_links_found = False
                                        print(f"   Не найдена ссылка: {link_elem}")
                                        break

                            if all_text_found and all_links_found:
                                match_found = True
                                matched_criterion = criterion

                                text_preview = ', '.join([t[:30] for t in text_elements[:2]]) if text_elements else ''
                                link_preview = ', '.join(
                                    [l.split('/')[-1] for l in link_elements[:2]]) if link_elements else ''
                                print(f"Совпадение в посте: {text_preview} {link_preview}")
                                break

                        if match_found:
                            owner_id = post['owner_id']
                            post_id = post['id']
                            post_link_url = f"https://vk.com/wall{owner_id}_{post_id}"

                            result = {
                                'source_name': group_name,
                                'source_link': group_link,
                                'link': post_link_url,
                                'date': datetime.fromtimestamp(post['date']),
                                'views': post.get('views', {}).get('count', 0),
                                'text': post_text,
                                'found_links': post_links,
                                'matched_criterion': matched_criterion
                            }
                            results.append(result)

                    offset += posts_per_request

                except Exception as e:
                    print(f"Ошибка при получении постов (offset {offset}): {e}")
                    break

            print(f"Статистика парсинга:")
            print(f"   Всего постов проверено: {total_posts_checked}")
            print(f"   Постов с текстом: {posts_with_text}")
            print(f"   Найдено совпадений: {len(results)}")

            print(f"VK парсинг завершён: найдено {len(results)} постов в {group_name}")

        except Exception as e:
            print(f"Ошибка VK парсинга {link}: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"VK парсинг failed: {str(e)}")

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
