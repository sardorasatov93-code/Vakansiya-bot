import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- Konfiguratsiya va Global O'zgaruvchilar ---

# Konfiguratsiya faylini o'qish
# Iltimos, "config.json" fayli mavjudligiga va ichida "token" hamda "admin_id" kalitlari borligiga ishonch hosil qiling.
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print("Xatolik: 'config.json' fayli topilmadi.")
    exit()
except json.JSONDecodeError:
    print("Xatolik: 'config.json' fayli noto'g'ri formatda (JSON).")
    exit()

API_TOKEN = config["token"]
ADMIN_ID = config["admin_id"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- State'lar (Forma bosqichlari) ---

class Form(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    # Hujjat State'lari
    waiting_for_diploma = State() # 1-hujjat: Diplom nusxasi
    waiting_for_reference_letter = State() # 2-hujjat: Ma'lumotnoma
    waiting_for_manager_cert = State() # 3-hujjat: Menejerlik sertifikati
    waiting_for_passport_info = State()
    
    # Admin State'lari
    admin_select_tuman = State()
    admin_add_jobs = State()
    admin_select_tuman_to_clear = State() 

# --- Ma'lumotlarni Yuklash/Saqlash ---

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Agar fayl buzilgan bo'lsa, bo'sh lug'at qaytarish
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Global ish o'rinlari lug'ati
vacancies = load_data() 

# Barcha tumanlar ro'yxati
all_tumans = [ 
    "Arnasoy tumani", "Baxmal tumani", "Do'stlik", "G'allaorol", "Jizzax shahar",
    "Sharof Rashidov", "Zafarobod", "Zarbdor", "Zomin", "Mirzacho'l",
    "Paxtakor", "Forish", "Yangiobod"
] 

# Malaka talablari uchun uzoq matn
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

# Ruxsat etilgan fayl turlari
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/zip',
    'application/x-zip-compressed',
    'application/x-rar-compressed'
]
# --- Umumiy Funksiyalar ---

def get_back_buttons(back_callback=None):
    """Bosh sahifaga va orqaga qaytish tugmalarini yaratadi."""
    buttons = []
    if back_callback:
        buttons.append(InlineKeyboardButton(text="⬅️ Ortga qaytish", callback_data=back_callback))
    
    buttons.append(InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="go_to_start"))
    
    return [buttons]

# --- Foydalanuvchi Qo'llanmalari ---

