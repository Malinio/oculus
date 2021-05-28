TARGET_PYTHON_VERSION := python3.9

VENV_DIR := .venv
VENV_PIP := $(VENV_DIR)/bin/pip
REQUIREMENTS_FILE := req.txt

run:
	echo 1

venv: $(VENV_DIR)
	$(VENV_PIP) install -r $(REQUIREMENTS_FILE)

clean:
	rm -rf $(VENV_DIR)

$(VENV_DIR):
	virtualenv --python=$(TARGET_PYTHON_VERSION) $(VENV_DIR)