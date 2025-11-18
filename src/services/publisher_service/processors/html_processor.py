from lxml import html, etree
from src.config.constants import TG_ALLOWED_TAGS, TG_TAG_MAPPING, TG_ALLOWED_ATTRS
from src.utils.logging import get_logger
# ---------------------------------------------------------------------------------------------------------------------


class HTMLProcessor:
    def __init__(
        self, allower_tags: dict = TG_ALLOWED_TAGS, tag_mapping: dict = TG_TAG_MAPPING,
        allowed_attrs: dict = TG_ALLOWED_ATTRS
    ) -> None:
        """
        Инициализирует HTMLProcessor с настройками по умолчанию
        :param allower_tags: Разрешённые теги
        :param tag_mapping: Синонимы тегов
        :param allowed_attrs: Разрешённые атрибуты
        """
        self._log = get_logger().bind(processor="html")
        self._allowed_tags = allower_tags
        self._tag_mapping = tag_mapping
        self._allowed_attrs = allowed_attrs

    def unwrap(self, node):
        """Safely unwrap node preserving text, children and tail."""
        parent = node.getparent()
        if parent is None:
            return

        idx = parent.index(node)

        # 1) Insert node.text
        if node.text:
            text_node = etree.Element("__text__")
            text_node.set("value", node.text)
            parent.insert(idx, text_node)
            idx += 1

        # 2) Move children safely
        children = list(node)
        for child in children:
            node.remove(child)
            parent.insert(idx, child)
            idx += 1

        # 3) Tail text
        if node.tail:
            tail_node = etree.Element("__text__")
            tail_node.set("value", node.tail)
            parent.insert(idx, tail_node)

        # Remove original node
        parent.remove(node)

    def clean(self, node):
        # Рекурсивно чистим детей
        for child in list(node):
            self.clean(child)

        tag = node.tag.lower() if isinstance(node.tag, str) else None

        # пропускаем корень
        if tag == "root":
            return

        # Преобразуем невалидные эквиваленты
        if tag in self._tag_mapping:
            node.tag = self._tag_mapping[tag]
            tag = node.tag

        # Обработка tg-spoiler
        if tag == "span":
            cls = node.attrib.get("class")
            if cls == "tg-spoiler":
                # span валиден, всё ок
                pass
            else:
                # span без tg-spoiler должен быть размотан
                self.unwrap(node)
                return

        if tag == "tg-spoiler":
            # Telegram допускает tg-spoiler как отдельный тег
            tag = "tg-spoiler"
            node.tag = "tg-spoiler"

        # Если тег не разрешён — разматываем
        if tag not in self._allowed_tags:
            self.unwrap(node)
            return

        # Чистим атрибуты
        allowed_attrs = self._allowed_attrs.get(tag, set())
        for attr in list(node.attrib.keys()):
            if attr not in allowed_attrs:
                del node.attrib[attr]

        # Дополнительные правила:
        # <span> только класс "tg-spoiler"
        if tag == "span":
            if node.attrib.get("class") != "tg-spoiler":
                node.attrib.pop("class", None)

    def sanitize_telegram_html(self, text: str) -> str:
        """
        Очищает HTML под Telegram:
        - автоисправление структуры (закрытие тегов)
        - маппинг «синонимов» на разрешённые теги
        - удаление всех запрещённых тегов, сохраняя текст
        - чистка атрибутов
        """
        try:
            try:
                root = html.fromstring(f"<root>{text}</root>")
            except etree.ParserError:
                return text  # если совсем поломанный html

            # Основная очистка
            self.clean(root)

            # Сборка HTML обратно
            return self.serialize(root) or text
        except Exception as e:
            self._log.error(f'Error while sanitizing the html for TG: {e}')

        return text

    def serialize(self, node):
        """Преобразует дерево обратно в HTML"""
        output = []

        for child in node:
            output.append(self.serialize_node(child))

        return "".join(output)

    def serialize_node(self, node):
        if node.tag == "__text__":
            return node.get("text", "")

        tag = node.tag

        # открывающий тег
        attrs = " ".join(f'{k}="{v}"' for k, v in node.attrib.items())
        if attrs:
            start = f"<{tag} {attrs}>"
        else:
            start = f"<{tag}>"

        parts = [start]

        # текст
        if node.text:
            parts.append(node.text)

        # дети
        for child in node:
            parts.append(self.serialize_node(child))

        # закрывающий тег
        parts.append(f"</{tag}>")

        # tail
        if node.tail:
            parts.append(node.tail)

        return "".join(parts)
