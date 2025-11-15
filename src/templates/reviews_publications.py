REVIEWS_SUMMARY_TEMPLATES = [
# --- Template 1: Dynamic Short Review ---
"""
🔥 <b>{{ title }}</b>

{{ summary }}

<b>Community Sentiment:</b> {{ (sentiment_score * 100) | round(0) }}%

<b>👍 Strengths:</b>
{% for s in strengths %}
• {{ s }}
{% endfor %}

<b>👎 Weaknesses:</b>
{% for w in weaknesses %}
• {{ w }}
{% endfor %}

<b>🛠 Most Requested Improvements:</b>
{% for r in common_requests %}
• {{ r }}
{% endfor %}

<b>💬 Notable Quote:</b>
{% if notable_quotes %}
“{{ notable_quotes[0].quote }}” — <i>{{ notable_quotes[0].author }}</i>
{% endif %}

{% if surprises %}
<b>🤯 Surprises:</b>
{% for s in surprises %}
• {{ s }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

<a href="{{ image }}">&#8205;</a>
{% endif %}
""",

# --- Template 2: Analytical Review ---
"""
🎮 <b>{{ title }}</b>

{{ summary }}

<b>📊 Overall Sentiment:</b> {{ (sentiment_score * 100) | round(0) }}%

<b>🔥 What Players Loved:</b>
{% for s in strengths %}
• {{ s }}
{% endfor %}

<b>⚠️ What Players Criticized:</b>
{% for w in weaknesses %}
• {{ w }}
{% endfor %}

<b>📌 What Players Want:</b>
{% for r in common_requests %}
• {{ r }}
{% endfor %}

<b>💬 Highlighted Community Quotes:</b>
{% for q in notable_quotes %}
• “{{ q.quote }}” — <i>{{ q.author }}</i>
{% endfor %}

{% if surprises %}
<b>🤔 Unexpected Notes:</b>
{% for s in surprises %}
• {{ s }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

<a href="{{ image }}">&#8205;</a>
{% endif %}
""",

# --- Template 3: Editorial Style Review ---
"""
📝 <b>{{ title }}</b>

{{ summary }}

<b>Sentiment Score:</b> <code>{{ (sentiment_score * 100) | round(1) }}%</code>  

<b>🎯 Highlights:</b>
{% for s in strengths %}
• <b>{{ s }}</b>
{% endfor %}

<b>🔻 Issues Players Point Out:</b>
{% for w in weaknesses %}
• {{ w }}
{% endfor %}

<b>✨ Common Player Requests:</b>
{% for r in common_requests %}
• {{ r }}
{% endfor %}

<b>💬 Community Quotes:</b>
{% for q in notable_quotes %}
— “{{ q.quote }}” <i>({{ q.author }})</i>
{% endfor %}

{% if surprises %}
<b>🎲 Surprising Takeaways:</b>
{% for s in surprises %}
• {{ s }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

<a href="{{ image }}">&#8205;</a>
{% endif %}
"""
]
