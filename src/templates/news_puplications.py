
NEWS_POST_TEMPLATES = [
    # --- Template 1 ---
    """
📰 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
<br>
{{ contents }}
<br>
<b>Game ID:</b> {{ appid }}
<br>  
<b>Source:</b> {{ feedlabel }}
<br>  
<b>Author:</b> {{ author }}
<br>  
📅 {{ date }}
<br>
<a href="{{ url }}">Read full article</a>
<br>
#indiegames #news
""",

    # --- Template 2 ---
    """
⚙️ <b>Update News for Steam App #{{ appid }}</b>
<br>
{{ title }}
<br>  
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
<br>
{{ contents }}
<br>
<b>Published on:</b> {{ date }}
<br>  
<a href="{{ url }}">Read more</a>
<br>
#indie #patchnotes
""",

    # --- Template 3 ---
    """
💡 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
{% endif %}
<br>
{{ contents }}
<br>
By {{ author }}
<br>  
<a href="{{ url }}">📖 Full story</a>
<br>  
#indie #gamingnews
"""
]
