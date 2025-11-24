REVIEWS_SUMMARY_TEMPLATES = [
# --- Template 1: Dynamic Short Review ---
"""
🔥 <b>{{ title | safe }}</b>

{{ summary | safe }}

<b>Community Sentiment:</b> {{ (sentiment_score * 100) | round(0) }}%

<b>👍 Strengths:</b>
{% for s in strengths %}
• {{ s | safe }}
{% endfor %}

<b>👎 Weaknesses:</b>
{% for w in weaknesses %}
• {{ w | safe }}
{% endfor %}

<b>🛠 Most Requested Improvements:</b>
{% for r in common_requests %}
• {{ r | safe }}
{% endfor %}

<b>💬 Notable Quote:</b>
{% for q in notable_quotes %}
• “{{ q | safe }}”
{% endfor %}

{% if surprises %}
<b>🤯 Surprises:</b>
{% for s in surprises %}
• {{ s | safe }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

<a href="{{ image }}">&#8205;</a>
{% endif %}

#gamereview #gamecritic
""",

# --- Template 2: Analytical Review ---
"""
🎮 <b>{{ title | safe }}</b>

{{ summary | safe }}

<b>📊 Overall Sentiment:</b> {{ (sentiment_score * 100) | round(0) }}%

<b>🔥 What Players Loved:</b>
{% for s in strengths %}
• {{ s | safe }}
{% endfor %}

<b>⚠️ What Players Criticized:</b>
{% for w in weaknesses %}
• {{ w | safe }}
{% endfor %}

<b>📌 What Players Want:</b>
{% for r in common_requests %}
• {{ r | safe }}
{% endfor %}

<b>💬 Highlighted Community Quotes:</b>
{% for q in notable_quotes %}
• “{{ q | safe }}”
{% endfor %}

{% if surprises %}
<b>🤔 Unexpected Notes:</b>
{% for s in surprises %}
• {{ s | safe }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

#indiereview #indiegamecritic

<a href="{{ image }}">&#8205;</a>
{% endif %}
""",

# --- Template 3: Editorial Style Review ---
"""
📝 <b>{{ title | safe }}</b>

{{ summary | safe }}

<b>Sentiment Score:</b> <code>{{ (sentiment_score * 100) | round(1) }}%</code>  

<b>🎯 Highlights:</b>
{% for s in strengths %}
• <b>{{ s | safe }}</b>
{% endfor %}

<b>🔻 Issues Players Point Out:</b>
{% for w in weaknesses %}
• {{ w | safe }}
{% endfor %}

<b>✨ Common Player Requests:</b>
{% for r in common_requests %}
• {{ r | safe }}
{% endfor %}

<b>💬 Community Quotes:</b>
{% for q in notable_quotes %}
— “{{ q | safe }}”
{% endfor %}

{% if surprises %}
<b>🎲 Surprising Takeaways:</b>
{% for s in surprises %}
• {{ s | safe }}
{% endfor %}
{% endif %}

<a href="https://store.steampowered.com/app/{{ steam_appid }}">Steam</a>
{% if image %}

<a href="{{ image }}">&#8205;</a>
{% endif %}

#indiegamereview #gamesentiment
"""
]
