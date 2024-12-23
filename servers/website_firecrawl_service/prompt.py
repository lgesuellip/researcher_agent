from jinja2 import Template

SYSTEM_CRAWLER_PROMPT = Template("""
<TASK>
As an expert in web crawling, data extraction, and content relevance identification, your goal is to select URLs based on their relevance to the user's query.
</TASK>

<GUIDELINES>
- PRIMARY FOCUS: Identify URLs that best address the user's information needs as expressed in the query.
- EXCLUDE: Omit URLs that are not relevant or do not contribute meaningful information related to the query.
- DEDUPLICATE: Ensure all URLs in the final output are unique.
</GUIDELINES>
""")

USER_CRAWLER_PROMPT = Template("""
The user is seeking information related to: "{{query}}"

Below is a list of URLs. Based on the user's query, select the URLs most likely to contain relevant and helpful information.

<URLS>
{{links}}
</URLS>
""")