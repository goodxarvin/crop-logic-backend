#!/usr/bin/env bash

set -euo pipefail

MODEL="${OPENAI_MODEL:-gpt-4}"
BASE_URL="${OPENAI_BASE_URL:-${GAPGPT_BASE_URL:-https://api.gapgpt.app/v1}}"
API_KEY="${OPENAI_API_KEY:-${GAPGPT_API_KEY:-}}"
EDITOR_CMD="${EDITOR:-vi}"
COMMIT_MESSAGE=""
BRANCH_NAME=""
FINAL_BRANCH_NAME=""
FINAL_BRANCH_MODE=""

usage() {
  cat <<'USAGE'
Usage: ai_git_commit.sh

Required environment variables:
  `OPENAI_API_KEY` or `GAPGPT_API_KEY`

Optional environment variables:
  `OPENAI_BASE_URL` or `GAPGPT_BASE_URL` (default: https://api.gapgpt.app/v1)
  `OPENAI_MODEL`                       Model name (default: gpt-4)
  `EDITOR`                             Editor used for manual commit message edits
USAGE
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Error: '$command_name' is required but not installed." >&2
    exit 1
  fi
}

ensure_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "Error: current directory is not a git repository." >&2
    exit 1
  }
}

get_staged_diff() {
  git diff --staged --patch --minimal
}

build_prompt() {
  local diff_content="$1"

  cat <<PROMPT
You are a senior engineer helping with Git hygiene.
Analyze the staged git diff below and respond with valid JSON only.

Requirements:
- The response must be a JSON object with exactly these keys: commit_message, branch_name.
- commit_message must be a single descriptive paragraph in plain text.
- branch_name must use the format type/short-description.
- branch_name should be lowercase, concise, and use hyphens instead of spaces.
- Do not wrap the JSON in markdown fences.

Staged diff:
${diff_content}
PROMPT
}

call_openai() {
  local prompt="$1"
  local endpoint="${BASE_URL%/}/chat/completions"
  local payload

  payload=$(jq -n \
    --arg model "$MODEL" \
    --arg prompt "$prompt" \
    '{
      model: $model,
      temperature: 0.2,
      response_format: {type: "json_object"},
      messages: [
        {role: "system", content: "You generate commit metadata from git diffs and always return strict JSON."},
        {role: "user", content: $prompt}
      ]
    }')

  curl --silent --show-error --fail \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${API_KEY}" \
    --data "$payload" \
    "$endpoint"
}

extract_ai_content() {
  local api_response="$1"

  jq -er '.choices[0].message.content' <<<"$api_response"
}

parse_ai_json() {
  local ai_json="$1"

  COMMIT_MESSAGE=$(jq -er '.commit_message' <<<"$ai_json")
  BRANCH_NAME=$(jq -er '.branch_name' <<<"$ai_json")
}

edit_multiline_value() {
  local initial_value="$1"
  local temp_file

  temp_file=$(mktemp)
  printf '%s\n' "$initial_value" > "$temp_file"
  "$EDITOR_CMD" "$temp_file"
  local edited_value
  edited_value=$(sed '/^[[:space:]]*$/d' "$temp_file")
  rm -f "$temp_file"

  if [[ -z "$edited_value" ]]; then
    echo "Error: value cannot be empty." >&2
    exit 1
  fi

  printf '%s' "$edited_value"
}

edit_single_line_value() {
  local current_value="$1"
  local updated_value

  read -r -e -i "$current_value" -p "> " updated_value

  if [[ -z "$updated_value" ]]; then
    echo "Error: value cannot be empty." >&2
    exit 1
  fi

  printf '%s' "$updated_value"
}

confirm_or_edit_commit_message() {
  local current_message="$1"

  echo
  echo "Suggested commit message:"
  echo "----------------------------------------"
  printf '%s\n' "$current_message"
  echo "----------------------------------------"
  echo "1) Use as-is"
  echo "2) Edit in \$EDITOR (${EDITOR_CMD})"

  local choice
  read -r -p "Choose an option [1-2]: " choice

  case "$choice" in
    1) printf '%s' "$current_message" ;;
    2) edit_multiline_value "$current_message" ;;
    *)
      echo "Error: invalid selection." >&2
      exit 1
      ;;
  esac
}

list_local_branches() {
  git for-each-ref --format='%(refname:short)' refs/heads
}

