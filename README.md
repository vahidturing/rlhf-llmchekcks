
# Fetching LLM checks from RLHF

## Overview

This Python script automates the process of checking and updating Google Sheets with results from a specified URL. It retrieves data from a Google Sheet, processes each row to extract task IDs, and makes API requests to fetch evaluation and prompt checks for those tasks. The results are then updated in specific columns of the Google Sheet.

## Prerequisites

- **Python 3.7+**
- **Google API Credentials**: The script uses Google Sheets API, so you need a service account JSON key file.
- **Required Python Packages**:
  - `concurrent.futures`
  - `gspread`
  - `requests`
  - `tqdm`
  - `oauth2client`

Install the required packages using pip:

```bash
pip install -rm requirements.txt
```

## Script Parameters

The script contains several parameters that you can customize according to your needs:

1. **sheet_url**: The URL of the Google Sheet you want to access.
   - **Default**: `'https://docs.google.com/spreadsheets/d/1HDlTM1csmIWAE6qUQDewdcNulwb6HUmurTGhhaqSBBU/edit?gid=0#gid=0'`
   - **Description**: The script extracts the sheet ID from this URL to identify the correct Google Sheet.

2. **tab_name**: The name of the specific tab within the Google Sheet.
   - **Default**: `'Delivery status'`
   - **Description**: This specifies the sheet tab that contains the data you want to process.

3. **rlhf_link_column**: The column in the Google Sheet that contains the task URLs.
   - **Default**: `'C'`
   - **Description**: This column holds the links to the tasks that the script will process. The task ID is extracted from this URL.

4. **prompt_check_column**: The column where the prompt check results will be stored.
   - **Default**: `'R'`
   - **Description**: This column will be updated with the results of the prompt checks.

5. **evaluation_check_column**: The column where evaluation check results will be stored.
   - **Default**: `'S'`
   - **Description**: This column will be updated with the results of the evaluation checks.

6. **important_checks_column**: The column where important check results will be stored.
   - **Default**: `'T'`
   - **Description**: This column will be updated with any important checks identified in the process.

7. **failed_check_column**: The column where failed check results will be stored.
   - **Default**: `'U'`
   - **Description**: This column will be updated with any failed checks identified during the process.

8. **credentials_file (Optional)**: The path to the Google service account JSON key file.
   - **Default**: `'creds/google__sa.json'`
   - **Description**: This file is required to authenticate with the Google Sheets API.

9. **RLHF_URL**: The API endpoint to send GraphQL queries.
   - **Default**: `'https://rlhf-v3.turing.com/graphql'`
   - **Description**: This is the URL where the API requests are sent to retrieve evaluation and prompt checks.

10. **IMPORTANT_CHECKS**: A list of keywords that define which checks are considered important.
    - **Default**:
      ```python
      [
          'rlhf_prompt__realistic',
          'prompt_detail_level',
          'Evaluationform__has_pleasantries',
          'Evaluationform__is_ideal',
          'rlhf_Evaluationform__realistic'
      ]
      ```
    - **Description**: These keywords are used to filter out important checks from the results.

11. **workers_count**: The number of concurrent workers used to process rows.
    - **Default**: `1`
    - **Description**: Controls the number of threads used for concurrent processing of rows in the Google Sheet.

## Running the Script

1. Update the **parameters** listed above according to your requirements.
2. (Optional) Ensure that the Google API credentials file is correctly placed in the specified path (`creds/google__sa.json` by default).
3. Run the script using Python:

```bash
python main.py
```

The script will connect to the specified Google Sheet, process each row, and update the sheet with the results from the API queries.

## Notes

- The script skips the header row during processing.
- Error handling is implemented for API requests, and the script will retry failed requests up to three times before logging an error and moving on.
- If you encounter issues, check the console output for error messages to diagnose the problem.