@dp.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Admin tekshiruvi
    if str(message.from_user.id) == str(ADMIN_ID):
        await message.answer("Salom Admin! Ish joylarini boshqarish uchun /admin yozing.")
        return

    full_start_text = "👋 Salom, siz Jizzax viloyat DMTT bo‘sh ish o‘rinlari bo‘limidasiz.\n\n" + MALAKA_TALABLARI_TEXT
    
    # Bosh menyuga o'tkazish uchun reply klaviaturani yashiramiz
    await message.answer(full_start_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

    # Ish o'rni mavjud tumanlarni topish
    available_tumans = [tuman for tuman, jobs in vacancies.items() if jobs]

    if not available_tumans:
        await message.answer("⚠️ **Hozirda hech qaysi tumanda bo'sh ish o'rinlari mavjud emas!**\nAdmin hali ish joyi qo'shgani yo'q.", parse_mode="Markdown")
        return

    # Tumanlar uchun klaviatura yaratish
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
    """Bosh sahifaga (start) qaytish."""
    # Start funksiyasi edit_text'ni qo'llab-quvvatlamaydi, shuning uchun xabarni o'chirib, yangisini yuboramiz.
    await callback.message.delete()
    await start(callback.message, state)
    await callback.answer()

@dp.callback_query(F.data == "back_to_tuman_selection")
async def back_to_tuman_selection(callback: types.CallbackQuery, state: FSMContext):
    """Tuman tanlash bosqichiga qaytish."""
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
    """Tuman tanlanganda ish o'rinlarini ko'rsatish."""
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
    """Ish o'rni tanlanganda F.I.Sh. ni so'rash."""
    try:
        tuman_job_str = callback.data.replace("user_job_", "")
        tuman, job = tuman_job_str.split("|", 1)
    except ValueError:
        await callback.message.answer("Xatolik yuz berdi. Iltimos, boshidan boshlang (/start).")
        await callback.answer()
        return

    await state.update_data(selected_tuman=tuman, selected_job=job)
    
    # Orqaga qaytish: Tuman ish o'rinlari ro'yxatiga
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
    """F.I.Sh. qabul qilingandan keyin telefon raqamni so'rash."""
    if message.text == "/start":
        await start(message, state)
        return
        
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
    """Telefon raqam qabul qilingandan keyin birinchi hujjatni (Diplom) so'rash."""
    if message.text == "/start":
        await start(message, state)
        return
        
    phone = message.contact.phone_number if message.contact else message.text
    if not phone:
        await message.answer("Telefon raqam aniqlanmadi. Iltimos, 'Telefon raqamni yuborish' tugmasini bosing yoki raqamni to'g'ri kiriting.")
        return
        
    await state.update_data(phone=phone)
    
    # Birinchi hujjatni so'rash (Diplom)
    # Orqaga qaytish: Telefon kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_phone"))
    
    await message.answer(
        "📄 Hujjatlarni yuborish bosqichi:\n\n"
        "1. Iltimos, **diplomingiz nusxasini (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_diploma)

# --- 1. Diplom nusxasini qabul qilish ---
@dp.message(Form.waiting_for_diploma)
async def process_diploma(message: types.Message, state: FSMContext):
    """Diplomni qabul qilish va 2-hujjatni (Ma'lumotnoma) so'rash."""
    if not message.document or message.document.mime_type not in ALLOWED_MIME_TYPES:
        kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_phone"))
        allowed_extensions = ", ".join([mime.split('/')[-1] if '/' in mime else mime for mime in ALLOWED_MIME_TYPES])
        await message.answer(
            f"⚠️ **Xatolik!** Iltimos, faqat **PDF, ZIP yoki RAR** fayl (ruxsat berilgan turlar: `{allowed_extensions}`) yuboring. Boshqa turdagi ma'lumot qabul qilinmaydi.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(diploma_info={
        "file_id": message.document.file_id,
        "file_name": message.document.file_name,
    })
    
    # Ikkinchi hujjatni so'rash (Ma'lumotnoma)
    # Orqaga qaytish: Diplom kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_diploma"))

    await message.answer(
        "2. Diplom qabul qilindi. Endi **ma'lumotnomangizni (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_reference_letter)

# --- 2. Ma'lumotnomani qabul qilish ---
@dp.message(Form.waiting_for_reference_letter)
async def process_reference_letter(message: types.Message, state: FSMContext):
    """Ma'lumotnomani qabul qilish va 3-hujjatni (Sertifikat) so'rash."""
    if not message.document or message.document.mime_type not in ALLOWED_MIME_TYPES:
        kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_diploma"))
        allowed_extensions = ", ".join([mime.split('/')[-1] if '/' in mime else mime for mime in ALLOWED_MIME_TYPES])
        await message.answer(
            f"⚠️ **Xatolik!** Iltimos, faqat **PDF, ZIP yoki RAR** fayl (ruxsat berilgan turlar: `{allowed_extensions}`) yuboring.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(reference_info={
        "file_id": message.document.file_id,
        "file_name": message.document.file_name,
    })
    
    # Uchinchi hujjatni so'rash (Menejerlik sertifikati)
    # Orqaga qaytish: Ma'lumotnoma kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_reference"))

    await message.answer(
        "3. Ma'lumotnoma qabul qilindi. Endi **menejerlik sertifikatingizni (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_manager_cert)

# --- 3. Menejerlik sertifikatini qabul qilish ---
@dp.message(Form.waiting_for_manager_cert)
async def process_manager_cert(message: types.Message, state: FSMContext):
    """Sertifikatni qabul qilish va 4-ma'lumotni (Pasport) so'rash."""
    if not message.document or message.document.mime_type not in ALLOWED_MIME_TYPES:
        kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_reference"))
        allowed_extensions = ", ".join([mime.split('/')[-1] if '/' in mime else mime for mime in ALLOWED_MIME_TYPES])
        await message.answer(
            f"⚠️ **Xatolik!** Iltimos, faqat **PDF, ZIP yoki RAR** fayl (ruxsat berilgan turlar: `{allowed_extensions}`) yuboring.",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(manager_cert_info={
        "file_id": message.document.file_id,
        "file_name": message.document.file_name,
    })
    
    # Pasport ma'lumotlarini so'rash (yakuniy bosqich)
    # Orqaga qaytish: Sertifikat kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_manager_cert"))

    await message.answer(
        "4. Barcha hujjatlar qabul qilindi. Iltimos, **pasport** ma'lumotlarini quyidagi tartibda kiriting:\n\n"
        "**[Kim tomonidan berilgan]**\n"
        "**[Qachongacha amal qiladi (dd.mm.yyyy)]**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_passport_info)

# --- 4. Pasport ma'lumotini qabul qilish va barchasini Admin'ga yuborish ---
@dp.message(Form.waiting_for_passport_info)
async def process_passport(message: types.Message, state: FSMContext):
    """Pasport ma'lumotini qabul qilish, barcha ma'lumotlarni Admin'ga MediaGroup orqali yuborish."""
    if message.text == "/start":
        await start(message, state)
        return
        
    await state.update_data(passport_info=message.text)
    
    data = await state.get_data()
    tuman = data.get("selected_tuman")
    job = data.get("selected_job")
    name = data.get("name")
    phone = data.get("phone")
    passport_info = data.get("passport_info")
    
    diploma_info = data.get("diploma_info")
    reference_info = data.get("reference_info")
    manager_cert_info = data.get("manager_cert_info")
    
    # MediaGroup uchun barcha hujjatlarni tayyorlash
    media_group = [
        types.InputMediaDocument(
            media=diploma_info["file_id"],
            caption=f"📄 **1. Diplom Nusxasi:** `{diploma_info['file_name']}`"
        ),
        types.InputMediaDocument(
            media=reference_info["file_id"],
            caption=f"📃 **2. Ma'lumotnoma:** `{reference_info['file_name']}`"
        ),
        types.InputMediaDocument(
            media=manager_cert_info["file_id"],
            caption=f"🏆 **3. Menejerlik Sertifikati:** `{manager_cert_info['file_name']}`"
        )
    ]

    # Admin'ga yuboriladigan yakuniy matn
    caption = (
        f"🔔 **Yangi Ariza!**\n\n"
        f"🏢 **Tuman:** {tuman}\n"
        f"💼 **Ish joyi:** {job}\n"
        f"👤 **F.I.Sh.:** {name}\n"
        f"📞 **Telefon:** `{phone}`\n"
        f"📃 **Pasport:** {passport_info}\n\n"
        f"**Yuqorida arizachining 3 ta hujjati ketma-ket biriktirilgan.**"
    )
    
    # MediaGroup xabarining caption'i faqat birinchi hujjatga biriktirilishi kerak
    media_group[0].caption = caption
    media_group[0].parse_mode = "Markdown"
    
    try:
        # Hamma hujjatlarni bitta MediaGroup qilib yuboramiz
        await bot.send_media_group(ADMIN_ID, media=media_group)
        
        # Foydalanuvchiga tasdiqlash xabari
        await message.answer("✅ Arizangiz va hujjatlaringiz qabul qilindi! **Siz bilan 48 soat ichida admin aloqaga chiqadi.** E'tiboringiz uchun rahmat.", 
                             reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="/start")]], resize_keyboard=True, one_time_keyboard=True))
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi. Admin xabar yuborishda muammo: {e}. Iltimos, qayta urinib ko'ring yoki admin bilan bog'laning.")
        await state.clear()


