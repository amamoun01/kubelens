"""Kube Client module for interacting with Kubernetes API."""

import logging
from kubernetes import client, config
from django.core.cache import cache

logger = logging.getLogger(__name__)


class KubeClient:
    """Kubernetes Client."""

    def __init__(self):
        """Init Kubernetes client."""
        try:
            config.load_kube_config()
        except Exception:
            try:
                config.load_incluster_config()
            except Exception as err:
                logger.error(f"Failed to load Kubernetes configuration: {err}")
                self.v1 = None
                return
        self.v1 = client.CoreV1Api()

    def get_namespaces(self):
        """List namespaces in the cluster."""
        if not self.v1:
            return []

        cache_key = "k8s_namespaces"
        namespaces = cache.get(cache_key)

        if namespaces is None:
            try:
                ns_list = self.v1.list_namespace(timeout_seconds=5)
                namespaces = [ns.metadata.name for ns in ns_list.items]
                cache.set(cache_key, namespaces, timeout=30)  # Cache namespaces for 30s
            except Exception as e:
                logger.error(f"Error fetching namespaces: {e}")
                return ["default"]
        return namespaces

    def get_pods(self, namespace="default"):
        """List pods in a given namespace."""
        if not self.v1:
            return []
        cache_key = f"k8s_pods_{namespace}"
        pods_data = cache.get(cache_key)

        if pods_data is None:
            try:
                pod_list = self.v1.list_namespaced_pod(namespace, timeout_seconds=5)
                pods_data = []
                for pod in pod_list.items:
                    containers = []
                    for c in pod.status.container_statuses or []:
                        containers.append(
                            {
                                "name": c.name,
                                "ready": c.ready,
                                "restart_count": c.restart_count,
                                "state": list(c.state.to_dict().keys())[0]
                                if c.state
                                else "Unknown",
                            }
                        )

                    pods_data.append(
                        {
                            "name": pod.metadata.name,
                            "status": pod.status.phase,
                            "pod_ip": pod.status.pod_ip,
                            "node_name": pod.spec.node_name,
                            "created": pod.metadata.creation_timestamp.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if pod.metadata.creation_timestamp
                            else "Unknown",
                            "containers": containers,
                        }
                    )
                cache.set(cache_key, pods_data, timeout=5)
            except Exception as e:
                logger.error(f"Error fetching pods: {e}")
                return []
        return pods_data

    def get_pod_logs(self, namespace, pod_name, container_name=None):
        """Fetch logs for a specific pod and container."""
        if not self.v1:
            return "KubeClient disconnected."

        try:
            kwargs = {"tail_lines": 200, "_preload_content": False}
            if container_name:
                kwargs["container"] = container_name

            raw_response = self.v1.read_namespaced_pod_log(
                name=pod_name, namespace=namespace, **kwargs
            )
            raw_bytes = raw_response.read()
            clean_text_logs = raw_bytes.decode("utf-8", errors="ignore")

            return clean_text_logs

        except Exception as e:
            return f"Error pulling logs from cluster: {e}"

    def get_services(self, namespace="default"):
        """List services in a given namespace."""
        if not self.v1:
            return []
        cache_key = f"k8s_services_{namespace}"
        services_data = cache.get(cache_key)

        if services_data is None:
            try:
                svc_list = self.v1.list_namespaced_service(namespace, timeout_seconds=5)
                services_data = []
                for svc in svc_list.items:
                    services_data.append(
                        {
                            "name": svc.metadata.name,
                            "type": svc.spec.type,
                            "cluster_ip": svc.spec.cluster_ip,
                            "ports": [
                                f"{p.port}:{p.target_port}/{p.protocol}"
                                for p in svc.spec.ports
                            ]
                            if svc.spec.ports
                            else [],
                            "created": svc.metadata.creation_timestamp.strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            if svc.metadata.creation_timestamp
                            else "Unknown",
                        }
                    )
                cache.set(cache_key, services_data, timeout=5)
            except Exception:
                return []
        return services_data

    def get_deployments(self, namespace="default"):
        """Get deployments in a given namespace."""
        try:
            apps_v1 = client.AppsV1Api()
            cache_key = f"k8s_deployments_{namespace}"
            deploy_data = cache.get(cache_key)

            if deploy_data is None:
                deploy_list = apps_v1.list_namespaced_deployment(
                    namespace, timeout_seconds=5
                )
                deploy_data = []
                for d in deploy_list.items:
                    deploy_data.append(
                        {
                            "name": d.metadata.name,
                            "replicas": f"{d.status.ready_replicas or 0}/{d.spec.replicas}",
                            "strategy": d.spec.strategy.type
                            if d.spec.strategy
                            else "RollingUpdate",
                            "updated": d.status.updated_replicas or 0,
                        }
                    )
                cache.set(cache_key, deploy_data, timeout=5)
            return deploy_data
        except Exception:
            return []
