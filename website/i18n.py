from flask import session
from .models import get_user_language


def get_lang():
    if 'lang' in session:
        return session['lang']

    user_id = session.get('user_id')
    if user_id:
        lang = get_user_language(user_id)
        session['lang'] = lang
        return lang

    return 'ar'


def get_translations(lang):
    if lang == 'en':
        return {
            'app_name': 'EgyLance',
            'hero_title': 'Find trusted Egyptian freelancers and launch your next project',
            'hero_subtitle': 'A secure bilingual marketplace for clients and freelancers across Egypt and the world.',
            'search_placeholder': 'Search for a service like web design, video editing, or content writing',
            'login': 'Login',
            'signup': 'Sign Up',
            'start_now': 'Start Now',
            'dashboard': 'Dashboard',
            'profile': 'Profile',
            'privacy_policy': 'Privacy Policy',
            'terms': 'Terms of Service',
            'verified': 'Verified',
            'services': 'Services',
            'why_us': 'Why Us',
            'how_it_works': 'How It Works',
            'talents': 'Talents',
            'trust': 'Trusted by clients and freelancers',
            'admin_panel': 'Admin Panel',
            'logout': 'Logout',
            'verification': 'Identity Verification',
            'submit_verification': 'Submit Verification',
        }
    return {
        'app_name': 'إيجيلانس',
        'hero_title': 'ابحث عن مستقلين مصريين موثوقين وابدأ مشروعك التالي',
        'hero_subtitle': 'منصة آمنة ثنائية اللغة تربط العملاء بالمستقلين في مصر وفي أنحاء العالم.',
        'search_placeholder': 'ابحث عن خدمة مثل تصميم مواقع، مونتاج فيديو، أو كتابة محتوى',
        'login': 'تسجيل الدخول',
        'signup': 'إنشاء حساب',
        'start_now': 'ابدأ الآن',
        'dashboard': 'لوحة التحكم',
        'profile': 'الملف الشخصي',
        'privacy_policy': 'سياسة الخصوصية',
        'terms': 'شروط الخدمة',
        'verified': 'موثق',
        'services': 'الخدمات',
        'why_us': 'لماذا نحن',
        'how_it_works': 'كيف تعمل',
        'talents': 'المواهب',
        'trust': 'موثوق به من العملاء والمستقلين',
        'admin_panel': 'لوحة الإدارة',
        'logout': 'تسجيل الخروج',
        'verification': 'تحقق الهوية',
        'submit_verification': 'إرسال طلب التحقق',
    }
