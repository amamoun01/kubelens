# KubeLens

A lightweight, high-performance Internal Developer Platform (IDP) and cluster topology dashboard. KubeLens maps, evaluates, and visualizes live namespace workloads and network resources directly from the Kubernetes Control Plane using the native Python client [SDK]((https://github.com/kubernetes-client/python)).

---

## 🏗️ Architecture & Mechanics

* **Zero-Dependency Control Plane Routing:** Interfaces directly with the Kubernetes Core API via the official [`kubernetes-client SDK`](https://github.com/kubernetes-client/python), executing real-time lookups without heavy third-party wrappers.

* **Decoupled Security Boundaries:** Runs under a dedicated, non-privileged cluster context tied strictly to native **ServiceAccounts** and restricted **ClusterRoles**.

* **Context Auto-Discovery:** Automatically detects its environment—seamlessly swapping between `load_incluster_config()` for live pod operations and `load_kube_config()` for local development loops.

![Architecture Diagram](https://github.com/amamoun01/kubelens/blob/main/assets/kubelens_architecture.png)

---

## 🚀 Quick Start

### 1. Configure the Local Environment

Clone the repository and create your local environment file:

```bash
echo "DEBUG=True" > .env
```

> 💡 The .env file is included in .gitignore to prevent local development variables from being committed to Git.

### 2. Initialize the Local Workspace

Install dependencies and set up the local development tooling:

```Bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run codebase formatting and linting scans
pre-commit run --all-files
```

### 3. Start the Local Server

Run the Django development server to verify visual mapping against your active local kubectl context:

```Bash
# Export env variables
set -a && source .env && set +a

# Start Django
python manage.py runserver
```

## 🚢 Kubernetes Deployment

Deploy the stack into your cluster using standard manifests.

### 1. Create the Secret

Generate a secure token for Django (for example):

```bash
python -c "import secrets; print(secrets.token_urlsafe(45))"
```

Update and apply your `deploy/kubelens-secret.yaml`:

```YAML
apiVersion: v1
kind: Secret
metadata:
  name: kubelens-secrets
  namespace: default
type: Opaque
stringData:
  django-secret-key: "<--- your-secure-production-token-here"
```

```bash
kubectl apply -f deploy/kubelens-secret.yaml
```

### 2. Deploy Core Manifests

Apply the primary manifests containing the `ServiceAccount`, `ClusterRole` `bindings`, `Deployment`, and `ClusterIP` Service:

```bash
kubectl apply -f deploy/kubelens-production.yaml
```

### 3. Access the Dashboard

Since the service is exposed internally via a `ClusterIP`, use a port-forward tunnel to access the dashboard locally:

```bash
kubectl port-forward svc/kubelens-service 8080:80
```

Open your browser and navigate to: `http://localhost:8080`

## 🛡️ CI/CD & Security Pipeline

The project uses GitHub Actions and [`pre-commit`](https://pre-commit.com/) to enforce code quality, linting, and security scans. To keep local development and remote CI runs consistent, the same validation checks are executed both locally and on remote runners.

The pipeline runs automatically on every push or pull request through the following steps:

* **Static Analysis & Linting:** Validates the codebase using [`Ruff`](https://docs.astral.sh/ruff/) for Python linting/formatting, alongside [`yamllint`](https://yamllint.readthedocs.io/en/stable/) and [`checkov`](https://www.checkov.io/1.Welcome/What%20is%20Checkov.html) for Kubernetes manifest validation.

* **Security Auditing:** Runs [`bandit`](https://bandit.readthedocs.io/en/latest/) to inspect Python code for security vulnerabilities.

* **Container Build & Registry:** Triggers a multi-stage Docker build and pushes verified images to [`GitHub Container Registry`](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry) (ghcr.io).

* **Vulnerability Scanning:** Scans the final container image layer-by-layer using [`AquaSecurity Trivy`](https://trivy.dev/docs/latest/guide/). The pipeline enforces a fail-closed policy (exit-code: 1) on any High or Critical CVEs, automatically blocking vulnerable builds from publishing.

## 🔮 Next Steps & Scaling Roadmap

The following milestones are planned to expand `KubeLens` from a single-cluster utility into a multi-cluster dashboard:

* **Multi-Cluster Context Switching:** Extend the Python SDK client layer to support dynamic token loading. This will allow users to securely switch views between multiple distinct clusters (e.g., Dev, Stage, Prod) from a single interface.

* **Redis Caching Layer:** Integrate [Redis](https://redis.io/docs/latest/) to cache frequent API responses (such as active pod lists and namespace changes). This reduces API overhead on the Kubernetes Control Plane and improves dashboard performance in large clusters.

* **WebSocket Log Streaming:** Refactor the container log pipeline from standard HTTP polling to [WebSockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API), enabling low-latency, real-time log streaming from live containers.

* **GitOps Integration (ArgoCD):** Provide native manifests and patterns to transition from manual kubectl apply deployments to automated GitOps continuous delivery workflows via [ArgoCD](https://argo-cd.readthedocs.io/en/stable/).
