PROMPT = """You are a business development expert
Given the following company names and their domain, provide an estimate for the probability they employ software engineers
Return the results as a single-line minified JSON array where each object has a single field named after the company name and a number between 0 and 100 representing the probability. Here's an example of the desired format:

[{"1 ACE TRAINING LIMITED": 20},{"1 ALS LIMITED": 10}]

Avoid any explanations"""