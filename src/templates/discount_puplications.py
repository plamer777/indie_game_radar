DISCOUNT_POST_TEMPLATES = [
    """
💸 <b>{{ name }}</b> is on SALE!
<br>
Now {{ discount_percent }}% off — only {{ price }} 💰
<br>  
({{ original_price }} → {{ price }})
<br>
{{ short_description }}
<br>
<b>Genres:</b> {{ genres }}
<br>
<b>Developed by:</b> {{ developers }}
<br>
<b>Platforms:</b> {{ platforms }}
<br>
{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}
<br>
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Grab it on Steam</a>
<br>
{% if tags %}
#{{ tags }}
{% endif %}
""",
    """
🔥 Massive discount on <b>{{ name }}</b> — now {{ discount_percent }}% OFF! 🔥
<br>
{{ short_description }}
<br>
<b>Old price:</b> {{ original_price }}
<br>
<b>New price:</b> {{ price }}
<br>
<b>Developers:</b> {{ developers }}
<br>
<b>Genres:</b> {{ genres }}
<br>
{% if image_url %}
<a href="https://store.steampowered.com/app/{{ steam_appid }}"><img src="{{ image_url }}"></a>
{% endif %}
<br>
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Check it out on Steam</a>
<br>
#indiesale #{{ tags }}
"""
]
