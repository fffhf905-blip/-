# -*- coding: utf-8 -*-
# نموذج تطبيق ويب Flask لمعالجة تحديثات Telegram Webhook.
# هذا الملف جاهز للنشر على منصة Render أو ما شابهها.

import os
import json
from flask import Flask, request, jsonify
# في بيئة حقيقية، ستحتاج إلى مكتبات Firebase/Firestore Python SDK
# لكننا سنستخدم هنا محاكاة بسيطة للوظائف والبيانات.

# =======================================================================
# I. تهيئة Firebase والمتغيرات العامة (ضروري)
# يتم توفير هذه المتغيرات تلقائياً من قبل بيئة Canvas
# =======================================================================

# يجب استخدام هذه المتغيرات للوصول إلى قاعدة بيانات Firestore الخاصة بك
try:
    APP_ID = os.environ.get('__app_id', 'default-app-id')
    FIREBASE_CONFIG = json.loads(os.environ.get('__firebase_config', '{}'))
    INITIAL_AUTH_TOKEN = os.environ.get('__initial_auth_token')
except Exception as e:
    print(f"Error loading required environment variables: {e}")
    APP_ID = 'default-app-id'
    FIREBASE_CONFIG = {}
    INITIAL_AUTH_TOKEN = None

# يمكنك هنا تهيئة مكتبة Firebase Python SDK الحقيقية
# (مثلاً: firebase_admin.initialize_app(options=FIREBASE_CONFIG))
# لكننا سنبقي الكود بسيطاً ومحاكياً للمنطق المطلوب.

app = Flask(__name__)

# =======================================================================
# II. ثوابت البوت والرسائل (باللغة العربية)
# =======================================================================

ADMIN_CHAT_ID = "123456789" # يجب استبداله بـ Chat ID للمدير
TELEGRAM_BOT_TOKEN = "8216554417:AAEs3O3y2lYLezGrLliBqXs0zPgpYU9srUg" # الرمز السري لبوتك

MESSAGES = {
    "START": "أهلاً بك! يرجى إرسال المعرّف الخاص بك في برنامج القياسات للربط. استخدم /verify للبدء.",
    "VERIFY_START": "يرجى إرسال المعرّف الخاص بك الآن (Measurement ID).",
    "VERIFY_SUCCESS": "تم ربط حسابك بنجاح! معرّف الربط: {mid}.\nستتلقى الآن تقاريرك.",
    "STATUS_INFO": "حالة حسابك (Chat ID: {uid}):\n- معرّف الربط المسجل: {mid}\n- نوع التقارير: فوري.",
    "STATUS_NO_LINK": "حسابك غير مرتبط بعد. يرجى استخدام الأمر /verify للربط.",
    "ADMIN_AUTH_FAIL": "عذراً، هذا الأمر مخصص للمدير فقط.",
    "ERROR_GENERAL": "حدث خطأ في معالجة طلبك.",
}

# =======================================================================
# III. وظائف قاعدة البيانات (محاكاة)
# في تطبيق حقيقي، سيتم استخدام Firestore SDK هنا
# =======================================================================

# محاكاة لـ "قاعدة بيانات" تخزين الروابط (في الذاكرة فقط لهذا النموذج)
# { "telegram_chat_id": "measurement_id" }
user_links_mock = {}

def get_user_link(user_id):
    """محاكاة لجلب حالة ربط المستخدم من Firestore."""
    return user_links_mock.get(user_id)

def save_user_link(user_id, measurement_id):
    """محاكاة لحفظ رابط المستخدم في Firestore."""
    user_links_mock[user_id] = measurement_id
    print(f"DEBUG: Saved link for {user_id} -> {measurement_id}")
    # في التطبيق الحقيقي، هنا يتم استدعاء setDoc/updateDoc
    pass

def send_telegram_message(chat_id, text):
    """دالة مساعدة لإرسال الرد إلى Telegram API."""
    # يجب استبدال هذا برمز حقيقي لاستدعاء API تليجرام
    # (مثل: requests.post(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage', ...))
    print(f"[TELEGRAM API MOCK] Sending to {chat_id}: {text}")
    return {"ok": True}

# =======================================================================
# IV. مسار Webhook الرئيسي
# =======================================================================

@app.route('/webhook', methods=['POST'])
def webhook():
    """نقطة النهاية التي تستقبل جميع تحديثات تليجرام."""
    try:
        update = request.get_json()
        if not update or 'message' not in update:
            return jsonify({"status": "ignored", "reason": "no message"}), 200

        message = update['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '').strip()
        
        # 1. معالجة الأوامر
        if text.startswith('/'):
            command = text.split()[0].lower()

            if command == '/start' or command == '/help':
                send_telegram_message(chat_id, MESSAGES['START'])

            elif command == '/verify':
                # منطق الـ /verify: نطلب من المستخدم إرسال المعرف
                send_telegram_message(chat_id, MESSAGES['VERIFY_START'])
                # في تطبيق حقيقي، يجب هنا ضبط "حالة" الدردشة لتوقع الرد التالي.
                
            elif command == '/status':
                link_status = get_user_link(chat_id)
                if link_status:
                    response_text = MESSAGES['STATUS_INFO'].format(uid=chat_id, mid=link_status)
                else:
                    response_text = MESSAGES['STATUS_NO_LINK']
                send_telegram_message(chat_id, response_text)

            elif command == '/admin_panel':
                if chat_id == ADMIN_CHAT_ID:
                    send_telegram_message(chat_id, "أهلاً أيها المدير. يمكنك الآن إدارة الروابط والتقارير.")
                else:
                    send_telegram_message(chat_id, MESSAGES['ADMIN_AUTH_FAIL'])
            
            # 2. معالجة الردود (كمحاكاة لاستقبال المعرّف بعد /verify)
        elif not text.startswith('/') and text:
            # نفترض أن أي نص غير أمر هو محاولة لإدخال Measurement ID
            measurement_id = text
            if len(measurement_id) >= 5: # تحقق مبدئي بسيط
                save_user_link(chat_id, measurement_id)
                response_text = MESSAGES['VERIFY_SUCCESS'].format(mid=measurement_id)
                send_telegram_message(chat_id, response_text)
            else:
                # إذا كان الرد غير أمر وليس معرّفاً صالحاً
                pass # تجاهل أو أرسل رسالة غير مفهومة

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"An error occurred in webhook processing: {e}")
        # لا نرد بخطأ 500 لتليجرام لتجنب إعادة الإرسال المتكرر
        return jsonify({"status": "error", "message": str(e)}), 200

# =======================================================================
# V. بدء تشغيل التطبيق (لبيئة التطوير)
# =======================================================================

if __name__ == '__main__':
    # هذه الكتلة لا تعمل على Render، هي فقط للاختبار المحلي
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))

