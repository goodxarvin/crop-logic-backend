#!/usr/bin/env bash

set -euo pipefail

MODEL="${OPENAI_MODEL:-gpt-4o-mini}"
BASE_URL="${OPENAI_BASE_URL:-${GAPGPT_BASE_URL:-https://api.gapgpt.app/v1}}"
API_KEY="${OPENAI_API_KEY:-${GAPGPT_API_KEY:-"sk-ZeFmDwROcQ2rYOFmUxHLjIwMTSUdo2qNc3Uraug9dOK2ihn5"}}"
EDITOR_CMD="${EDITOR:-vi}"
SHOW_API_RESPONSE="${SHOW_API_RESPONSE:-0}"
ALLOWED_BRANCH_TYPES="documentation,feature,fixbug"
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
  `OPENAI_MODEL`                       Model name (default: gpt-4o-mini)
  `EDITOR`                             Editor used for manual commit message edits
  `SHOW_API_RESPONSE`                  Print raw API response body when set to 1
USAGE
}

show_jq_install_help() {
  cat >&2 <<'EOF'
Error: 'jq' is required but not installed.

Install jq on Linux with one of these commands:
- Ubuntu/Debian: sudo apt update && sudo apt install -y jq
- Fedora/RHEL/CentOS: sudo dnf install -y jq
- Arch Linux: sudo pacman -S jq
- Alpine: sudo apk add jq
EOF
}

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    if [[ "$command_name" == "jq" ]]; then
      show_jq_install_help
      exit 1
    fi
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

stage_all_changes() {
  git add .
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
- Allowed branch types are only: documentation, feature, fixbug.
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
  local response_file
  local http_code

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

  response_file=$(mktemp)
  http_code=$(curl --silent --show-error \
    --output "$response_file" \
    --write-out "%{http_code}" \
    --header "Content-Type: application/json" \
    --header "Authorization: Bearer ${API_KEY}" \
    --data "$payload" \
    "$endpoint")

  if [[ "$SHOW_API_RESPONSE" == "1" ]]; then
    echo
    echo "Raw API response:"
    echo "----------------------------------------"
    cat "$response_file"
    echo
    echo "----------------------------------------"
  fi

  if [[ ! "$http_code" =~ ^2 ]]; then
    echo "API request failed with HTTP ${http_code}." >&2
    echo "Raw API error response:" >&2
    echo "----------------------------------------" >&2
    cat "$response_file" >&2
    echo >&2
    echo "----------------------------------------" >&2
    rm -f "$response_file"
    return 1
  fi

  cat "$response_file"
  rm -f "$response_file"
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

  read -r -e -i "$current_value" -p "> " updated_value </dev/tty

  if [[ -z "$updated_value" ]]; then
    echo "Error: value cannot be empty." >&2
    exit 1
  fi

  printf '%s' "$updated_value"
}

confirm_pull_from_develop() {
  local choice

  echo >&2
  echo "Before asking AI, do you want to pull the latest changes from \`develop\` into the current branch?" >&2
  read -r -p "Pull from develop now? [y/N]: " choice </dev/tty

  if [[ "$choice" =~ ^[Yy]$ ]]; then
    git pull origin develop
  fi
}

confirm_or_edit_commit_message() {
  local current_message="$1"

  echo >&2
  echo "Suggested commit message:" >&2
  echo "----------------------------------------" >&2
  printf '%s\n' "$current_message" >&2
  echo "----------------------------------------" >&2
  echo "1) Use as-is" >&2
  echo "2) Edit in \$EDITOR (${EDITOR_CMD})" >&2

  local choice
  read -r -p "Choose an option [1-2]: " choice </dev/tty

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

  echo >&2
  echo "Select an existing branch:" >&2
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
  local branch_type="${branch_name%%/*}"

  if ! git check-ref-format --branch "$branch_name" >/dev/null 2>&1; then
    echo "Error: '$branch_name' is not a valid git branch name." >&2
    exit 1
  fi

  if [[ "$branch_name" != */* ]]; then
    echo "Error: branch name must use the format type/short-description." >&2
    exit 1
  fi

  case "$branch_type" in
    documentation|feature|fixbug) ;;
    *)
      echo "Error: branch type must be one of: documentation, feature, fixbug." >&2
      exit 1
      ;;
  esac
}

choose_branch() {
  local suggested_branch="$1"
  local branch_choice
  local branch_value
  local branch_mode

  echo >&2
  echo "Suggested branch name: $suggested_branch" >&2
  echo "1) Create new branch with suggested name" >&2
  echo "2) Edit branch name and create new branch" >&2
  echo "3) Select an existing branch" >&2
  read -r -p "Choose an option [1-3]: " branch_choice </dev/tty

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

  if [[ "$branch_mode" == "new" ]]; then
    validate_branch_name "$branch_value"
  fi

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

push_branch() {
  local branch_name="$1"
  local branch_mode="$2"

  if [[ "$branch_mode" == "new" ]]; then
    git push -u origin "$branch_name"
  else
    git push origin "$branch_name"
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

  confirm_pull_from_develop
  stage_all_changes

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
  push_branch "$FINAL_BRANCH_NAME" "$FINAL_BRANCH_MODE"

  echo
  echo "Done: committed and pushed on '$FINAL_BRANCH_NAME'."
}

main "$@"
