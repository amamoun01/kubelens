"""Views."""

from django.shortcuts import render
from django.http import HttpResponse
from django.utils.html import escape
from .kube_client import KubeClient

k8s = KubeClient()


def dashboard_home(request):
    """Home Dashboard view."""
    selected_ns = request.GET.get("namespace", "default")
    context = {
        "namespaces": k8s.get_namespaces(),
        "selected_namespace": selected_ns,
        "pods": k8s.get_pods(selected_ns),
        "services": k8s.get_services(selected_ns),
        "deployments": k8s.get_deployments(selected_ns),
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "partials/pod_grid.html", context)

    return render(request, "landing_page.html", context)


def pod_logs_partial(request, namespace, pod_name):
    """Logs view."""
    container_name = request.GET.get("container", None)
    logs = escape(k8s.get_pod_logs(namespace, pod_name, container_name))

    response_html = f"""
    <pre class="text-xs font-mono text-slate-200 whitespace-pre-wrap leading-relaxed bg-transparent p-1 block w-full">
{logs}
    </pre>
    """

    return HttpResponse(response_html)
