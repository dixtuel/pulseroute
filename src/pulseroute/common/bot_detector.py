import re

BOT_PATTERNS = [
    r"bot", r"spider", r"crawl", r"slurp", r"google", r"bing", r"yandex",
    r"baidu", r"duckduck", r"yahoo", r"twitterbot", r"facebookexternalhit",
    r"facebot", r"linkedinbot", r"embedly", r"quora link preview",
    r"showyoubot", r"outbrain", r"pinterest", r"slackbot", r"vkshare",
    r"w3c_validator", r"whatsapp", r"telegrambot", r"discordbot",
    r"applebot", r"pingdom", r"uptimerobot", r"headlesschrome",
]

COMPILED_BOT_REGEX = re.compile("|".join(BOT_PATTERNS), re.IGNORECASE)


def parse_user_agent(user_agent: str) -> tuple[bool, str, str, str]:
    """
    Returns (is_bot: bool, device_type: str, browser: str, os: str)
    """
    if not user_agent:
        return False, "desktop", "Unknown", "Unknown"

    ua_lower = user_agent.lower()
    is_bot = bool(COMPILED_BOT_REGEX.search(ua_lower))

    # Device type
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "tablet"
    else:
        device_type = "desktop"

    # OS
    if "iphone" in ua_lower or "ipad" in ua_lower or "ios" in ua_lower:
        os_name = "iOS"
    elif "android" in ua_lower:
        os_name = "Android"
    elif "mac" in ua_lower:
        os_name = "macOS"
    elif "windows" in ua_lower:
        os_name = "Windows"
    elif "linux" in ua_lower:
        os_name = "Linux"
    else:
        os_name = "Other"

    # Browser
    if "chrome" in ua_lower and "edg" not in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        browser = "Safari"
    elif "firefox" in ua_lower:
        browser = "Firefox"
    elif "edg" in ua_lower:
        browser = "Edge"
    elif "opera" in ua_lower or "opr" in ua_lower:
        browser = "Opera"
    else:
        browser = "Other"

    return is_bot, device_type, browser, os_name
