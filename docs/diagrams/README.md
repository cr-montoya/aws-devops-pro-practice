# Architecture diagrams

The PNGs use the official AWS `aws4` shapes bundled with draw.io. Open the adjacent `.drawio` files in diagrams.net to edit them. Numbered arrows describe flows, not a global execution sequence. Dashed arrows indicate control, telemetry or supporting access. Boundaries show placement; repeated resources across availability zones are aggregated for readability.

## Scope and source of truth

- SAM: `SAM/template.yaml`, `SAM/pipeline.yaml` and `SAM/buildspec.yml`. Five functions have `live` aliases and CodeDeploy canaries in every stage. Only task operations access DynamoDB. Function error alarms drive rollback; API alarms provide monitoring. No VPC is configured.
- CDK: `CDK/app.py`, `CDK/stacks/*.py`, `CDK/ecs/app.py` and `CDK/lambda/*.py`. Production has public ALB subnets and isolated Fargate subnets across two AZs. Dev uses public tasks with public IPs. Lambda, Kinesis and storage are regional services outside the VPC.
- Production interface endpoints: ECR API/Docker, ECS/agent/telemetry, STS, Secrets Manager, CloudWatch Logs and Kinesis. Gateway endpoints: S3 and DynamoDB. No NAT gateway is defined.
- CDK CloudWatch collects application/infrastructure telemetry and sends alarm actions to SNS. Lambda tracing uses X-Ray. EventBridge sends stopped-task notifications and a 15-minute heartbeat to SNS, and invokes the redriver every five minutes.
- The stream failure destination receives batch metadata. The current redriver wraps each queue body as an order payload; successful recovery of original stream records is not established by this code.
- CDK delivery includes asset publishing and self-mutation. Its optional, manually approved teardown wave is omitted from the normal delivery diagram. These diagrams do not claim runtime deployment verification.

## Reproduce PNG exports

Run from the repository root with Docker; no system package installation is needed:

```bash
docker run --rm -v "$PWD":/data rlespinasse/drawio-export:v4.60.0 \
  -f png -s 2 -b 20 --remove-page-suffix -o . docs/diagrams
```

White background, 2x scale, one PNG per source alongside the editable file. The explicit image tag was published on 2026-09-14, more than seven days before selection. Image digest: `sha256:2c133c2bbb42ba97fb3c8aca83fd62be3927fef8c7caeba2673d4092b7f6c578`.

References: [export image documentation](https://github.com/rlespinasse/drawio-export/blob/v4.x/README.adoc), [version tag metadata](https://hub.docker.com/v2/repositories/rlespinasse/drawio-export/tags/v4.60.0). Export flags were checked with the pinned image's `--help`.

## CI scope

No GitHub Actions workflow or status badge is added. The full CDK application performs SSM configuration and availability-zone lookups during synthesis and requires Docker bundling. A faithful credential-free synth needs a separately maintained context fixture or isolated entry point. That is outside this documentation change; existing local validation commands remain unchanged.
