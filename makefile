REPO:=$(shell git remote -v | grep fetch | grep origin | awk '{print $$2}' | sed 's/\.git$$//')
REPO_UPSTREAM:=$(shell git remote -v | grep fetch | grep upstream | awk '{print $$2}' | sed 's/\.git$$//')
BRANCH:=$(shell git branch --show-current)
SUBDIR:=$(shell git rev-parse --show-prefix)

open-in-github:
	open -a "Google Chrome Dev" $(REPO)/tree/$(BRANCH)/$(SUBDIR)

open-upstream-in-github:
	open $(REPO_UPSTREAM)/tree/$(BRANCH)/$(SUBDIR)

TARGET_ORG=:fflib-apex-mocks

set-target-org:
	sf config get target-org
	sf config set target-org=$(TARGET_ORG)
	sf config get target-org

deploy:
	sf project deploy start --target-org fflib-apex-mocks

generate-component-table:
	python3 bin/generate-component-table.py sfdx-source > docs/08-component-table.md
