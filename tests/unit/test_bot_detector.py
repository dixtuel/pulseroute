from pulseroute.common.bot_detector import parse_user_agent


def test_googlebot_detection():
    ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
    is_bot, device, browser, os_name = parse_user_agent(ua)
    assert is_bot is True


def test_iphone_detection():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
    is_bot, device, browser, os_name = parse_user_agent(ua)
    assert is_bot is False
    assert device == "mobile"
    assert os_name == "iOS"
    assert browser == "Safari"
