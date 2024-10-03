import json
import os.path

import nbformat
import gdown
import markdown
from bs4 import BeautifulSoup
import requests

from config import OUTPUT_FOLDER

RLHF_URL = 'https://rlhf-v3.turing.com/graphql'
output_folder = OUTPUT_FOLDER


def send_request(message):
    message = message.replace('\n', '')
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer dummy'

    }
    return requests.post(RLHF_URL, headers=headers, data=message)


def extract_python_code(markdown_text):
    # Convert the markdown text to HTML
    html = markdown.markdown(markdown_text, extensions=['fenced_code'])

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Extract all <code> blocks inside <pre> that have Python as the language
    code_blocks = soup.find_all('code', class_='language-python')

    # Combine all Python code blocks into one string
    combined_code = "\n".join([block.get_text() for block in code_blocks])

    return combined_code


task_id = "fd859800-afe9-4a7c-a1d9-93194d88fa38"
prompt_query = {
	"operationName": "GetPrompt",
	"query": "query GetPrompt($id: ID!) {\n  prompt(idOrUuid: $id) {\n    ...PromptBaseFields\n    feedback\n    genericTextLLMChecks {\n      ...GenericTextLLMCheckBaseFields\n      __typename\n    }\n    promptTurns {\n      ...PromptTurnBaseFields\n      promptResponses {\n        ...PromptResponseBaseFields\n        __typename\n      }\n      __typename\n    }\n    llmChecks {\n      ...LLMCheckBaseFields\n      feedbacks {\n        ...LLMCheckFeedbackBaseFields\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment ReviewCriteriaBaseFields on ReviewCriteria {\n  key\n  name\n  description\n  type\n  displayCondition\n  options {\n    name\n    value\n    __typename\n  }\n  llmCheckEnabled\n  __typename\n}\n\nfragment PromptTurnUploadedFilesBaseFields on PromptTurnUploadedFile {\n  id\n  filename\n  gcsPath\n  mimeType\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptResponseClaimBaseFields on PromptResponseClaim {\n  id\n  claim\n  createdAt\n  updatedAt\n  feedback\n  claimIndex\n  __typename\n}\n\nfragment PromptResponseSearchContextBaseFields on PromptResponseSearchContext {\n  id\n  promptResponseId\n  type\n  feedback\n  article\n  searchContextUUID\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptBaseFields on Prompt {\n  id\n  uuid\n  status\n  modelConfig\n  qualityDimensions {\n    systemName\n    qualityGuidelines\n    qualityEvaluationRules\n    checkedPart\n    __typename\n  }\n  reviewCriteria {\n    ...ReviewCriteriaBaseFields\n    __typename\n  }\n  createdAt\n  updatedAt\n  metadata\n  turingMetadata\n  config\n  type\n  __typename\n}\n\nfragment GenericTextLLMCheckBaseFields on GenericTextLLMCheck {\n  id\n  status\n  text\n  runId\n  result\n  createdAt\n  updatedAt\n  __typename\n}\n\nfragment PromptTurnBaseFields on PromptTurn {\n  id\n  prompt\n  createdAt\n  updatedAt\n  promptIndex\n  groupIndex\n  tags\n  parentId\n  feedback\n  promptEvaluationFeedback\n  preferenceJustification\n  preferenceSignal\n  customTitle\n  uploadedFiles {\n    ...PromptTurnUploadedFilesBaseFields\n    __typename\n  }\n  idealResponse\n  idealResponseAsPreferred\n  idealResponseLLMReviewStatus\n  idealResponseLLMReviewPayload\n  unratable\n  isToolTurn\n  __typename\n}\n\nfragment PromptResponseBaseFields on PromptResponse {\n  id\n  claims {\n    ...PromptResponseClaimBaseFields\n    __typename\n  }\n  searchContexts {\n    ...PromptResponseSearchContextBaseFields\n    __typename\n  }\n  searchContextPayload {\n    id\n    searchResult\n    searchQuery\n    type\n    __typename\n  }\n  response\n  toolCalls\n  model\n  temperature\n  feedback\n  chosenToContinue\n  createdAt\n  updatedAt\n  promptTurnId\n  llmReviewPayload\n  llmReviewStatus\n  tags\n  overallWebRagFeedback\n  overallXRagFeedback\n  __typename\n}\n\nfragment LLMCheckBaseFields on LLMCheck {\n  id\n  checkPartType\n  status\n  runId\n  resultJson\n  checkPartId\n  createdAt\n  updatedAt\n  promptId\n  __typename\n}\n\nfragment LLMCheckFeedbackBaseFields on LLMChecksFeedback {\n  id\n  llmCheckId\n  qualityDimension\n  thumbScore\n  feedback\n  createdAt\n  updatedAt\n  __typename\n}",
	"variables": {
		"id": task_id
	}
}

http_response = send_request(json.dumps(prompt_query))
res = json.loads(http_response.text)
# print(json.dumps(res, indent=2))

turn0 = res['data']['prompt']['promptTurns'][0]
idealRes = turn0['idealResponse']
# print(idealRes)

python_code = extract_python_code(idealRes)
with open(os.path.join(output_folder, "ideal.py"), "w") as output_file:
    output_file.write(python_code)
    print("Python code has been extracted and saved to output.py")


criteria = turn0['feedback']['customModelReviewCriteria']
colab_link = next(c['value'] for c in criteria if c['name'] == 'idealResponseExecutionLink')

print(colab_link)
colab_link = 'https://colab.research.google.com/drive/1UWlExuNvnsxEL0EalTG92lTCk7YvCuN_'

file_id = colab_link.split('?')[0].split('/')[-1]
download_link = f'https://drive.google.com/uc?id={file_id}'
print(download_link)
notebook_path = os.path.join(output_folder, 'notebook.ipynb')
gdown.download(download_link, notebook_path, quiet=False)
with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook_content = f.read()

notebook = nbformat.reads(notebook_content, as_version=4)

dp_python = []
dp_bash = []
for cell in notebook['cells']:
    if cell['cell_type'] == 'code' and cell['source']:
        lines = cell['source'].split('\n')
        if lines[0].startswith('#P') or lines[0].startswith('#p'):
            if lines[1].startswith('!'):
                dp_bash.append(cell['source'].replace('!', ''))
            else:
                dp_python.append(cell['source'])

# Step 4: Write extracted code cells to a Python file
with open(os.path.join(output_folder, "prep.py"), 'w') as f:
    f.write('\n\n'.join(dp_python))

with open(os.path.join(output_folder, "prep.sh"), 'w') as f:
    f.write('\n\n'.join(dp_bash))

print("Extracted #DP cells written to dp_cells.py.")


