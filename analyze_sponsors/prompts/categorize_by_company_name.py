PROMPT = """Given the following list of company names, please categorize each company's suggested services or products based on their names. Use only the following categories:

1. Finance & Banking
2. Technology & Software
3. Healthcare & Medical
4. Education & Training
5. Retail & Consumer Goods
6. Food & Beverage
7. Real Estate & Property
8. Legal Services
9. Manufacturing & Industrial
10. Media & Entertainment
11. Transportation & Logistics
12. Energy & Utilities
13. Construction & Engineering
14. Professional Services
15. Other (for companies that don't fit the above categories)

Return the results as a single-line minified JSON array where each object has a single field named with the company name and it's value is the category. Here's an example of the desired format:

[{"Ace Training Limited": "Education & Training"},{"British Heart Foundation": "Healthcare & Medical"}]

Avoid any explanations"""