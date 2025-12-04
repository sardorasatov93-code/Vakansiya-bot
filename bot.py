import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

API_TOKEN = config["token"]
ADMIN_ID = config["admin_id"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_reference_file = State()
    waiting_for_passport_info = State()
    admin_select_tuman = State()
    admin_add_jobs = State()

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

vacancies = load_data() 

all_tumans = [ 
    "Arnasoy", "Baxmal", "Do'stlik", "G'allaorol", "Jizzax shahar",
    "Sharof Rashidov", "Zafarobod", "Zarbdor", "Zomin", "Mirzacho'l",
    "Paxtakor", "Forish", "Yangiobod"
] 

MALAKA_TALABLARI_TEXT = """
**Direktor lavozimiga qo‘yiladigan malaka talablari:**

**Ma’lumot:** Nomzod oliy ma’lumotga, ya’ni bakalavr diplomiga ega bo‘lishi lozim. Magistratura darajasi yoki ilmiy unvon mavjudligi afzal.

**Mutaxassislik:** Pedagogika yo‘nalishida tahsil olgan bo‘lishi kerak. Agar nomzod pedagog bo‘lmasa yoki boshqa sohada oliy ma’lumotga ega bo‘lsa, u holda pedagogika yo‘nalishi bo‘yicha kasbiy qayta tayyorlash kursini tamomlagan bo‘lishi shart.

**Mehnat staji:** Kamida 3 yillik pedagogik ish tajribasiga ega bo‘lishi zarur.

**Kompyuter savodxonligi:** Microsoft Office dasturlari (Word, Excel, PowerPoint va boshqalar), zamonaviy axborot texnologiyalari, axborot tizimlari hamda internet tarmog‘ida ishlash bo‘yicha yetarli ko‘nikmaga ega bo‘lishi lozim.

**Qo‘shimcha talablar:**
1. O‘zbekiston Respublikasining “Maktabgacha ta’lim va tarbiya to‘g‘risida”, “Ta’lim to‘g‘risida”, “Pedagogning maqomi to‘g‘risida”, “Davlat fuqarolik xizmati to‘g‘risida”gi qonunlarini to‘liq bilishi;
2. Davlat tilini bilishi shart. Rus, ingliz yoki boshqa chet tillarini bilish afzallik hisoblanadi;
3. Menejerlik sertifikatiga ega bo‘lishi;
4. Ilmiy daraja yoki ilmiy unvonga ega bo‘lgan, hududiy maktabgacha va maktab ta’limi bo‘limlarida ikki yildan ortiq faoliyat yuritgan, Davlat mukofotlari bilan taqdirlangan yosh mutaxassislardan pedagogik ish staji talab etilmaydi;
5. Soha bo‘yicha normativ-huquqiy hujjatlarni bilishi, ularni amaliyotga tatbiq eta olishi, doimiy ravishda malakasini oshirgan bo‘lishi.

**Cheklovlar:**
O‘zbekiston Respublikasining “Maktabgacha ta’lim va tarbiya to‘g‘risida”gi Qonunning 44-moddasiga muvofiq, quyidagi shaxslar maktabgacha ta’lim tizimida mehnat faoliyatini amalga oshira olmaydi:
1. Muomala layoqatsiz yoki muomala layoqati cheklangan deb topilgan, pedagogik faoliyatga to‘sqinlik qiladigan kasalliklari yoki jismoniy nuqsonlari mavjud shaxslar;
2. Xizmat vazifalarini suiste’mol qilgan yoki jinoyat sodir etganlik uchun ilgari sudlangan shaxslar;
3. Maktabgacha ta’lim tashkilotlarida pedagogik faoliyatni amalga oshirishga yo‘l qo‘yilmaydi.

---
**Murojaat uchun:**
📞 Telefon: +998 93 303 54 54
👤 Admin: Sardor Asatov
"""
def get_back_buttons(back_callback=None):
    buttons = []
    if back_callback:
        buttons.append(InlineKeyboardButton(text="⬅️ Ortga qaytish", callback_data=back_callback))
    
    buttons.append(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="go_to_start"))
    
    return [buttons]

@dp.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("Salom Admin! Ish joylarini boshqarish uchun /admin yozing.")
        return

    full_start_text = "👋 Salom, siz Jizzax viloyat DMTT bo‘sh ish o‘rinlari bo‘limidasiz.\n\n" + MALAKA_TALABLARI_TEXT
    
    await message.answer(full_start_text, parse_mode="Markdown")

    available_tumans = [tuman for tuman, jobs in vacancies.items() if jobs]

    if not available_tumans:
        await message.answer("⚠️ **Hozirda hech qaysi tumanda bo'sh ish o'rinlari mavjud emas!**\nAdmin hali ish joyi qo'shgani yo'q.", parse_mode="Markdown")
        return

    keyboard_buttons = []
    row = []
    for i, tuman in enumerate(available_tumans, 1):
        row.append(InlineKeyboardButton(text=tuman, callback_data=f"user_tuman_{tuman}"))
        if i % 2 == 0:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer("👇 Bo'sh ish o'rinlari mavjud tumanni tanlang:", reply_markup=kb)

