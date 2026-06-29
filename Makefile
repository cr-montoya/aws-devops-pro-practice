.PHONY: help test-sam validate-sam build-sam deploy-sam-dev test-cdk synth-cdk validate-all clean-sam

help:
	@echo "Available targets:"
	@echo "  test-sam        Run SAM unit tests"
	@echo "  validate-sam    Run sam validate --lint and cfn-lint for SAM pipeline"
	@echo "  build-sam       Build SAM application"
	@echo "  deploy-sam-dev  Deploy SAM dev stack"
	@echo "  test-cdk        Run CDK unit tests"
	@echo "  synth-cdk       Synthesize CDK app"
	@echo "  validate-all    Run SAM and CDK validation"
	@echo "  clean-sam       Remove SAM build artifacts"

test-sam:
	cd SAM && python -m pytest tests/unit -q

validate-sam:
	cd SAM && sam validate --lint
	cd SAM && cfn-lint pipeline.yaml

build-sam:
	cd SAM && sam build

deploy-sam-dev:
	cd SAM && sam deploy --config-env dev

test-cdk:
	cd CDK && .venv/bin/python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider

synth-cdk:
	cd CDK && cdk synth

validate-all: test-sam validate-sam build-sam test-cdk synth-cdk

clean-sam:
	rm -rf SAM/.aws-sam