# --- Orqaga Qaytish Funksiyalari ---

@dp.callback_query(F.data == "back_to_name")
async def back_to_name(callback: types.CallbackQuery, state: FSMContext):
    """F.I.Sh. kiritish bosqichiga qaytish."""
    data = await state.get_data()
    tuman = data.get("selected_tuman")
    
    # Orqaga qaytish: Ish tanlash bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"user_tuman_{tuman}")) 

    await callback.message.edit_text(
        "Iltimos, **F.I.Sh.**'ngizni to'liq kiriting:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_name)
    await callback.answer()

@dp.callback_query(F.data == "back_to_phone")
async def back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    """Telefon kiritish bosqichiga qaytish."""
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Telefon raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="/start")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.edit_text("Endi **telefon raqamingizni** yuboring:", reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Form.waiting_for_phone)
    await callback.answer()

@dp.callback_query(F.data == "back_to_diploma")
async def back_to_diploma(callback: types.CallbackQuery, state: FSMContext):
    """Diplom kiritish bosqichiga qaytish."""
    # Orqaga qaytish: Telefon kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_phone"))

    await callback.message.edit_text(
        "📄 Hujjatlarni yuborish bosqichi:\n\n"
        "1. Iltimos, **diplomingiz nusxasini (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_diploma)
    await callback.answer()

@dp.callback_query(F.data == "back_to_reference")
async def back_to_reference(callback: types.CallbackQuery, state: FSMContext):
    """Ma'lumotnoma kiritish bosqichiga qaytish."""
    # Orqaga qaytish: Diplom kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_diploma"))

    await callback.message.edit_text(
        "2. Endi **ma'lumotnomangizni (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_reference_letter)
    await callback.answer()

@dp.callback_query(F.data == "back_to_manager_cert")
async def back_to_manager_cert(callback: types.CallbackQuery, state: FSMContext):
    """Menejerlik sertifikati kiritish bosqichiga qaytish."""
    # Orqaga qaytish: Ma'lumotnoma kiritish bosqichiga
    kb = InlineKeyboardMarkup(inline_keyboard=get_back_buttons(f"back_to_reference"))

    await callback.message.edit_text(
        "3. Endi **menejerlik sertifikatingizni (PDF, ZIP yoki RAR fayl)** ko'rinishida yuboring.",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(Form.waiting_for_manager_cert)
    await callback.answer()

# --- Admin Panel Funksiyalari ---

@dp.message(F.text == "/admin")
async def admin_panel(message: types.Message, state: FSMContext):
    """Admin panel menyusini ko'rsatish."""
    if str(message.from_user.id) != str(ADMIN_ID):
        await message.answer("Siz admin emassiz!")
        return
        
    await state.clear() 

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Ish joy qo'shish", callback_data="add_job")],
        [InlineKeyboardButton(text="📜 Mavjud ish joylari ro'yxati", callback_data="list_tumans")],
        [InlineKeyboardButton(text="🗑️ Tuman ish joylarini tozalash", callback_data="clear_tuman_jobs")] 
    ])
    await message.answer("Admin paneliga xush kelibsiz:", reply_markup=kb)

@dp.callback_query(F.data == "add_job")
async def add_job(callback: types.CallbackQuery, state: FSMContext):
    """Ish joyi qo'shish uchun tumanni tanlash."""
    keyboard_buttons = []
    row = []
    for i, tuman in enumerate(all_tumans, 1):
        row.append(InlineKeyboardButton(text=tuman, callback_data=f"admin_tuman_{tuman}"))
        if i % 2 == 0:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)
    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text("Ish joyi qo'shmoqchi bo'lgan tumanni tanlang:", reply_markup=kb)
    await state.set_state(Form.admin_select_tuman)
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_tuman_"))
async def admin_tuman_selected(callback: types.CallbackQuery, state: FSMContext):
    """Tuman tanlanganda ish joyi nomini kiritishni so'rash."""
    tuman = callback.data.replace("admin_tuman_", "")
    await state.update_data(tuman=tuman)
    
    back_button = [[InlineKeyboardButton(text="⬅️ Tuman tanlash", callback_data="add_job")]] 
    kb = InlineKeyboardMarkup(inline_keyboard=back_button)

    await callback.message.edit_text(f"**{tuman}** tumaniga qo'shiladigan **har bir** bog‘cha nomini **alohida SMS** qilib kiriting! (masalan: `2-DMTT` yoki `bosh o'qituvchi`)\n\n"
                                     "Barcha ish joylarini kiritib bo'lgach, /admin buyrug'ini yozing.", reply_markup=kb, parse_mode="Markdown")
    await state.set_state(Form.admin_add_jobs)
    await callback.answer()

