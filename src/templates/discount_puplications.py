DISCOUNT_POST_TEMPLATES = [
    """
💸 <b>{{ name }}</b> is on SALE!

Now {{ discount_percent }}% off — only {{ price }} 💰
  
({{ original_price }} → {{ price }})

{{ short_description }}

<b>Genres:</b> {{ genres }}

<b>Developed by:</b> {{ developers }}

<b>Platforms:</b> {{ platforms }}
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Grab it on Steam</a>

{% if tags %}
#{{ tags }}
{% endif %}
""",
    """
🔥 Massive discount on <b>{{ name }}</b> — now {{ discount_percent }}% OFF! 🔥

{{ short_description }}

<b>Old price:</b> {{ original_price }}

<b>New price:</b> {{ price }}

<b>Developers:</b> {{ developers }}

<b>Genres:</b> {{ genres }}
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Check it out on Steam</a>

#indiesale #{{ tags }}
"""
]
