from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter

from src.filters import ChatTypeFilter
from src.handlers.callback_mapping import callback_action_mapping
from src.states.user import TopicEdit, UserRegistration, UserTopic

from . import chat, chat_handle, registration, start, topic, report


def prepare_router() -> Router:
    user_router = Router()
    user_router.message.filter(ChatTypeFilter("private"))

    user_router.message.register(start.start, CommandStart())
    user_router.message.register(chat.chats_command, Command("chats"))
    user_router.message.register(topic.topics_command, Command("topics"))
    user_router.message.register(
        registration.start_registration,
        Command("registration"),
    )
    user_router.message.register(chat_handle.handle_command, Command("handle"))
    # user_router.message.register(payment.pay_command, Command("pay"))

    user_router.message.register(topic.name_topic, StateFilter(UserTopic.name))
    user_router.message.register(
        topic.description_topic,
        StateFilter(UserTopic.description),
    )
    user_router.message.register(topic.gpt_topic, StateFilter(UserTopic.gpt))
    user_router.message.register(topic.edit_topic_field, TopicEdit.edit_name)
    user_router.message.register(topic.edit_topic_field, TopicEdit.edit_description)
    user_router.message.register(topic.edit_topic_field, TopicEdit.edit_prompt)
    user_router.message.register(
        registration.api_id_registration,
        StateFilter(UserRegistration.api_id),
    )
    user_router.message.register(
        registration.api_hash_registration,
        StateFilter(UserRegistration.api_hash),
    )
    user_router.message.register(
        registration.register_client,
        StateFilter(UserRegistration.phone),
    )
    user_router.message.register(
        registration.tg_code_registration,
        StateFilter(UserRegistration.tg_code),
    )
    user_router.message.register(
        registration.password_registration,
        StateFilter(UserRegistration.password),
    )
    # user_router.message.register(
    #     payment.process_amount,
    #     StateFilter("waiting_for_amount"),
    # )

    user_router.message.register(report.report_command, Command("report"))
    user_router.message.register(
        report.generate_report,
        StateFilter("waiting_for_report_period"),
    )

    # user_router.message.register(restore.start_restore, Command("restore_session"))
    # user_router.message.register(
    #     restore.restore_code,
    #     StateFilter("waiting_for_restore_code"),
    # )
    # user_router.message.register(
    #     restore.restore_password,
    #     StateFilter("waiting_for_restore_password"),
    # )

    for handler, filter_ in callback_action_mapping:
        user_router.callback_query.register(handler, filter_)

    return user_router
