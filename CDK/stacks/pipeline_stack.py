import aws_cdk as cdk
from aws_cdk import pipelines
from aws_cdk import aws_codebuild as codebuild
from constructs import Construct
from stacks.app_stage import AppStage


class PipelineStack(cdk.Stack):
    """
    Self-mutating CDK Pipeline: GitHub -> dev (automatic) -> manual approval -> prod.

    The pipeline updates itself on every run (self_mutation=True by default).
    Changing this stack and pushing to main is enough to update the pipeline definition.

    Prerequisites before deploying:
      1. Create a GitHub CodeStar Connection in AWS Console (CodePipeline -> Settings -> Connections)
         and set it to "Available" status. Copy the ARN into app.py.
      2. Run `cdk deploy Pipeline` once manually to bootstrap the pipeline.
         From then on, pushes to main trigger the pipeline automatically.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        github_owner: str,
        github_repo: str,
        github_branch: str,
        codestar_connection_arn: str,
        app_name: str,
        component: str,
        dev_alert_emails: list,
        prod_alert_emails: list,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Source: GitHub via CodeStar Connection (OAuth-based, no personal tokens needed)
        source = pipelines.CodePipelineSource.connection(
            f"{github_owner}/{github_repo}",
            github_branch,
            connection_arn=codestar_connection_arn
        )

        # Synth step: installs deps and runs `cdk synth` from the CDK/ subdirectory.
        # primary_output_directory tells CDK Pipelines where to find the synthesized templates.
        synth = pipelines.ShellStep("Synth",
            input=source,
            install_commands=[
                "npm install -g aws-cdk",
                "pip install -r CDK/requirements.txt -r CDK/requirements-dev.txt",
            ],
            commands=[
                "cd CDK",
                "cdk synth",
            ],
            primary_output_directory="CDK/cdk.out"
        )

        # privileged=True: required for Docker builds triggered by ContainerImage.from_asset()
        # docker_enabled_for_synth=True: allows Docker during the synth step for BundlingOptions
        # cross_account_keys=False: simpler setup for same-account deployments
        pipeline = pipelines.CodePipeline(self, "Pipeline",
            pipeline_name=f"{app_name}-pipeline",
            synth=synth,
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    privileged=True,
                )
            ),
            docker_enabled_for_synth=True,
            cross_account_keys=False,
        )

        # Unit tests run as a pre-step in dev — a failure blocks deployment.
        # They run against synthesized templates without AWS credentials.
        unit_tests = pipelines.ShellStep("UnitTests",
            input=source,
            install_commands=[
                "pip install -r CDK/requirements.txt -r CDK/requirements-dev.txt",
            ],
            commands=[
                "cd CDK",
                "python -m pytest tests/unit/ -v --tb=short -p no:cacheprovider",
            ]
        )

        # Dev stage — deploys automatically on every push after unit tests pass
        pipeline.add_stage(
            AppStage(self, "Dev",
                app_name=app_name,
                stage="dev",
                component=component,
                alert_emails=dev_alert_emails,
                env=cdk.Environment(account=self.account, region=self.region)
            ),
            pre=[unit_tests]
        )

        # Prod stage — requires manual approval before deployment
        # ManualApprovalStep creates a CodePipeline approval action backed by SNS email
        pipeline.add_stage(
            AppStage(self, "Prod",
                app_name=app_name,
                stage="prod",
                component=component,
                alert_emails=prod_alert_emails,
                env=cdk.Environment(account=self.account, region=self.region)
            ),
            pre=[
                pipelines.ManualApprovalStep("PromoteToProd",
                    comment="Review dev deployment before promoting to prod"
                )
            ]
        )
