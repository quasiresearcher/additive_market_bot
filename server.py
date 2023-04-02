import os
import urllib

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import CallbackQuery
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from aiogram_dialog import Dialog, Window, DialogManager, DialogRegistry, StartMode
from aiogram_dialog.widgets.kbd import Row, SwitchTo, Back, Cancel, Button
from aiogram_dialog.widgets.text import Const, Format

from visualization import visualize_model

storage = MemoryStorage()

API_TOKEN = os.getenv("TELEGRAM_ADDITIVEMARKET_API_TOKEN")
print('API_TOKEN', API_TOKEN)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
registry = DialogRegistry(dp)


class DialogSG(StatesGroup):
    base = State()
    metal = State()
    abs = State()
    order = State()

price_list = {
    'metal_stainless': 0.5,
    'metal_alum': 0.4,
    "abs_standard": 20,
    "abs_tok": 100,
              }

translate = {
    'metal_stainless': ' 12Х18Н10Т (нерж.сталь)',
    "metal_alum": ' AlSi10Mg (алюминий)',
    "abs_standard": ' ABS-Пластик стандарт',
    "abs_tok": ' ABS-Пластик токопроводящий',
             }


async def getter_volume(aiogd_storage_proxy, aiogd_stack, aiogd_context, state,
                        dialog_manager: DialogManager, aiogd_original_callback_data):

    volume = aiogd_context.start_data['volume']
    material = aiogd_original_callback_data.split(aiogd_context._intent_id)[-1].strip()
    price = price_list[material]

    return {
        'price': '{:.1} руб.'.format(price * volume),
        'unit_price': '{} руб./мм3'.format(price),
        'volume': '{:.4} мм3'.format(volume),
        'material_id': material,
        'material': translate[material],
    }


async def make_order(c: CallbackQuery, button: Button, dialog_manager: DialogManager):
    price = c["message"]["reply_markup"]['inline_keyboard'][0][0]['text'].split('Заказать ')[-1]

    await bot.send_message(c.from_user.id, 'Цена: ' + price + '\nЗаказ сделан!')


dialog = Dialog(
    Window(
            Const("Выбор материала:"),
            SwitchTo(Const("Металл"), id="metal", state=DialogSG.metal),
            SwitchTo(Const("ABS-Пластик"), id="abs", state=DialogSG.abs),
            Row(
                Cancel(text=Const("Отмена")),
                ),
            state=DialogSG.base,
        ),
    Window(
        Const("Металл"),
        Row(
            SwitchTo(Const("12Х18Н10Т (нерж.сталь)"), id="metal_stainless", state=DialogSG.order),
            SwitchTo(Const("AlSi10Mg (алюминий)"), id="metal_alum", state=DialogSG.order),
            ),
        Row(
            SwitchTo(Const("Назад"), id="base", state=DialogSG.base),
            Cancel(text=Const("Отмена")),
            ),
        state=DialogSG.metal,
    ),
    Window(
        Format('''Материал: {material}\nОбъем: {volume}\nЦена за мм3: {unit_price}'''),
        Row(
            Cancel(Format("Заказать {price}"), id='order', on_click=make_order),
        ),
        Row(
            SwitchTo(Const("Назад"), id="base", state=DialogSG.base),
            Cancel(text=Const("Отмена")),
        ),
        state=DialogSG.order,
        getter=getter_volume,
    ),
    Window(
        Const("ABS-Пластик"),
        Row(
            SwitchTo(Const("ABS-Пластик стандарт"), id="abs_standard", state=DialogSG.order),
            SwitchTo(Const("ABS-Пластик токопроводящий"), id="abs_tok", state=DialogSG.order),
        ),
        Row(
            SwitchTo(Const("Назад"), id="base", state=DialogSG.base),
            Cancel(text=Const("Отмена")),
        ),
        state=DialogSG.abs,
    ),
)
registry.register(dialog)

#
# async def check_material


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение и помощь по боту"""
    await message.answer(
        "Тут вы можете создать заказ на изготовление 3D модели\n\n"
        "Отправьте файл во вложении, а мы попробуем оценить вашу модель\n")


@dp.message_handler(content_types=['document'])
async def scan_message(message: types.Message, dialog_manager: DialogManager):
    document_id = message.document.file_id
    file_info = await bot.get_file(document_id)
    fi = file_info.file_path
    name = message.document.file_name
    file_format = name.split('.')
    if file_format[-1] == 'stl':
        urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{API_TOKEN}/{fi}', f'./models/{name}')
        await bot.send_message(message.from_user.id, 'Загружаем модель')
        img_location, volume = visualize_model(model_url=f'{name}')
        await bot.send_photo(chat_id=message.from_user.id, photo=open(img_location, 'rb'))
        await bot.send_message(message.from_user.id, 'Объем модели: {:.4} мм3'.format(volume))
        await dialog_manager.start(state=DialogSG.base, mode=StartMode.RESET_STACK, data={'volume': volume})
    else:
        await bot.send_message(message.from_user.id, 'Не похоже на модель')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
