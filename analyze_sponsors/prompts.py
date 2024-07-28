ANALYZE_OPEN_POSITIONS_PAGE = """Certainly. I'll adapt the system prompt to be specific for careers pages, based on the example you provided earlier. Here's the modified prompt:

Your task is to analyze the provided careers page content and extract key job information into a structured JSON format. Follow these guidelines:

1. Identify all job positions mentioned in the text

2. For each position, extract the following information (where available):
   - Job title
   - Job type (e.g., full-time, part-time, contract)
   - Location

3. Organize the extracted information into a JSON structure with the following format:

```json
{
  "positions": [
    {
      "title": "Job Title",
      "type": "Job Type",
      "location": "Job Location",
    },
    // Additional positions...
  ]
}
```

4. If any information is not explicitly stated for a position, use "N/A" as the value

5. Ensure that the data is accurately represented and properly formatted within the JSON structure

6. The resulting JSON should provide a clear, structured overview of the job positions and their details as presented on the careers page

Remember to focus only on extracting job position information. Do not include general company information, benefits, or other content not directly related to specific job openings
Avoid any explanations
"""
