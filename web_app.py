import json
import requests
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
from flask import Flask, render_template, request, jsonify
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

SOCIAL_MEDIA_LIST = [
    {"url": "https://www.facebook.com/{}", "name": "Facebook"},
    {"url": "https://twitter.com/{}", "name": "Twitter / X"},
    {"url": "https://www.instagram.com/{}", "name": "Instagram"},
    {"url": "https://www.linkedin.com/in/{}", "name": "LinkedIn"},
    {"url": "https://www.github.com/{}", "name": "GitHub"},
    {"url": "https://www.pinterest.com/{}", "name": "Pinterest"},
    {"url": "https://www.tumblr.com/{}", "name": "Tumblr"},
    {"url": "https://www.youtube.com/@{}", "name": "YouTube"},
    {"url": "https://soundcloud.com/{}", "name": "SoundCloud"},
    {"url": "https://www.tiktok.com/@{}", "name": "TikTok"},
    {"url": "https://www.behance.net/{}", "name": "Behance"},
    {"url": "https://medium.com/@{}", "name": "Medium"},
    {"url": "https://www.quora.com/profile/{}", "name": "Quora"},
    {"url": "https://www.flickr.com/people/{}", "name": "Flickr"},
    {"url": "https://www.twitch.tv/{}", "name": "Twitch"},
    {"url": "https://dribbble.com/{}", "name": "Dribbble"},
    {"url": "https://t.me/{}", "name": "Telegram"},
    {"url": "https://www.reddit.com/user/{}", "name": "Reddit"},
    {"url": "https://steamcommunity.com/id/{}", "name": "Steam"}
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/my-ip', methods=['GET'])
def get_my_ip():
    try:
        res = requests.get('https://api.ipify.org?format=json', timeout=5)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/track-ip', methods=['POST'])
def track_ip():
    data = request.get_json() or {}
    ip = data.get('ip', '').strip()
    if not ip:
        return jsonify({"error": "IP 地址不能为空"}), 400

    try:
        res = requests.get(f"http://ipwho.is/{ip}", timeout=8)
        ip_data = res.json()
        if not ip_data.get('success', True):
            return jsonify({"error": ip_data.get('message', '查询 IP 失败')}), 400
        return jsonify(ip_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/track-phone', methods=['POST'])
def track_phone():
    data = request.get_json() or {}
    raw_phone = data.get('phone', '').strip()
    if not raw_phone:
        return jsonify({"error": "电话号码不能为空"}), 400

    try:
        # 兼容未带 + 引导的情况
        formatted_input = raw_phone if raw_phone.startswith('+') else f"+{raw_phone}"
        parsed_number = phonenumbers.parse(formatted_input, None)

        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)
        region_code = phonenumbers.region_code_for_number(parsed_number)
        operator_name = carrier.name_for_number(parsed_number, "zh") or carrier.name_for_number(parsed_number, "en")
        location = geocoder.description_for_number(parsed_number, "zh") or geocoder.description_for_number(parsed_number, "en")
        tz_list = list(timezone.time_zones_for_number(parsed_number))
        number_type_val = phonenumbers.number_type(parsed_number)

        type_mapping = {
            phonenumbers.PhoneNumberType.MOBILE: "移动电话 (Mobile)",
            phonenumbers.PhoneNumberType.FIXED_LINE: "固定电话 (Fixed Line)",
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE: "固话或移动电话",
            phonenumbers.PhoneNumberType.TOLL_FREE: "免费电话 (Toll-Free)",
            phonenumbers.PhoneNumberType.VOIP: "网络电话 (VoIP)",
        }
        number_type_str = type_mapping.get(number_type_val, "其他类型")

        result = {
            "valid": is_valid,
            "possible": is_possible,
            "location": location or "未知",
            "region_code": region_code or "未知",
            "timezone": ", ".join(tz_list) if tz_list else "未知",
            "carrier": operator_name or "未知",
            "type": number_type_str,
            "country_code": parsed_number.country_code,
            "national_number": str(parsed_number.national_number),
            "international_format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "e164_format": phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"解析电话号码失败: {str(e)}"}), 400


def check_single_social(site, username):
    url = site['url'].format(username)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=6, allow_redirects=True)
        # 常见状态码判断：200 通常表示存在
        found = (resp.status_code == 200)
        return {
            "name": site['name'],
            "url": url,
            "status": "Found" if found else "Not Found",
            "code": resp.status_code
        }
    except Exception:
        return {
            "name": site['name'],
            "url": url,
            "status": "Error",
            "code": -1
        }


@app.route('/api/track-username', methods=['POST'])
def track_username():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    if not username:
        return jsonify({"error": "用户名不能为空"}), 400

    # 采用线程池并发加快检测速度
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(check_single_social, site, username) for site in SOCIAL_MEDIA_LIST]
        for f in futures:
            results.append(f.result())

    return jsonify({"username": username, "results": results})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
