from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatConfig:
    general_chat_id: Optional[int] = -1003767775982      # Общий чат
    announcements_id: Optional[int] = -1003677400542     # Канал объявлений
    help_chat_id: Optional[int] = None                    # Чат помощи


chat_config = ChatConfig()