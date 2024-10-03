import subprocess

from config import OUTPUT_FOLDER

output_folder = OUTPUT_FOLDER
image_name = "dp_code_image"
build_command = f"sudo -S docker build -t {image_name} {output_folder}"
run_command = f"sudo -S docker run --rm {image_name}"

try:
    print("Building Docker image...")
    subprocess.run(build_command, shell=True, check=True)
    print(f"Docker image '{image_name}' built successfully.")

    print("Running the Docker container...")
    subprocess.run(run_command, shell=True, check=True)
    print("Python script ran successfully in the Docker container.")
except subprocess.CalledProcessError as e:
    print(f"Error occurred while running the code: {e}")
    exit(1)
