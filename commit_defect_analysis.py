import subprocess
import os
import json
import lizard
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


defect_keywords = ['fix', 'bug', 'error', 'issue']
repo_path = '.'  # Update this to your local repository path
output_file = 'defect_frequencies.json'
plot_file = 'correlation_plot.png'

def extract_defect_commits(repo_path):
  """
  Extracts commit messages and files associated with defect-related keywords.
  """
  original_path = os.getcwd()
  os.chdir(repo_path)

  # I used this instead of PyDriller or other Python libs due to perf reasons
  # working under the assumption that the keywords should be only considered in the subject message of the commit
  git_log_cmd = ['git', 'log', '--pretty=format:%H|%s', '--name-only']
  git_log_output = subprocess.check_output(git_log_cmd, universal_newlines=True, encoding='utf-8')

  os.chdir(original_path)

  commit_lines = git_log_output.split('\n')
  defect_files = {}
  current_commit = False

  for line in commit_lines:
    if '|' in line:
      _, commit_subject = line.split('|', 1)
      if any(keyword in commit_subject.lower() for keyword in defect_keywords):
        current_commit = True
      else:
        current_commit = False
    elif line.strip() == '':
      current_commit = False
    elif current_commit:
      filename = line.strip()
      defect_files[filename] = defect_files.get(filename, 0) + 1

  return defect_files


def save_defect_frequencies(defect_files, output_file):
  """
  Saves the defect frequencies to a JSON file in the specified format.
  """
  sorted_file_counts = sorted(defect_files.items(), key=lambda x: x[1],
                              reverse=True)

  defect_list = [{filename: count} for filename, count in sorted_file_counts]
  with open(output_file, 'w') as f:
    json.dump(defect_list, f, indent=4)


def calculate_complexities(defect_files, repo_path):
  """
  Calculates the cyclomatic complexity for each file using Lizard.
  """
  complexities = {}
  for filename in defect_files.keys():
    file_path = os.path.join(repo_path, filename)

    if not os.path.isfile(file_path):
      continue

    if not filename.endswith(('.js', '.jsx', '.ts', '.tsx', '.rs', '.cpp', '.html')):
      continue

    try:
      analysis = lizard.analyze_file(file_path)
      total_complexity = sum(
        func.cyclomatic_complexity for func in analysis.function_list)
      complexities[filename] = total_complexity
    except Exception as e:
      print(f"Error analyzing {filename}: {e}")

  return complexities


def visualize_correlation(defect_files, complexities):
  """
  Visualizes the correlation between cyclomatic complexity and defect frequency.
  """
  data = []
  for filename in defect_files.keys():
    if filename in complexities:
      data.append({
        'Filename': filename,
        'Defect Frequency': defect_files[filename],
        'Complexity': complexities[filename]
      })
  df = pd.DataFrame(data)

  plt.figure(figsize=(10, 6))
  sns.regplot(x='Complexity', y='Defect Frequency', data=df,
              scatter_kws={'s': 50}, line_kws={'color': 'red'})
  plt.title('Correlation between Cyclomatic Complexity and Defect Frequency')
  plt.xlabel('Cyclomatic Complexity')
  plt.ylabel('Defect Frequency')
  plt.tight_layout()
  plt.savefig(plot_file)
  plt.show()



print('Extracting defect commits...')
defect_files = extract_defect_commits(repo_path)
print(
  f'Found {len(defect_files)} JavaScript files with defect-related commits.')

print('Saving defect frequencies to JSON...')
save_defect_frequencies(defect_files, output_file)
print(f'Defect frequencies saved to {output_file}.')

print('Calculating cyclomatic complexities...')
complexities = calculate_complexities(defect_files, repo_path)
print('Cyclomatic complexities calculated.')

print('Visualizing correlation...')
visualize_correlation(defect_files, complexities)
print(f'Correlation plot saved as {plot_file}')
