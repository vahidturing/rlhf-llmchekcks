import concurrent.futures
import json
from urllib.parse import urlparse
import gspread
import requests
from tqdm import tqdm
from oauth2client.service_account import ServiceAccountCredentials


def alphabetic_index(letter):
    letter = letter.upper()

    index = ord(letter) - ord('A')

    return index


def get_worksheet(credentials_file, sheet_url, tab_name):
    sheet_id = sheet_url.split('/d/')[1].split('/')[0]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(tab_name)
    return worksheet


def extract_task_id(url):
    parsed_url = urlparse(url)
    return parsed_url.path.split('/')[-1]


def send_request(message):
    message = message.replace('\n', '')
    headers = {'content-type': 'application/json'}
    return requests.post(RLHF_URL, headers=headers, data=message)


def get_llm_checks(id, type):
    query = {"variables": {
        "checkPartId": int(id),
        "checkPartType": type
    },
        "operationName": "GetLLMChecksResult",
        "query": "query GetLLMChecksResult($checkPartType: CheckedPartsType!, $checkPartId: Int!) {\n  getLLMChecksResult(checkPartType: $checkPartType, checkPartId: $checkPartId) {\n...LLMCheckBaseFields\n    feedbacks {\n...LLMCheckFeedbackBaseFields\n      __typename\n}\n    __typename\n}\n}\n\nfragment LLMCheckBaseFields on LLMCheck {\n  id\n  checkPartType\n  status\n  runId\n  resultJson\n  checkPartId\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment LLMCheckFeedbackBaseFields on LLMChecksFeedback {\n  id\n  llmCheckId\n  qualityDimension\n  thumbScore\n  feedback\n  createdAt\n  updatedAt\n  __typename\n}"
    }

    res = send_request(json.dumps(query))
    if res.status_code != 200:
        raise Exception(f"Failed to get LLM checks for {id} of type {type}\nStatus: {res.status_code}\n{res.text}")

    return json.loads(res.text)


def three_retry(func):
    def wrapper(*args, **kwargs):
        for i in range(3):
            result = func(*args, **kwargs)
            if result:
                return result

        return result

    return wrapper


@three_retry
def create_checks_string(turn_id, type):
    try:
        result = ""

        checks = get_llm_checks(turn_id, type)
        evaluations = (checks
                       .get("data", {})
                       .get("getLLMChecksResult", {})
                       .get("resultJson", {})
                       .get("result", {})
                       .get("evaluations", []))
        for e in evaluations:
            status = str.lower(e.get("output", {}).get("evaluation_result"))
            result += f"{e.get("name", "NO_NAME")}: {status}\n"

        return result
    except Exception as e:
        print(f"Failed to get checks for {turn_id} of type {type} with error: {e}")
        return ""


def get_lines_containing(input_string, word_list):
    lines = input_string.splitlines()

    matching_lines = [
        line for line in lines
        if any(word in line for word in word_list)
    ]

    result = "\n".join(matching_lines)
    if result:
        result += "\n"

    return result


