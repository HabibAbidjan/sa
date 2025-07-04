# === TO'LIQ ISHLAYDIGAN TELEGRAM GAME BOT KODI ===
# O'yinlar: Mines, Aviator, Dice
# Tugmalar: balans, hisob toldirish, pul chiqarish, bonus, referal

from keep_alive import keep_alive
import telebot
from telebot import types
import random
import threading
import time
import datetime

TOKEN = "8161107014:AAH1I0srDbneOppDw4AsE2kEYtNtk7CRjOw"
bot = telebot.TeleBot(TOKEN)

user_balances = {}
addbal_state = {}
user_games = {}
user_aviator = {}
user_bonus_state = {}
withdraw_sessions = {}
ADMIN_ID = 5815294733

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_balances.setdefault(user_id, 3000)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('💣 Play Mines', '🛩 Play Aviator')
    markup.add('🎲 Play Dice', '💰 Balance')
    markup.add('💸 Pul chiqarish', '💳 Hisob toldirish')
    markup.add('🎁 Kunlik bonus', '👥 Referal link')
    bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def show_balance(message):
    user_id = message.from_user.id
    bal = user_balances.get(user_id, 0)
    bot.send_message(message.chat.id, f"💰 Sizning balansingiz: {bal} so‘m")


@bot.message_handler(commands=['addbal'])
def addbal_start(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ Bu buyruq faqat admin uchun.")
        return
    msg = bot.send_message(message.chat.id, "🆔 Foydalanuvchi ID raqamini kiriting:")
    bot.register_next_step_handler(msg, addbal_get_id)

def addbal_get_id(message):
    try:
        target_id = int(message.text)
        addbal_state[message.from_user.id] = {'target_id': target_id}
        msg = bot.send_message(message.chat.id, "💵 Qo‘shiladigan miqdorni kiriting:")
        bot.register_next_step_handler(msg, addbal_get_amount)
    except:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri ID. Son kiriting.")

def addbal_get_amount(message):
    try:
        amount = int(message.text)
        admin_id = message.from_user.id
        data = addbal_state.get(admin_id)
        if not data:
            bot.send_message(message.chat.id, "❌ Jarayon topilmadi.")
            return
        target_id = data['target_id']
        user_balances[target_id] = user_balances.get(target_id, 0) + amount
        bot.send_message(message.chat.id, f"✅ {target_id} foydalanuvchiga {amount} so‘m qo‘shildi.")
        if admin_id in addbal_state:
            del addbal_state[admin_id]
    except:
        bot.send_message(message.chat.id, "❌ Miqdor noto‘g‘ri.")


@bot.message_handler(func=lambda m: m.text == "👥 Referal link")
def referal_link(message):
    uid = message.from_user.id
    username = bot.get_me().username
    link = f"https://t.me/{username}?start={uid}"
    bot.send_message(message.chat.id, f"👥 Referal linkingiz:\n{link}")

@bot.message_handler(func=lambda m: m.text == "💳 Hisob toldirish")
def deposit(message):
    bot.send_message(message.chat.id, "💳 Hisob to‘ldirish uchun adminga yozing: @for_X_bott")

@bot.message_handler(func=lambda m: m.text == "💸 Pul chiqarish")
def withdraw_step1(message):
    msg = bot.send_message(message.chat.id, "💵 Miqdorni kiriting (min 20000 so‘m):")
    bot.register_next_step_handler(msg, withdraw_step2)

def withdraw_step2(message):
    try:
        amount = int(message.text)
        user_id = message.from_user.id
        if amount < 20000:
            bot.send_message(message.chat.id, "❌ Minimal chiqarish miqdori 20000 so‘m.")
            return
        if user_balances.get(user_id, 0) < amount:
            bot.send_message(message.chat.id, "❌ Mablag‘ yetarli emas.")
            return
        withdraw_sessions[user_id] = amount
        msg = bot.send_message(message.chat.id, "💳 Karta yoki to‘lov usulini yozing:")
        bot.register_next_step_handler(msg, withdraw_step3)
    except:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri miqdor.")

# === SHU YERGA QO‘Y — withdraw_step3 ===
def withdraw_step3(message):
    user_id = message.from_user.id
    amount = withdraw_sessions.get(user_id)
    info = message.text.strip()

    # === Karta yoki to‘lov tizimi tekshiruvlari ===
    valid = False
    digits = ''.join(filter(str.isdigit, info))
    if len(digits) in [16, 19] and (digits.startswith('8600') or digits.startswith('9860') or digits.startswith('9989')):
        valid = True
    elif any(x in info.lower() for x in ['click', 'payme', 'uzcard', 'humo', 'apelsin']):
        valid = True

    if not valid:
        bot.send_message(message.chat.id, "❌ To‘lov usuli noto‘g‘ri kiritildi. Karta raqami (8600...) yoki servis nomini kiriting.")
        return

    user_balances[user_id] -= amount
    text = f"🔔 Yangi pul chiqarish so‘rovi!\n👤 @{message.from_user.username or 'no_username'}\n🆔 ID: {user_id}\n💵 Miqdor: {amount} so‘m\n💳 To‘lov: {info}"
    bot.send_message(ADMIN_ID, text)
    bot.send_message(message.chat.id, "✅ So‘rov yuborildi, kuting.")
    del withdraw_sessions[user_id]


@bot.message_handler(func=lambda m: m.text == "🎁 Kunlik bonus")
def daily_bonus(message):
    user_id = message.from_user.id
    today = datetime.date.today()
    if user_bonus_state.get(user_id) == today:
        bot.send_message(message.chat.id, "🎁 Siz bugun bonus oldingiz.")
        return
    bonus = random.randint(1000, 5000)
    user_balances[user_id] = user_balances.get(user_id, 0) + bonus
    user_bonus_state[user_id] = today
    bot.send_message(message.chat.id, f"🎉 Sizga {bonus} so‘m bonus berildi!")

@bot.message_handler(func=lambda m: m.text == "🎲 Play Dice")
def dice_start(message):
    msg = bot.send_message(message.chat.id, "🎯 Stavka miqdorini kiriting:")
    bot.register_next_step_handler(msg, dice_process)

def dice_process(message):
    try:
        user_id = message.from_user.id
        stake = int(message.text)
        if user_balances.get(user_id, 0) < stake:
            bot.send_message(message.chat.id, "❌ Mablag‘ yetarli emas.")
            return
        user_balances[user_id] -= stake
        bot.send_message(message.chat.id, "🎲 Qaytarilmoqda...")
        time.sleep(2)
        dice = random.randint(1, 6)
        if dice <= 2:
            win = 0
        elif dice <= 4:
            win = stake
        else:
            win = stake * 2
        user_balances[user_id] += win
        bot.send_dice(message.chat.id)
        time.sleep(3)
        bot.send_message(message.chat.id, f"🎲 Natija: {dice}\n{'✅ Yutdingiz!' if win > stake else '❌ Yutqazdingiz.'}\n💵 Yutuq: {win} so‘m")
    except:
        bot.send_message(message.chat.id, "❌ Noto‘g‘ri stavka.")

# === MINES o'yini funksiyasi ===
@bot.message_handler(func=lambda m: m.text == "💣 Play Mines")
def play_mines(message):
    user_id = message.from_user.id
    if user_balances.get(user_id, 0) < 1000:
        bot.send_message(message.chat.id, "❌ Kamida 1000 so‘m kerak.")
        return
    stake = 1000
    user_balances[user_id] -= stake
    bombs = random.sample(range(25), 3)
    user_games[user_id] = {
        'stake': stake,
        'bombs': bombs,
        'opened': [],
        'multiplier': 1.0
    }
    send_mines_board(message.chat.id, user_id, bomb_triggered=False)

def send_mines_board(chat_id, user_id, bomb_triggered):
    game = user_games[user_id]
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = []

    for i in range(25):
        if i in game['opened']:
            emoji = "💣" if i in game['bombs'] else "✅"
        else:
            emoji = "⬜"
        buttons.append(types.InlineKeyboardButton(emoji, callback_data=f"open_{i}"))

    # 5x5 ko‘rinishda joylash
    for i in range(0, 25, 5):
        markup.row(*buttons[i:i+5])

    if not bomb_triggered:
        markup.add(types.InlineKeyboardButton("💸 Cash Out", callback_data="cashout"))

    text = f"""💣 <b>MINES O'yini</b>
🔢 Bombalar: 3
💰 Stavka: {game['stake']} so‘m
📈 Multiplikator: x{round(game['multiplier'], 2)}"""
    
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("open_") or call.data == "cashout")
def handle_mines_callback(call):
    user_id = call.from_user.id
    if user_id not in user_games:
        bot.answer_callback_query(call.id, "⛔ O‘yin topilmadi.")
        return

    game = user_games[user_id]

    if call.data == "cashout":
        win = min(int(game['stake'] * game['multiplier']), int(game['stake'] * 2))
        user_balances[user_id] += win
        del user_games[user_id]
        bot.edit_message_text(f"✅ {win} so‘m yutdingiz! Tabriklaymiz!", call.message.chat.id, call.message.message_id)
        return

    idx = int(call.data.split("_")[1])
    if idx in game['opened']:
        bot.answer_callback_query(call.id, "Bu katak allaqachon ochilgan.")
        return

    if idx in game['bombs']:
        game['opened'] = list(set(game['opened'] + game['bombs']))
        send_mines_board(call.message.chat.id, user_id, bomb_triggered=True)
        del user_games[user_id]
        bot.edit_message_text("💥 Bomba topildi! Siz yutqazdingiz.", call.message.chat.id, call.message.message_id)
        return

    game['opened'].append(idx)
    game['multiplier'] *= 1.08
    send_mines_board(call.message.chat.id, user_id, bomb_triggered=False)


