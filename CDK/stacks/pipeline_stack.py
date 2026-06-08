import aws_cdk as cdk
from aws_cdk import pipelines
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_iam as iam
from constructs import Construct
from stacks.app_stage import AppStage


class PipelineStack(cdk.Stack):
    """
    Self-mutating CDK Pipeline: GitHub -> dev (automatic) -> manual approval -> prod.

    The pipeline updates itself on every run (self_mutation=True by default).
    Changing this stack and pushing triggers it to update itself before deploying the app.

    Prerequisites (one-time setup before first deploy):
      1. Create SSM parameters with your personal values (see .env.example for names)
      2. Create a GitHub CodeStar Connection in AWS Console and set it to "Available"
      3. Run `cdk deploy Pipeline` once manually to bootstrap the pipeline
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        github_repo: str,
        github_branch: str,
        app_name: str,
        component: str,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Read personal/account-specific values from SSM Parameter Store at synth time.
        # value_from_lookup resolves immediately (not via CloudFormation) and caches the
        # result in cdk.context.json (gitignored). CodeBuild reads SSM via its IAM role.
        github_owner = ssm.StringParameter.value_from_lookup(
            self, "/orders/pipeline/github_owner"
        )
        codestar_arn = ssm.StringParameter.value_from_lookup(
            self, "/orders/pipeline/codestar_connection_arn"
        )
        alert_emails_str = ssm.StringParameter.value_from_lookup(
            self, "/orders/pipeline/alert_emails"
        )
        alert_emails = [e.strip() for e in alert_emails_str.split(",") if e.strip()]

        # Source: GitHub via CodeStar Connection (OAuth-based, no personal tokens needed)
        source = pipelines.CodePipelineSource.connection(
            f"{github_owner}/{github_repo}",
            github_branch,
            connection_arn=codestar_arn
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
                "cp requirements.txt cdk.out/",  # needed by SelfMutate step
            ],
            primary_output_directory="CDK/cdk.out"
        )

        # SSM permission for the Synth CodeBuild role.
        # value_from_lookup calls ssm:GetParameter at synth time — without this the
        # PipelineStack fails to synthesize in CodeBuild and is excluded from the assembly,
        # which causes the SelfMutate step to fail with "No stacks match the name(s) Pipeline".
        ssm_policy = iam.PolicyStatement(
            actions=["ssm:GetParameter", "ssm:GetParameters"],
            resources=[
                f"arn:aws:ssm:{self.region}:{self.account}:parameter/orders/pipeline/*"
            ]
        )

        # privileged=True: required for Docker builds triggered by ContainerImage.from_asset()
        # docker_enabled_for_synth=True: allows Docker during the synth step for BundlingOptions
        # cross_account_keys=False: simpler setup for same-account deployments
        pipeline = pipelines.CodePipeline(self, "Pipeline",
            pipeline_name=f"{app_name}-pipeline",
            synth=synth,
            synth_code_build_defaults=pipelines.CodeBuildOptions(
                role_policy=[ssm_policy]
            ),
            code_build_defaults=pipelines.CodeBuildOptions(
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                    privileged=True,
                )
            ),
            # SelfMutate receives the cdk.out artifact and runs `cdk -a . deploy Pipeline`.
            # It needs aws-cdk and the Python deps installed — requirements.txt was copied
            # into cdk.out/ by the Synth step so it's available here.
            self_mutation_code_build_defaults=pipelines.CodeBuildOptions(
                partial_build_spec=codebuild.BuildSpec.from_object({
                    "version": "0.2",
                    "phases": {
                        "install": {
                            "commands": [
                                "npm install -g aws-cdk",
                                "pip install -r requirements.txt",
                            ]
                        }
                    }
                }),
                build_environment=codebuild.BuildEnvironment(
                    build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
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
                alert_emails=alert_emails,
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
                alert_emails=alert_emails,
                env=cdk.Environment(account=self.account, region=self.region)
            ),
            pre=[
                pipelines.ManualApprovalStep("PromoteToProd",
                    comment="Review dev deployment before promoting to prod"
                )
            ]
        )