def create_task_check_string(task_id):
    query = {
        "variables": {"id": task_id},
        "operationName": "GetPrompt",
        "query": "query GetPrompt($id: ID!) {\n  prompt(idOrUuid: $id) {\n    ...PromptBaseFields\n    feedback\n    genericTextLLMChecks {\n      ...GenericTextLLMCheckBaseFields\n      __typename\n    }\n    promptTurns {\n      ...PromptTurnBaseFields\n      promptResponses {\n        ...PromptResponseBaseFields\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ReviewCriteriaBaseFields on ReviewCriteria {\n  key\n  name\n  description\n  type\n  displayCondition\n  options {\n    name\n    value\n    __typename\n  }\n  llmCheckEnabled\n  __typename\n}\n\nfragment PromptTurnUploadedFilesBaseFields on PromptTurnUploadedFile {\n  id\n  filename\n  gcsPath\n  mimeType\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptResponseClaimBaseFields on PromptResponseClaim {\n  id\n  claim\n  createdAt\n  updatedAt\n  feedback\n  claimIndex\n  __typename\n}\n\nfragment PromptResponseSearchContextBaseFields on PromptResponseSearchContext {\n  id\n  promptResponseId\n  type\n  feedback\n  article\n  searchContextUUID\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptBaseFields on Prompt {\n  id\n  uuid\n  status\n  modelConfig\n  qualityDimensions {\n    systemName\n    qualityGuidelines\n    qualityEvaluationRules\n    checkedPart\n    __typename\n  }\n  reviewCriteria {\n    ...ReviewCriteriaBaseFields\n    __typename\n  }\n  createdAt\n  updatedAt\n  metadata\n  config\n  type\n  __typename\n}\n\nfragment GenericTextLLMCheckBaseFields on GenericTextLLMCheck {\n  id\n  status\n  text\n  runId\n  result\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptTurnBaseFields on PromptTurn {\n  id\n  prompt\n  createdAt\n  updatedAt\n  promptIndex\n  groupIndex\n  tags\n  parentId\n  feedback\n  promptEvaluationFeedback\n  preferenceJustification\n  preferenceSignal\n  customTitle\n  uploadedFiles {\n    ...PromptTurnUploadedFilesBaseFields\n    __typename\n  }\n  idealResponse\n  idealResponseAsPreferred\n  idealResponseLLMReviewStatus\n  idealResponseLLMReviewPayload\n  unratable\n  isToolTurn\n  __typename\n}\n\nfragment PromptResponseBaseFields on PromptResponse {\n  id\n  claims {\n    ...PromptResponseClaimBaseFields\n    __typename\n  }\n  searchContexts {\n    ...PromptResponseSearchContextBaseFields\n    __typename\n  }\n  searchContextPayload {\n    id\n    searchResult\n    searchQuery\n    type\n    __typename\n  }\n  response\n  toolCalls\n  model\n  temperature\n  feedback\n  chosenToContinue\n  createdAt\n  updatedAt\n  promptTurnId\n  llmReviewPayload\n  llmReviewStatus\n  tags\n  overallWebRagFeedback\n  overallXRagFeedback\n  __typename\n}"
    }
    response = send_request(json.dumps(query))
    response_data = json.loads(response.text)
    turns = response_data["data"]["prompt"]["promptTurns"]
    prompt_check_string = ""
    evaluation_check_string = ""
    failed_checks = ""
    important_checks = ""
    for turn in turns:
        new_important_checks = ""
        turn_id = turn["id"]
        prompt_index = turn["promptIndex"]

        turn_title = f"## Turn {prompt_index + 1}\n"
        prompt_check_string += turn_title
        evaluation_check_string += turn_title
        failed_checks += turn_title
        failed_checks += turn_title

        turn_prompt_check_string = create_checks_string(turn_id, "PROMPT")
        failed_checks += get_lines_containing(turn_prompt_check_string, ['fail'])
        new_important_checks += get_lines_containing(turn_prompt_check_string, IMPORTANT_CHECKS)
        prompt_check_string += turn_prompt_check_string

        for i, response in enumerate(turn["promptResponses"]):
            evaluation_check_string += f"### Model {i + 1}\n"
            turn_evaluation_check_string = create_checks_string(response["id"], "EVALUATION_FORM")
            failed_checks += get_lines_containing(turn_evaluation_check_string, ['fail'])
            new_important_checks += get_lines_containing(turn_evaluation_check_string, IMPORTANT_CHECKS)
            evaluation_check_string += turn_evaluation_check_string

        if new_important_checks:
            important_checks += turn_title
            important_checks += new_important_checks

    return prompt_check_string, evaluation_check_string, important_checks, failed_checks


def process_row(i, row, worksheet):
    # Skip the header row
    if i == 0:
        return None

    task_id = extract_task_id(row[alphabetic_index(rlhf_link_column)])
    print(f"Processing task {task_id}")
    prompt_check_string, evaluation_check_string, important_checks_string, failed_check_string = create_task_check_string(task_id)

    worksheet.update_cell(i + 1, alphabetic_index(prompt_check_column) + 1, prompt_check_string)
    worksheet.update_cell(i + 1, alphabetic_index(evaluation_check_column) + 1, evaluation_check_string)
    worksheet.update_cell(i + 1, alphabetic_index(important_checks_column) + 1, important_checks_string)
    worksheet.update_cell(i + 1, alphabetic_index(failed_check_column) + 1, failed_check_string)

    return i

if __name__ == '__main__':
    sheet_url = 'https://docs.google.com/spreadsheets/d/1HDlTM1csmIWAE6qUQDewdcNulwb6HUmurTGhhaqSBBU/edit?gid=0#gid=0'
    tab_name = 'Delivery status'
    rlhf_link_column = 'C'
    prompt_check_column = 'R'
    evaluation_check_column = 'S'
    important_checks_column = 'T'
    failed_check_column = 'U'
    credentials_file = 'creds/google__sa.json'
    RLHF_URL = 'https://rlhf-v3.turing.com/graphql'
    IMPORTANT_CHECKS = [
        'rlhf_prompt__realistic',
        'prompt_detail_level',
        'Evaluationform__has_pleasantries',
        'Evaluationform__is_ideal',
        'rlhf_Evaluationform__realistic'
    ]

    workers_count = 1

    worksheet = get_worksheet(credentials_file, sheet_url, tab_name)

    rows = worksheet.get_all_values()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        list(tqdm(executor.map(lambda i_row: process_row(i_row[0], i_row[1], worksheet), enumerate(rows)), total=len(rows)))