@dp.callback_query(F.data == "go_to_start")
async def go_to_start_handler(callback: types.CallbackQuery, state: FSMContext):
    await start(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data == "back_to_tuman_selection")
async def back_to_tuman_selection(callback: types.CallbackQuery, state: FSMContext):
    available_tumans = [tuman for tuman, jobs in vacancies.items() if jobs]

    keyboard_buttons = []
    row = []
    for i, tuman in enumerate(available_tumans, 1):
        row.append(InlineKeyboardButton(text=tuman, callback_data=f"user_tuman_{tuman}"))
        if i % 2 == 0:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text("👇 Bo'sh ish o'rinlari mavjud tumanni tanlang:", reply_markup=kb)
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data.startswith("user_tuman_"))
async def tuman_selected(callback: types.CallbackQuery, state: FSMContext):
    tuman = callback.data.replace("user_tuman_", "")
    await state.update_data(current_tuman=tuman)

    jobs = vacancies.get(tuman, [])
    
    if not jobs:
        await callback.message.answer("Afsuski, bu tumanda hozircha bo'sh ish o'rni qolmadi.")
        await callback.answer()
        return

    keyboard_buttons = []
    for job in jobs:
        callback_data = f"user_job_{tuman}|{job}"
        keyboard_buttons.append([InlineKeyboardButton(text=job, callback_data=callback_data)])
        
    keyboard_buttons.extend(get_back_buttons("back_to_tuman_selection"))
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text(f"**{tuman}** tumanidagi bo'sh ish o'rinlaridan birini tanlang:", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("user_job_"))
async def job_selected(callback: types.CallbackQuery, state: FSMContext):
    try:
        tuman_job_str = callback.data.replace("user_job_", "")
        tuman, job = tuman_job_str.split("|", 1)
    except ValueError:
        await callback.message.answer("Xatolik yuz berdi. Iltimos, boshidan boshlang (/start).")
        await callback.answer()
        return

    await state.update_data(selected_tuman=tuman, selected_job=job)
    
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"user_tuman_{tuman}"))

    await callback.message.edit_text(
        f"Siz **{tuman}** tumanidagi **{job}** ish o'rnini tanladingiz.\n\n"
        "Iltimos, **F.I.Sh.**'ngizni to'liq kiriting:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_name)
    await callback.answer()

@dp.message(Form.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer("Endi **telefon raqamingizni** yuboring:", reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Form.waiting_for_phone)

@dp.message(Form.waiting_for_phone, F.content_type.in_({"contact", "text"}))
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone)
    
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_name"))
    
    await message.answer(
        "Iltimos, endi **ma'lumotnomangizni PDF fayl** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_reference_file)

@dp.message(Form.waiting_for_reference_file)
async def process_reference_file(message: types.Message, state: FSMContext):
    if not message.document or message.document.mime_type != 'application/pdf':
        kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_phone"))
        await message.answer(
            "⚠️ **Xatolik!** Iltimos, faqat **PDF (.pdf) fayl** yuboring. Boshqa turdagi ma'lumot qabul qilinmaydi.",
            reply_markup=kb
        )
        return
    
    await state.update_data(pdf_file_id=message.document.file_id)
    
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_pdf"))

    await message.answer(
        "Iltimos, **pasport** ma'lumotlarini quyidagi tartibda kiriting:\n\n"
        "**[Kim tomonidan berilgan]**\n"
        "**[Qachongacha amal qiladi (dd.mm.yyyy)]**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_passport_info)

@dp.message(Form.waiting_for_passport_info)
async def process_passport(message: types.Message, state: FSMContext):
    await state.update_data(passport_info=message.text)
    
    data = await state.get_data()
    tuman = data.get("selected_tuman")
    job = data.get("selected_job")
    name = data.get("name")
    phone = data.get("phone")
    passport_info = data.get("passport_info")
    pdf_file_id = data.get("pdf_file_id")

    caption = (
        f"🔔 **Yangi Ariza!**\n\n"
        f"🏢 **Tuman:** {tuman}\n"
        f"💼 **Ish joyi:** {job}\n"
        f"👤 **F.I.Sh.:** {name}\n"
        f"📞 **Telefon:** `{phone}`\n"
        f"📃 **Pasport:** {passport_info}\n\n"
        f"**Ma'lumotnoma (PDF) yuqorida biriktirilgan.**"
    )
    
    await bot.send_document(
        ADMIN_ID,
        pdf_file_id,
        caption=caption,
        parse_mode="Markdown"
    )
    
    await message.answer("✅ Arizangiz va hujjatlaringiz qabul qilindi! **Siz bilan 48 soat ichida admin aloqaga chiqadi.** E'tiboringiz uchun rahmat.", 
                         reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True, one_time_keyboard=True))
    await state.clear()


@dp.callback_query(F.data == "back_to_name")
async def back_to_name(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tuman = data.get("selected_tuman")
    job = data.get("selected_job")
    
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"user_job_{tuman}|{job}")) 

    await callback.message.edit_text(
        "Iltimos, **F.I.Sh.**'ngizni to'liq kiriting:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_name)
    await callback.answer()

@dp.callback_query(F.data == "back_to_phone")
async def back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.edit_text("Endi **telefon raqamingizni** yuboring:", reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Form.waiting_for_phone)
    await callback.answer()

@dp.callback_query(F.data == "back_to_pdf")
async def back_to_pdf(callback: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_phone"))

    await callback.message.edit_text(
        "Iltimos, endi **ma'lumotnomangizni PDF fayl** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_reference_file)
    await callback.answer()


@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("Siz admin emassiz!")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ish joy qo'shish", callback_data="add_job")],
        [InlineKeyboardButton(text="Mavjud ish joylari ro'yxati", callback_data="list_tumans")]
    ])
    await message.answer("Admin paneliga xush kelibsiz:", reply_markup=kb)

@dp.callback_query(F.data == "add_job")
async def add_job(callback: types.CallbackQuery, state: FSMContext):
    keyboard_buttons = []
    row = []
    for i, tuman in enumerate(all_tumans, 1):
        row.append(InlineKeyboardButton(text=tuman, callback_data=f"admin_tuman_{tuman}"))
        if i % 2 == 0:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text("Ish joyi qo'shmoqchi bo'lgan tumanni tanlang:", reply_markup=kb)
    await state.set_state(Form.admin_select_tuman)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_tuman_"))
async def admin_tuman_selected(callback: types.CallbackQuery, state: FSMContext):
    tuman = callback.data.replace("admin_tuman_", "")
    await state.update_data(tuman=tuman)
    await callback.message.edit_text(f"**{tuman}** tumaniga qo'shiladigan **har bir** bog‘cha nomini **alohida SMS** qilib kiriting! (masalan: `2-DMTT` yoki `bosh o'qituvchi`)\n\n"
                                     "Barcha ish joylarini kiritib bo'lgach, /admin buyrug'ini yozing.", parse_mode="Markdown")
    await state.set_state(Form.admin_add_jobs)
    await callback.answer()

@dp.message(Form.admin_add_jobs)
async def admin_add_jobs_message(message: types.Message, state: FSMContext):
    global vacancies
    data = await state.get_data()
    tuman = data.get("tuman")
    
    job_name = message.text.strip()

    if not job_name:
        await message.answer("Ish joyi nomini kiritmadingiz. Qayta urinib ko'ring.")
        return

    if tuman not in vacancies:
        vacancies[tuman] = []
        
    if job_name in vacancies[tuman]:
        await message.answer(f"⚠️ **{tuman}** tumaniga **{job_name}** allaqachon qo'shilgan. Boshqa nom kiriting yoki tugatish uchun /admin yozing.", parse_mode="Markdown")
        return

    vacancies[tuman].append(job_name)
    save_data(vacancies)
    
    await message.answer(f"✅ **{tuman}** tumaniga ish joyi: **{job_name}** muvaffaqiyatli qo‘shildi. Yana bir ish joyi nomini kiriting yoki /admin buyrug'ini yozing.", parse_mode="Markdown")

@dp.callback_query(F.data == "list_tumans")
async def list_tumans(callback: types.CallbackQuery):
    global vacancies
    vacancies = load_data() 

    text = "Tumanlar va mavjud ish joylari ro'yxati:\n\n"
    
    if not vacancies or all(not jobs for jobs in vacancies.values()):
        text = "Hozircha hech qaysi tumanda ish joylari mavjud emas."
    else:
        for tuman in all_tumans:
            jobs = vacancies.get(tuman)
            if jobs:
                text += f"**{tuman}** ({len(jobs)} ta): {', '.join(jobs)}\n"
            else:
                text += f"{tuman}: _Ish joyi yo'q._\n"
                
    await callback.message.edit_text(text, parse_mode="Markdown")
    await callback.answer()

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot)) 

    