# === AVIATOR o'yini funksiyasi ===
@bot.message_handler(func=lambda m: m.text == "🛩 Play Aviator")
def play_aviator(message):
    user_id = message.from_user.id
    if user_id in user_aviator:
        bot.send_message(message.chat.id, "⏳ Avvalgi Aviator o‘yini tugamagani uchun kuting.")
        return
    msg = bot.send_message(message.chat.id, "🎯 Stavka miqdorini kiriting (min 1000 so‘m):")
    bot.register_next_step_handler(msg, process_aviator_stake)

def process_aviator_stake(message):
    try:
        user_id = message.from_user.id
        stake = int(message.text)
        if stake < 1000:
            bot.send_message(message.chat.id, "❌ Minimal stavka 1000 so‘m.")
            return
        if user_balances.get(user_id, 0) < stake:
            bot.send_message(message.chat.id, "❌ Yetarli balans yo‘q.")
            return
        user_balances[user_id] -= stake
        user_aviator[user_id] = {
            'stake': stake,
            'multiplier': 1.0,
            'chat_id': message.chat.id,
            'message_id': None,
            'stopped': False
        }
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛑 STOP", callback_data="aviator_stop"))
        msg = bot.send_message(message.chat.id, f"🛫 Boshlanmoqda... x1.00", reply_markup=markup)
        user_aviator[user_id]['message_id'] = msg.message_id
        threading.Thread(target=run_aviator_game, args=(user_id,)).start()
    except:
        bot.send_message(message.chat.id, "❌ Xatolik. Raqam kiriting.")

