
NEWS_POST_TEMPLATES = [
# --- Template 1 ---
"""
📰 <b>{{ title | safe }}</b>
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ contents | safe }}

<b>Game ID:</b> {{ appid }}
  
<b>Source:</b> {{ feedlabel }}
  
<b>Author:</b> {{ author }}
  
📅 {{ date }}

<a href="{{ url }}">Read full article</a>

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

#indiegames #news
""",

# --- Template 2 ---
"""
⚙️ <b>Update News for Steam App #{{ appid }}</b>

{{ title | safe }}
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ contents | safe }}

<b>Published on:</b> {{ date }}
  
<a href="{{ url }}">Read more</a>

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

#indie #patchnotes
""",

# --- Template 3 ---
"""
💡 <b>{{ title | safe }}</b>
{% if image_url %}
<a href="{{ image_url }}">&#8205;</a>
{% endif %}

{{ contents | safe }}

By {{ author }}
  
<a href="{{ url }}">📖 Full story</a>
  
<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam Page</a>

#indie #gamingnews
"""
]
