import requests
import yaml
import json
import os
import sys
import argparse

from kubernetes import watch, client, config


def format_constructor(loader, node):
    return loader.construct_scalar(node).format(**os.environ)


yaml.SafeLoader.add_constructor(u'tag:yaml.org,2002:str', format_constructor)


class GrafanaAnnotate(object):

    tags = ['kube-deployment']
    ignore_k8s_annotations = ['kubectl.kubernetes.io/last-applied-configuration']

    def __init__(self, url, token):
        self._url = url
        self._headers = {'Content-Type': 'application/json',
                         'user-agent': 'KubeAnnotationDeployment',
                         'Authorization': 'Bearer %s' % (token)}

    def _render_containers(self, deployment):
        text = ""
        containers = deployment.spec.template.spec.containers

        if containers:
            text = "<b>Containers</b></br>"

            for container in containers:
                text += "- %s/%s</br>" % (container.name, container.image)

        return text

    def _render_annotations(self, deployment):
        text = ""
        annotations = deployment.metadata.annotations
        if annotations:
            text = "<b>Annotations</b></br>"

            for k, v in annotations.items():
                if k in self.ignore_k8s_annotations:
                    continue

                if 'http://' in v or 'https://' in v:
                    v = '<a href="%s">%s</a>' % (v, v)

                text += "- %s:%s</br>" % (k, v)
        return text

    def post(self, deployment, dashboard_id=None, panel_id=None):
        text = self._render_annotations(deployment)
        text += self._render_containers(deployment)

        data = {
            'text': text,
            'tags': self.tags
        }

        if dashboard_id:
            data["dashboardId"] = int(dashboard_id)

        if panel_id:
            data["panelId"] = int(panel_id)

        annotation = json.dumps(data)
        annotation_url = "%s/api/annotations" % (self._url)

        try:
            response = requests.post(annotation_url, data=annotation,
                                     headers=self._headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            sys.exit(1)
        

def main(grafana_url, grafana_token):

    if "KUBERNETES_PORT" in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()

    api_client = client.api_client.ApiClient()
    core = client.ExtensionsV1beta1Api(api_client)

    grafana = GrafanaAnnotate(grafana_url, grafana_token)

    while True:
        pods = core.list_deployment_for_all_namespaces(watch=False)
        resource_version = pods.metadata.resource_version
        stream = watch.Watch().stream(core.list_deployment_for_all_namespaces,
                                      resource_version=resource_version
                                      )
        print("Waiting for deployment events to come in..")
        for event in stream:
            if event['type'] == 'ADDED':
                deployment = event['object']
                print(f"got event for {deployment.metadata.namespace}/{deployment.metadata.name}")
                grafana.post(deployment)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='path to configuration file')
    args = parser.parse_args()

    config_file = args.config

    if not os.path.exists(config_file):
        print("Config not found: %s" % (config_file))
        sys.exit(1)

    print("Using config: %s" % (config_file))
    with open(config_file, 'r') as ymlfile:
        yaml_config = yaml.safe_load(ymlfile)

    grafana_url = yaml_config.get("grafana_url")
    grafana_token = yaml_config.get("grafana_token")

    main(grafana_url, grafana_token)
