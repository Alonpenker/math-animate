# Security Policy

MathAnimate takes security seriously. This policy applies to the source code in this repository, the infrastructure definitions under `infrastructure/`, and the official MathAnimate deployments operated from this codebase, including `https://mathanimate.com` and `https://api.mathanimate.com`.

Security reports help protect the project and its users. Thank you for reporting issues responsibly and privately.

## Supported Versions

MathAnimate is an actively developed monorepo. Security fixes are only guaranteed for the latest production deployment and the current `main` branch.

| Deployment / branch | Frontend | Backend / API / worker | Security fixes |
| --- | --- | --- | --- |
| Latest production deployment | Latest deployed `mathanimate.com` frontend | Latest deployed `api.mathanimate.com` API and worker stack | Yes |
| `main` branch | Current development version | Current development version | Yes |
| Older commits, tags, branches, forks, and stale self-hosted deployments | Older | Older | No |

If you run a fork or self-hosted copy, update to the latest code and dependencies before requesting a fix. Reports against outdated deployments may still be reviewed, but fixes may be limited to the current supported code.

## Reporting a Vulnerability

Do not open a public GitHub issue, discussion, or pull request for a suspected security problem.

Use GitHub's private vulnerability reporting flow for this repository:

1. Open the repository Security tab at `https://github.com/Alonpenker/math-animate/security`.
2. Select `Report a vulnerability`.
3. Submit the report privately with the details listed below.

If the private reporting flow is temporarily unavailable, use a private contact method published on the official site or GitHub profile and reference this policy. Do not disclose the issue publicly first.

## What To Include In Your Report

Please include as much of the following as you can:

- The vulnerability type and the affected component.
- The affected URL, API route, source file, infrastructure module, or workflow.
- The affected branch, commit, tag, or deployment environment.
- Prerequisites, configuration, or credentials required to reproduce the issue.
- Step-by-step reproduction instructions.
- A proof of concept, logs, screenshots, or a minimal exploit if available.
- The security impact, including whether the issue could expose secrets, bypass the API key gate, access artifacts across jobs, escape the render sandbox, read or write arbitrary files, trigger SSRF, or abuse queues or storage.
- Whether any sensitive data was accessed, modified, or retained during testing.
- Any suggested mitigation or patch direction.

Please redact secrets from your report whenever possible. Do not include production credentials, tokens, or unrelated personal data unless they are strictly necessary to demonstrate impact.

## Scope

In scope:

- The code in this repository.
- The official frontend at `mathanimate.com`.
- The official API at `api.mathanimate.com`.
- Project-controlled infrastructure and deployment configuration documented in this repository.
- Security issues involving secrets handling, artifact access, queue processing, infrastructure exposure, rate-limit bypass with real impact, or sandbox escape in the render pipeline.

Potentially out of scope or lower priority:

- Automated scanner output without a working exploit or a clear impact statement.
- Clickjacking, missing headers, or content spoofing with no meaningful state-changing or data-exposure impact.
- Self-XSS that requires a user to paste code into their own browser or console.
- Volumetric denial-of-service, spam, or brute-force traffic without a concrete MathAnimate-specific bypass or weakness.
- Issues that require physical access, machine-in-the-middle control of the victim environment, or compromise of a local development machine only.
- Reports affecting unsupported branches, forks, stale deployments, or unpatched self-hosted copies.
- Publicly known dependency CVEs without a demonstrated vulnerable path in this project.
- Vulnerabilities that belong exclusively to upstream services or vendors, such as GitHub, OpenAI, AWS, Cloudflare, Docker Hub, Ollama, or Manim, unless MathAnimate-specific configuration makes the issue exploitable here.

## Safe Harbor

If you act in good faith and follow this policy, MathAnimate will not pursue legal action against you for your research.

Good-faith research means, at minimum:

- Avoid privacy violations, data destruction, service degradation, and social engineering.
- Access only the minimum data needed to demonstrate the issue.
- Do not retain, share, or use any data obtained during testing beyond what is necessary for the report.
- Stop testing and report immediately if you encounter real user data, secrets, or infrastructure credentials.
- Give the maintainer a reasonable opportunity to investigate and remediate the issue before public disclosure.

MathAnimate does not currently offer a bug bounty program.

## Coordinated Disclosure Process

After receiving a report, the maintainer will typically:

1. Confirm receipt and validate the report.
2. Reproduce the issue and determine affected components and versions.
3. Mitigate immediate risk where necessary.
4. Prepare and test a fix.
5. Coordinate a disclosure timeline with the reporter.
6. Publish a GitHub Security Advisory and request a CVE when appropriate.

Please allow a default coordinated disclosure window of up to 90 days unless a shorter timeline is agreed due to active exploitation or a low-risk issue.

## Third-Party Dependencies

If the issue is in an upstream package, container image, or hosted provider rather than MathAnimate-specific code or configuration, please report it to the upstream maintainer as well. If MathAnimate's usage, defaults, or deployment model materially increase the risk, include that context in your private report here.

## Credit

If a report leads to a confirmed fix, the reporter may be credited in the advisory or changelog unless they prefer to remain anonymous.