@dp.message(Form.admin_add_jobs)
async def admin_add_jobs_message(message: types.Message, state: FSMContext):
    """Admin kiritgan ish joylarini saqlash."""
    if message.text == "/admin":
        await admin_panel(message, state)
        return
        
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
    """Mavjud barcha ish joylarini ro'yxatini ko'rsatish."""
    global vacancies
    vacancies = load_data() 

    text = "Tumanlar va mavjud ish joylari ro'yxati:\n\n"
    
    if not vacancies or all(not jobs for jobs in vacancies.values()):
        text = "Hozircha hech qaysi tumanda ish joylari mavjud emas."
    else:
        for tuman in all_tumans:
            jobs = vacancies.get(tuman)
            if jobs:
                # Ish joylarini alifbo tartibida saralash
                jobs_list = "\n * " + "\n * ".join(sorted(jobs))
                text += f"**{tuman}** ({len(jobs)} ta):{jobs_list}\n"
            else:
                text += f"**{tuman}**: _Ish joyi yo'q._\n"
                
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")]
    ])
    
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "go_to_admin_panel")
async def go_to_admin_panel_handler(callback: types.CallbackQuery, state: FSMContext):
    """Admin paneliga qaytish uchun tugma ishlashi."""
    # callback.message.edit_text uchun yangi xabar yuborish o'rniga, mavjud xabarni o'chirmasdan menyuni yangilaymiz.
    await admin_panel(callback.message, state)
    await callback.answer()
    
