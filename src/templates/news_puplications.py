
NEWS_POST_TEMPLATES = [
    # --- Template 1 ---
    """
📰 <b>{{ title }}</b>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
{{ contents }}

<b>Game ID:</b> {{ appid }}  
<b>Source:</b> {{ feedlabel }}  
<b>Author:</b> {{ author }}  
📅 {{ date }}

<a href="{{ url }}">Read full article</a>
#indiegames #news
""",

    # --- Template 2 ---
    """
⚙️ <b>Update News for Steam App #{{ appid }}</b>

{{ title }}  
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
{{ contents }}

<b>Published on:</b> {{ date }}  
<a href="{{ url }}">Read more</a>
#indie #patchnotes
""",

    # --- Template 3 ---
    """
💡 <b>{{ title }}</b>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
{{ contents }}

By {{ author or 'Anonymous' }}  
<a href="{{ url }}">📖 Full story</a>  
#indie #gamingnews
"""
]
