import subprocess

def start_application_and_log_errors():
    # Command to start the application
    command = ["uvicorn", "app.main:app", "--reload"]

    # Open a file to write the output
    with open("application_error_log.txt", "w") as log_file:
        try:
            # Run the command and redirect stdout and stderr to the log file
            process = subprocess.run(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
        except Exception as e:
            # If an exception occurs, write it to the log file
            log_file.write(f"Exception occurred: {str(e)}\n")

if __name__ == "__main__":
    start_application_and_log_errors()