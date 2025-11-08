REDDIT_MEME_TEMPLATES = [
    # --- Template 1: Классический мем ---
    """
😂 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
#funny #{{ subreddit }}
""",

    # --- Template 2: Мем про геймдев ---
    """
👾 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
#memes #{{ subreddit }}
""",

    # --- Template 3: Мем без заголовка (если title слишком короткий или не нужен) ---
"""
🙈 <b>{{ title }}</b>
<br>
{% if image_url %}
<img src="{{ image_url }}">
<br>
{% endif %}
#gamememes #{{ subreddit }}
"""
]