@dp.callback_query(F.data == "clear_tuman_jobs")
async def clear_tuman_jobs_selection(callback: types.CallbackQuery, state: FSMContext):
    """Ish joylarini tozalash uchun tuman tanlash."""
    global vacancies
    vacancies = load_data()
    
    available_tumans = [tuman for tuman, jobs in vacancies.items() if jobs]

    if not available_tumans:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")]
        ])
        await callback.message.edit_text("Hozircha hech qaysi tumanda ish joylari mavjud emas. Tozalash uchun ma'lumot yo'q.", reply_markup=kb)
        await callback.answer()
        return

    keyboard_buttons = []
    row = []
    for i, tuman in enumerate(available_tumans, 1):
        row.append(InlineKeyboardButton(text=f"🗑️ {tuman}", callback_data=f"confirm_clear_{tuman}"))
        if i % 2 == 0:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)

    keyboard_buttons.append([InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")])
    
    kb = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await callback.message.edit_text("Ish joylarini tozalash (o'chirish) uchun tumanni tanlang:", reply_markup=kb)
    await state.set_state(Form.admin_select_tuman_to_clear) 
    await callback.answer()

@dp.callback_query(F.data.startswith("confirm_clear_"), Form.admin_select_tuman_to_clear)
async def confirm_clear_tuman_jobs(callback: types.CallbackQuery, state: FSMContext):
    """Ish joylarini tozalashni tasdiqlash."""
    tuman = callback.data.replace("confirm_clear_", "")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Ha, tozalash", callback_data=f"do_clear_{tuman}")],
        [InlineKeyboardButton(text="❌ Yo'q, qaytish", callback_data="clear_tuman_jobs")] 
    ])

    await callback.message.edit_text(f"⚠️ **DIQQAT!** Siz **{tuman}** tumanidagi barcha ({len(vacancies.get(tuman, []))} ta) ish joylarini **butunlay o'chirmoqchisiz**.\n\n"
                                     "Tasdiqlaysizmi?", reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@dp.callback_query(F.data.startswith("do_clear_"))
async def do_clear_tuman_jobs(callback: types.CallbackQuery, state: FSMContext):
    """Tanlangan tuman ish joylarini o'chirish."""
    global vacancies
    tuman = callback.data.replace("do_clear_", "")

    if tuman in vacancies:
        cleared_jobs_count = len(vacancies[tuman])
        vacancies[tuman] = [] 
        save_data(vacancies)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")]
        ])
        
        await callback.message.edit_text(f"✅ **{tuman}** tumanidan **{cleared_jobs_count}** ta ish joyi muvaffaqiyatli tozalandi.", reply_markup=kb, parse_mode="Markdown")
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Admin Panel", callback_data="go_to_admin_panel")]
        ])
        await callback.message.edit_text(f"⚠️ **{tuman}** tumanida tozalash uchun ish joylari topilmadi.", reply_markup=kb, parse_mode="Markdown")

    await state.clear()
    await callback.answer()


if __name__ == "__main__":
    # Botni ishga tushirish
    # Ishga tushirishdan oldin "config.json" mavjudligiga va token to'g'riligiga ishonch hosil qiling.
    asyncio.run(dp.start_polling(bot))