def run_aviator_game(user_id):
    data = user_aviator.get(user_id)
    if not data:
        return
    chat_id = data['chat_id']
    message_id = data['message_id']
    stake = data['stake']
    multiplier = data['multiplier']
    for _ in range(30):
        if user_aviator.get(user_id, {}).get('stopped'):
            win = int(stake * multiplier)
            user_balances[user_id] += win
            bot.edit_message_text(f"🛑 To‘xtatildi: x{multiplier}\n✅ Yutuq: {win} so‘m", chat_id, message_id)
            del user_aviator[user_id]
            return
        time.sleep(1)
        multiplier = round(multiplier + random.uniform(0.15, 0.4), 2)
        chance = random.random()
        if (multiplier <= 1.6 and chance < 0.3) or (1.6 < multiplier <= 2.4 and chance < 0.15) or (multiplier > 2.4 and chance < 0.1):
            bot.edit_message_text(f"💥 Portladi: x{multiplier}\n❌ Siz yutqazdingiz.", chat_id, message_id)
            del user_aviator[user_id]
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🛑 STOP", callback_data="aviator_stop"))
        try:
            bot.edit_message_text(f"🛩 Ko‘tarilmoqda... x{multiplier}", chat_id, message_id, reply_markup=markup)
        except:
            pass
        user_aviator[user_id]['multiplier'] = multiplier

@bot.callback_query_handler(func=lambda call: call.data == "aviator_stop")
def aviator_stop(call):
    user_id = call.from_user.id
    if user_id in user_aviator:
        user_aviator[user_id]['stopped'] = True
        bot.answer_callback_query(call.id, "🛑 O'yin to'xtatildi, pulingiz qaytarildi.")

print("Bot ishga tushdi...")
keep_alive()
bot.polling(none_stop=True)
