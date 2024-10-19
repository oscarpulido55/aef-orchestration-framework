#!/bin/bash
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Fork demo [Dataform repository] (https://github.com/oscarpulido55/aef-data-orchestration/blob/0c1a69e655e3435b978e6a68640db141e86b2685/workflow-definitions/demo_pipeline_cloud_workflows.json#L42)
# Modify new repository, so it points to the GCP projects where you will deploy / store your data by modifying [dataform.json](https://github.com/oscarpulido55/aef-sample-dataform-repo/blob/main/dataform.json) and push to your own new repository.

new_repo_name=$1
project_id=$2
working_directory=$3

# Check if arguments are provided
if [ -z "$new_repo_name" ] || [ -z "$project_id" ] || [ -z "$working_directory" ]; then
  echo "Usage: $0 <new_repo_name> <project_id> <working_directory>"
  exit 1
fi

cd $working_directory

# Check if gh is installed
if ! command -v gh &> /dev/null; then
  echo "gh is not installed. Installing..."

  # Install gh based on OS
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt &> /dev/null; then
      sudo apt install gh -y
    elif command -v dnf &> /dev/null; then
      sudo dnf install gh -y
    elif command -v pacman &> /dev/null; then
      sudo pacman -S gh --noconfirm
    else
      echo "Unsupported package manager. Please install gh manually."
      exit 1
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
      brew install gh
    else
      echo "Homebrew is not installed. Please install Homebrew first or install gh manually."
      exit 1
    fi
  elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    echo "Please install gh manually from https://cli.github.com/"
    exit 1
  else
    echo "Unsupported OS. Please install gh manually."
    exit 1
  fi
fi

gh auth login

# Create a new repository from the template
rm -rf $new_repo_name
gh repo create "$new_repo_name" --template "https://github.com/oscarpulido55/aef-sample-dataform-repo" --public | grep "already exists"
if [[ $? -eq 0 ]]; then
  exit 1
fi

echo "New repository '$new_repo_name' created from template 'https://github.com/oscarpulido55/aef-sample-dataform-repo'"
sleep 3
gh repo clone "$new_repo_name"

# Replace <PROJECT_ID> with the actual Project ID in dataform.json
cd $new_repo_name
escaped_project_id=$(echo "$project_id" | sed 's/-/\\-/g')

sed -i.bak "s/<PROJECT_ID>/$escaped_project_id/g" dataform.json

# Commit the changes
git add dataform.json
git commit -m "Update dataform.json with Project ID"
git push origin main

cd $working_directory