select_existing_branch() {
  mapfile -t branches < <(list_local_branches)

  if [[ ${#branches[@]} -eq 0 ]]; then
    echo "Error: no local branches found." >&2
    exit 1
  fi

  echo
  echo "Select an existing branch:"
  select branch in "${branches[@]}"; do
    if [[ -n "${branch:-}" ]]; then
      printf '%s' "$branch"
      return 0
    fi

    echo "Invalid selection. Try again." >&2
  done
}

validate_branch_name() {
  local branch_name="$1"

  if ! git check-ref-format --branch "$branch_name" >/dev/null 2>&1; then
    echo "Error: '$branch_name' is not a valid git branch name." >&2
    exit 1
  fi
}

choose_branch() {
  local suggested_branch="$1"
  local branch_choice
  local branch_value
  local branch_mode

  echo
  echo "Suggested branch name: $suggested_branch"
  echo "1) Create new branch with suggested name"
  echo "2) Edit branch name and create new branch"
  echo "3) Select an existing branch"
  read -r -p "Choose an option [1-3]: " branch_choice

  case "$branch_choice" in
    1)
      branch_value="$suggested_branch"
      branch_mode="new"
      ;;
    2)
      branch_value=$(edit_single_line_value "$suggested_branch")
      branch_mode="new"
      ;;
    3)
      branch_value=$(select_existing_branch)
      branch_mode="existing"
      ;;
    *)
      echo "Error: invalid selection." >&2
      exit 1
      ;;
  esac

  validate_branch_name "$branch_value"

  if git show-ref --verify --quiet "refs/heads/$branch_value"; then
    branch_mode="existing"
  fi

  FINAL_BRANCH_NAME="$branch_value"
  FINAL_BRANCH_MODE="$branch_mode"
}

checkout_branch() {
  local branch_name="$1"
  local branch_mode="$2"

  if [[ "$branch_mode" == "new" ]]; then
    git checkout -b "$branch_name"
  else
    git checkout "$branch_name"
  fi
}

print_summary() {
  local commit_message="$1"
  local branch_name="$2"
  local branch_mode="$3"

  echo
  echo "Final plan:"
  echo "- Branch: $branch_name ($branch_mode)"
  echo "- Commit message:"
  printf '%s\n' "$commit_message"
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  require_command git
  require_command curl
  require_command jq
  ensure_git_repo

  if [[ -z "$API_KEY" ]]; then
    echo "Error: set OPENAI_API_KEY or GAPGPT_API_KEY." >&2
    exit 1
  fi

  local staged_diff
  staged_diff=$(get_staged_diff)

  if [[ -z "$staged_diff" ]]; then
    echo "Error: there are no staged changes to analyze." >&2
    exit 1
  fi

  echo "Analyzing staged changes with ${MODEL}..."

  local prompt
  prompt=$(build_prompt "$staged_diff")

  local api_response
  if ! api_response=$(call_openai "$prompt"); then
    echo "Error: failed to contact the OpenAI-compatible API." >&2
    exit 1
  fi

  local ai_content
  if ! ai_content=$(extract_ai_content "$api_response"); then
    echo "Error: API response did not include message content." >&2
    exit 1
  fi

  if ! parse_ai_json "$ai_content"; then
    echo "Error: AI response was not valid JSON with the required keys." >&2
    exit 1
  fi

  local final_commit_message
  final_commit_message=$(confirm_or_edit_commit_message "$COMMIT_MESSAGE")

  choose_branch "$BRANCH_NAME"

  print_summary "$final_commit_message" "$FINAL_BRANCH_NAME" "$FINAL_BRANCH_MODE"

  local final_confirmation
  read -r -p "Proceed with checkout and commit? [y/N]: " final_confirmation

  if [[ ! "$final_confirmation" =~ ^[Yy]$ ]]; then
    echo "Aborted. No branch switch or commit was made."
    exit 0
  fi

  checkout_branch "$FINAL_BRANCH_NAME" "$FINAL_BRANCH_MODE"

  local commit_file
  commit_file=$(mktemp)
  printf '%s\n' "$final_commit_message" > "$commit_file"
  git commit -F "$commit_file"
  rm -f "$commit_file"

  echo
  echo "Done: committed on '$FINAL_BRANCH_NAME'."
}

main "$@"
