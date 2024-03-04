from typing import Union, Optional

from aiogram import methods, types


def get_call_method(message: Union[dict, types.Message], reply_markup: Optional[types.InlineKeyboardMarkup] = None):
    if isinstance(message, dict):
        message = types.Message(**message)
    match message.content_type:
        case "text":
            obj = message.text
            call = methods.SendMessage
        case "photo":
            obj = message.photo[-1].file_id
            call = methods.SendPhoto
        case "audio":
            obj = message.audio.file_id
            call = methods.SendAudio
        case "video":
            obj = message.video.file_id
            call = methods.SendVideo
        case "video_note":
            obj = message.video_note.file_id
            call = methods.SendVideoNote
        case "voice":
            obj = message.voice.file_id
            call = methods.SendVoice
        case _:
            return
    kwargs = {
        message.content_type: obj,
        "caption": message.caption,
        "caption_entities": message.caption_entities,
        "reply_markup": reply_markup or message.reply_markup
    }

    def inner_func(chat_id: int):
        kwargs["chat_id"] = chat_id
        return call(**kwargs)

    return inner_func
